import requests
from datetime import datetime
from typing import Optional
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import sessionmaker
import re

from packages.models import engine
from packages.models.githubissue import PullRequest, Issue  # assumes you have this

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class GithubScraper:
    GITHUB_API_URL = "https://api.github.com/graphql"

    def __init__(self, token: str, owner_or_url: str, repo: str = ""):
        self.token = token
        
        # If the first parameter is a full GitHub URL, parse it
        if owner_or_url.startswith('http'):
            parsed = self._parse_github_url(owner_or_url)
            self.owner = parsed['owner']
            self.repo = parsed['repo']
        else:
            self.owner = owner_or_url
            # If repo parameter is a full GitHub URL, parse it
            if repo.startswith('http'):
                parsed = self._parse_github_url(repo)
                self.owner = parsed['owner']
                self.repo = parsed['repo']
            else:
                self.repo = repo
                
        print(f"🔍 GitHub Scraper initialized - Owner: {self.owner}, Repo: {self.repo}")
                
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.db = SessionLocal()
        PullRequest.metadata.create_all(bind=engine)  # optional if handled in main

    def _parse_github_url(self, url: str) -> Dict[str, str]:
        """Parse GitHub URL to extract owner and repo name."""
        # Remove trailing slash and .git if present
        url = url.rstrip('/').rstrip('.git')
        
        # Match GitHub URL pattern
        pattern = r'https?://github\.com/([^/]+)/([^/]+)'
        match = re.match(pattern, url)
        
        if match:
            return {
                'owner': match.group(1),
                'repo': match.group(2)
            }
        else:
            raise ValueError(f"Invalid GitHub URL format: {url}")

    def build_query(self) -> str:
        return f"""
        {{
          repository(owner: "{self.owner}", name: "{self.repo}") {{
            pullRequests(first: 100, states: MERGED, orderBy: {{field: UPDATED_AT, direction: DESC}}) {{
              nodes {{
                number
                title
                body
                url
                mergedAt
                closingIssuesReferences(first: 5) {{
                  nodes {{
                    number
                    title
                    body
                    url
                    closedAt
                  }}
                }}
              }}
            }}
          }}
        }}
        """
    
    def fetch_diff(self, pr_number: int) -> str:
        diff_url = f"https://patch-diff.githubusercontent.com/raw/{self.owner}/{self.repo}/pull/{pr_number}.diff"

        response = requests.get(diff_url, headers={
            "Authorization": f"Bearer {self.token}"
        })

        if response.status_code == 200:
            return response.text  # ✅ contains raw diff
        else:
            print(f"❌ Failed to fetch diff for PR #{pr_number}: {response.status_code}")
            return ""


    def fetch_data(self) -> List[Dict[str, Any]]:
        response = requests.post(self.GITHUB_API_URL, headers=self.headers, json={"query": self.build_query()})
        
        if response.status_code != 200:
            print("❌ Query failed:", response.status_code)
            print(response.text)
            return []

        try:
            response_data = response.json()
            
            # Check if the response has errors
            if "errors" in response_data:
                print("❌ GraphQL errors:", response_data["errors"])
                return []
            
            # Check if the expected data structure exists
            if ("data" not in response_data or 
                "repository" not in response_data["data"] or 
                response_data["data"]["repository"] is None):
                print("❌ Repository not found or access denied")
                print("Response:", response_data)
                return []
            
            if ("pullRequests" not in response_data["data"]["repository"] or
                "nodes" not in response_data["data"]["repository"]["pullRequests"]):
                print("❌ No pull requests found")
                return []
            
            return response_data["data"]["repository"]["pullRequests"]["nodes"]
            
        except Exception as e:
            print("❌ Error parsing response:", str(e))
            print("Response text:", response.text)
            return []
    
    def safe_parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str or not dt_str.strip():
            return None
        try:
            return datetime.fromisoformat(dt_str.rstrip("Z"))
        except Exception:
            return None

    def _save_to_db(self, pr_data: Dict[str, Any]):
        pr_number = pr_data["number"]
        pr = self.db.query(PullRequest).filter_by(number=pr_number).first()

        merged_at = self.safe_parse_datetime(pr_data.get("mergedAt"))

        diff = self.fetch_diff(pr_number)
        if not pr:
            pr = PullRequest(
                number=pr_number,
                title=pr_data["title"],
                url=pr_data["url"],
                merged_at=merged_at,
                body= pr_data["body"],
                diff=diff
            )
            self.db.add(pr)
            print(f"✅ Inserted PR #{pr_number}")
        else:
            pr.title = pr_data["title"]
            pr.url = pr_data["url"]
            pr.merged_at = merged_at
            pr.body = pr_data["body"]
            pr.diff = diff
            print(f"♻️ Updated PR #{pr_number}")

        # Clear and re-add issues (idempotent behavior)
        pr.closing_issues.clear()

        for issue_data in pr_data["closingIssuesReferences"]["nodes"]:
            issue_closed_at = self.safe_parse_datetime(issue_data.get("closedAt"))
            issue = Issue(
                number=issue_data["number"],
                title=issue_data["title"],
                url=issue_data["url"],
                closed_at=issue_closed_at,
                body=issue_data["body"],
                pull_request=pr
            )
            self.db.add(issue)

        self.db.commit()

    def scrape(self) -> None:
        pull_requests = self.fetch_data()
        for pr_data in pull_requests:
            self._save_to_db(pr_data)
