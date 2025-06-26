import requests
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from models import engine
from models.githubissue import PullRequest, Issue  # assumes you have this

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class GithubScraper:
    GITHUB_API_URL = "https://api.github.com/graphql"

    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.db = SessionLocal()
        PullRequest.metadata.create_all(bind=engine)  # optional if handled in main

    def build_query(self) -> str:
        return f"""
        {{
          repository(owner: "{self.owner}", name: "{self.repo}") {{
            pullRequests(first: 10, states: MERGED, orderBy: {{field: UPDATED_AT, direction: DESC}}) {{
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

        return response.json()["data"]["repository"]["pullRequests"]["nodes"]

    def _save_to_db(self, pr_data: Dict[str, Any]):
        pr_number = pr_data["number"]
        pr = self.db.query(PullRequest).filter_by(number=pr_number).first()

        merged_at = datetime.fromisoformat(pr_data["mergedAt"].rstrip("Z"))

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
            issue_closed_at = datetime.fromisoformat(issue_data["closedAt"].rstrip("Z"))
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
