import requests
from datetime import datetime
from typing import Optional
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import sessionmaker
import re

from src.models import engine
from src.models.Issue import PullRequest, Issue  # assumes you have this

from config import get_logger

# Setup logger for this module
logger = get_logger(__name__)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class GithubScraper:
    GITHUB_API_URL = "https://api.github.com/graphql"

    def __init__(self, token: str, owner_or_url: str, repo: str = "", limit: int = 100):
        self.token = token
        self.limit = limit
        
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
                
        logger.debug(f"🔍 GitHub Scraper initialized - Owner: {self.owner}, Repo: {self.repo}")
                
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.db = SessionLocal()

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

    def build_query(self, after_cursor: str = None) -> str:
        # GitHub API limits pullRequests to max 100 per request
        page_size = min(self.limit, 100)
        after_clause = f', after: "{after_cursor}"' if after_cursor else ''
        
        return f"""
        {{
          repository(owner: "{self.owner}", name: "{self.repo}") {{
            pullRequests(first: {page_size}{after_clause}, states: MERGED, orderBy: {{field: UPDATED_AT, direction: DESC}}) {{
              pageInfo {{
                hasNextPage
                endCursor
              }}
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
            logger.debug(f"❌ Failed to fetch diff for PR #{pr_number}: {response.status_code}")
            return ""


    def fetch_data(self) -> List[Dict[str, Any]]:
        all_pull_requests = []
        after_cursor = None
        fetched_count = 0
        
        while fetched_count < self.limit:
            # Calculate how many more records we need
            remaining = self.limit - fetched_count
            page_size = min(remaining, 100)  # GitHub's max limit per request
            
            response = requests.post(self.GITHUB_API_URL, headers=self.headers, json={"query": self.build_query(after_cursor)})
            
            if response.status_code != 200:
                logger.debug("❌ Query failed:", response.status_code)
                logger.debug(response.text)
                break

            try:
                response_data = response.json()
                
                # Check if the response has errors
                if "errors" in response_data:
                    logger.debug("❌ GraphQL errors:", response_data["errors"])
                    break
                
                # Check if the expected data structure exists
                if ("data" not in response_data or 
                    "repository" not in response_data["data"] or 
                    response_data["data"]["repository"] is None):
                    logger.debug("❌ Repository not found or access denied")
                    logger.debug("Response:", response_data)
                    break
                
                if ("pullRequests" not in response_data["data"]["repository"] or
                    "nodes" not in response_data["data"]["repository"]["pullRequests"]):
                    logger.debug("❌ No pull requests found")
                    break
                
                pull_requests_data = response_data["data"]["repository"]["pullRequests"]
                nodes = pull_requests_data["nodes"]
                page_info = pull_requests_data["pageInfo"]
                
                # Add the nodes to our collection
                all_pull_requests.extend(nodes)
                fetched_count += len(nodes)
                
                logger.debug(f"📦 Fetched {len(nodes)} PRs (Total: {fetched_count}/{self.limit})")
                
                # Check if we have more pages and haven't reached our limit
                if not page_info["hasNextPage"] or fetched_count >= self.limit:
                    break
                    
                after_cursor = page_info["endCursor"]
                
            except Exception as e:
                logger.debug("❌ Error parsing response:", str(e))
                logger.debug("Response text:", response.text)
                break
        
        # Return only the number of items requested
        return all_pull_requests[:self.limit]
    
    def safe_parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str or not dt_str.strip():
            return None
        try:
            return datetime.fromisoformat(dt_str.rstrip("Z"))
        except Exception:
            return None

    def _save_to_db(self, pr_data: Dict[str, Any]):
        pr_number = pr_data["number"]
        pr = self.db.query(PullRequest).filter_by(Number=pr_number).first()

        merged_at = self.safe_parse_datetime(pr_data.get("mergedAt"))

        diff = self.fetch_diff(pr_number)
        if not pr:
            pr = PullRequest(
                Number=pr_number,
                Title=pr_data["title"],
                Url=pr_data["url"],
                MergedAt=merged_at,
                Body= pr_data["body"],
                Diff=diff
            )
            self.db.add(pr)
            logger.debug(f"✅ Inserted PR #{pr_number}")
        else:
            pr.Title = pr_data["title"]
            pr.Url = pr_data["url"]
            pr.MergedAt = merged_at
            pr.Body = pr_data["body"]
            pr.Diff = diff
            logger.debug(f"♻️ Updated PR #{pr_number}")

        # Clear and re-add issues (idempotent behavior)
        pr.ClosedIssue.clear()

        for issue_data in pr_data["closingIssuesReferences"]["nodes"]:
            issue_closed_at = self.safe_parse_datetime(issue_data.get("closedAt"))
            issue = Issue(
                Number=issue_data["number"],
                Title=issue_data["title"],
                Url=issue_data["url"],
                ClosedAt=issue_closed_at,
                Body=issue_data["body"],
                PR=pr
            )
            self.db.add(issue)

        self.db.commit()

    def scrape(self) -> None:
        pull_requests = self.fetch_data()
        for pr_data in pull_requests:
            self._save_to_db(pr_data)
