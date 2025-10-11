import requests
import re
from typing import Dict, Any, List
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert

from db.index import SessionLocal
from db.models.githubcommits import GithubCommit
from semantic.VectorStore import VectorStore
from semantic.LLMStore import LLMStore
from semantic.PromptStore import PromptStoreFactory, PromptType
from config import get_logger

logger = get_logger(__name__)

class GithubScraper:
    GITHUB_API_URL = "https://api.github.com/graphql"

    def __init__(self, token: str, owner_or_url: str, user_id: int, repo: str = "", limit: int = 20):
        self.token = token
        self.user_id = user_id

        if owner_or_url.startswith("http"):
            parsed = self._parse_github_url(owner_or_url)
            self.owner = parsed["owner"]
            self.repo = parsed["repo"]
        else:
            self.owner = owner_or_url
            if repo.startswith("http"):
                parsed = self._parse_github_url(repo)
                self.owner = parsed["owner"]
                self.repo = parsed["repo"]
            else:
                self.repo = repo

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        self.limit = self.get_commit_count()

        logger.info(f"GitHub Scraper initialized — Owner: {self.owner}, Repo: {self.repo}")

    def get_commit_count(self) -> int:
        query = f"""
        {{
        repository(owner: "{self.owner}", name: "{self.repo}") {{
            defaultBranchRef {{
            target {{
                ... on Commit {{
                history {{
                    totalCount
                }}
                }}
            }}
            }}
        }}
        }}
        """
        response = requests.post(
            self.GITHUB_API_URL,
            headers=self.headers,
            json={"query": query}
        )
        data = response.json()
        return data["data"]["repository"]["defaultBranchRef"]["target"]["history"]["totalCount"]

    def _parse_github_url(self, url: str) -> Dict[str, str]:
        url = url.rstrip("/").rstrip(".git")
        pattern = r"https?://github\.com/([^/]+)/([^/]+)"
        match = re.match(pattern, url)
        if not match:
            raise ValueError(f"Invalid GitHub URL: {url}")
        return {"owner": match.group(1), "repo": match.group(2)}

    def build_query(self, after_cursor: str = None, page_size: int = 20) -> str:
        after_clause = f', after: "{after_cursor}"' if after_cursor else ""
        return f"""
        {{
          repository(owner: "{self.owner}", name: "{self.repo}") {{
            defaultBranchRef {{
              target {{
                ... on Commit {{
                  history(first: {page_size}{after_clause}) {{
                    pageInfo {{
                      hasNextPage
                      endCursor
                    }}
                    nodes {{
                      oid
                      message
                      committedDate
                      author {{
                        name
                        email
                        user {{
                          login
                        }}
                      }}
                      url
                      associatedPullRequests(first: 1) {{
                        nodes {{
                          number
                          url
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        """

    def fetch_pr_diff(self, pr_number: int) -> str:
        diff_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls/{pr_number}"
        try:
            response = requests.get(diff_url, headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3.diff"
            })
            return response.text if response.status_code == 200 else ""
        except Exception as e:
            logger.error(f"Error fetching diff for PR #{pr_number}: {e}")
            return ""

    def fetch_diff(self, sha: int) -> str:
        diff_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits/{sha}"
        try:
            response = requests.get(diff_url, headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3.diff"
            })
            return response.text if response.status_code == 200 else ""
        except Exception as e:
            logger.error(f"Error fetching diff for sha #{sha}: {e}")
            return ""

    def fetch_data(self):
        logger.info("Starting to fetch data from GitHub...")
        results = []
        after_cursor = None
        fetched_count = 0

        while fetched_count < self.limit:
            remaining = self.limit - fetched_count
            page_size = min(remaining, 20)
            logger.info(f"Fetching commits batch — progress: {fetched_count}/{self.limit}")

            try:
                response = requests.post(
                    self.GITHUB_API_URL,
                    headers=self.headers,
                    json={"query": self.build_query(after_cursor, page_size)},
                    timeout=30
                )
            except Exception as e:
                logger.error(f"Request failed: {e}")
                break

            if response.status_code != 200:
                logger.error(f"GitHub GraphQL query failed — Status: {response.status_code}, Response: {response.text}")
                break

            try:
                data = response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON response: {e}, Raw: {response.text}")
                break

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                break

            repo_data = data.get("data", {}).get("repository")
            if not repo_data:
                logger.warning(f"Repository not found or access denied. Response: {data}")
                break

            default_branch = repo_data.get("defaultBranchRef")
            if not default_branch:
                logger.warning("No default branch found — possibly empty repository.")
                break

            history = default_branch["target"]["history"]
            nodes = history["nodes"]

            if not nodes:
                logger.info("No more commits found — finished scanning.")
                break

            results.extend(nodes)
            fetched_count += len(nodes)
            logger.info(f"Fetched {len(nodes)} new commits (Total: {fetched_count}/{self.limit})")

            self.save_commits(nodes, self.user_id)

            if not history["pageInfo"]["hasNextPage"] or fetched_count >= self.limit:
                break

            after_cursor = history["pageInfo"]["endCursor"]

        logger.info(f"Completed fetching {len(results)} commits in total.")

    def save_commits(self, commits: list, user_id: int):
        session = SessionLocal()
        try:
            for commit in commits:
                sha = commit["oid"]
                logger.debug(f"Processing commit: {sha}")

                commit_diff = self.fetch_diff(sha)
                logger.info(f"LLM invoke for diff summary {sha}")
                diff_desc = self.get_diff_summary(commit_diff)

                stmt = insert(GithubCommit).values(
                    user_id=user_id,
                    sha=sha,
                    message=commit.get("message"),
                    author_name=commit.get("author", {}).get("name"),
                    author_email=commit.get("author", {}).get("email"),
                    author_date=commit.get("committedDate"),
                    html_url=commit.get("url"),
                    raw_payload=commit_diff,
                    diff_desc=diff_desc
                ).on_conflict_do_update(
                    index_elements=['sha'],
                    set_={
                        "message": commit.get("message"),
                        "author_name": commit.get("author", {}).get("name"),
                        "author_email": commit.get("author", {}).get("email"),
                        "author_date": commit.get("committedDate"),
                        "html_url": commit.get("url"),
                        "raw_payload": commit_diff
                    }
                )

                session.execute(stmt)

            session.commit()
            logger.info(f"Inserted or updated {len(commits)} commits into DB successfully.")

        except IntegrityError:
            session.rollback()
            logger.warning("Duplicate commit(s) detected and skipped due to integrity constraint.")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert commits: {e}", exc_info=True)
        finally:
            session.close()

    def scrape(self):
        try:
            logger.info("Starting GitHub scrape operation...")
            self.fetch_data()
        except KeyboardInterrupt:
            logger.warning("Scrape operation manually interrupted by user.")
        except Exception as e:
            logger.error(f"Scrape operation failed: {e}", exc_info=True)

    def get_diff_summary(self, diff):
        llm = LLMStore().get_llm()
        prompt_store = PromptStoreFactory.create(PromptType.COMMIT_DIFF)
        prompt = prompt_store.format_prompt(diff)
        try:
            res = llm.invoke(prompt).content
            return res
        except Exception as e:
            logger.error(f"Error while generating diff summary: {e}", exc_info=True)
            raise
