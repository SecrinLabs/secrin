from github import Github, Commit
from typing import cast

from packages.memory import Memory
from packages.ingest.edges import Edge


class GithubIngest:
    def __init__(self, token: str):
        self.gh = Github(token)
        self.memory = Memory()

    def ingest_commits(self, repo_full_name: str, limit: int = 30):
        repo = self.gh.get_repo(repo_full_name)
        commits = repo.get_commits()[:limit]

        # Create or get Repo node
        repo_node_id = self.memory.add_memory(
            type="Repo",
            content=repo_full_name,
            metadata={}
        )

        for c in commits:
            commit = cast(Commit.Commit, c)

            # Create Commit node
            commit_node_id = self.memory.add_memory(
                type="Commit",
                content=commit.commit.message,
                metadata={
                    "repo": repo_full_name,
                    "sha": commit.sha,
                    "date": str(commit.commit.author.date) if commit.commit.author else None
                }
            )

            # Create author node
            author_name = commit.commit.author.name if commit.commit.author else "Unknown"
            author_node_id = self.memory.add_memory(
                type="Author",
                content=author_name,
                metadata={}
            )

            # Create files node
            files = commit.files
            for f in files:
              file_node_id = self.memory.add_memory(
                  type="File",
                  content=f.filename,
                  metadata={"repo": repo_full_name}
              )

              # Commit → Files
              self.memory.link(commit_node_id, Edge.TOUCHED, file_node_id)

            # Commit → Repo
            self.memory.link(commit_node_id, Edge.BELONGS_TO, repo_node_id)

            # Commit → Author
            self.memory.link(commit_node_id, Edge.AUTHORED_BY, author_node_id)
