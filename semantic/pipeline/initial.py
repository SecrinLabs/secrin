from langchain_core.documents import Document
from sqlalchemy.orm import Session

from db.models.repository import Repository
from db.index import SessionLocal
from semantic.VectorStore import VectorStore
from config import get_logger

logger = get_logger(__name__)

class InitialPipeline:
    def __init__(self, collection_name: str) -> None:
        self.vector_store = VectorStore(collection_name).get_vector_store()

    def run_initial_pipeline(self):
        session: Session = SessionLocal()
        try:
            repos = (
                session.query(Repository)
                .filter(Repository.description.isnot(None))
                .all()
            )
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return None
        finally:
            session.close()

        if not repos:
            logger.info("No repositories with descriptions found.")
            return None

        docs, ids = [], []
        for repo in repos:
            raw_metadata = {
                "id": repo.id,
                "user_id": repo.user_id,
                "repo_name": repo.repo_name,
                "repo_url": repo.repo_url,
                "repo_id": repo.repo_id,
                "full_name": repo.full_name,
                "private": repo.private,
                "language": repo.language,
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "watchers_count": repo.watchers_count,
                "default_branch": repo.default_branch,
                "open_issues_count": repo.open_issues_count,
                "has_issues": repo.has_issues,
                "has_discussions": repo.has_discussions,
                "archived": repo.archived,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "clone_url": repo.clone_url,
                "owner_login": repo.owner_login,
                "owner_type": repo.owner_type,
            }

            safe_metadata = {k: (str(v) if v is not None else "") for k, v in raw_metadata.items()}

            page_content = f"""
            Repository: {repo.repo_name}
            Full Name: {repo.full_name}
            Description: {repo.description}

            Clone URL: {repo.clone_url}
            Repo URL: {repo.repo_url}
            Owner: {repo.owner_login} ({repo.owner_type})
            Language: {repo.language}
            Private: {repo.private}

            Stars: {repo.stargazers_count}
            Forks: {repo.forks_count}
            Watchers: {repo.watchers_count}
            Open Issues: {repo.open_issues_count}
            Default Branch: {repo.default_branch}
            Archived: {repo.archived}
            Created At: {safe_metadata["created_at"]}
            Updated At: {safe_metadata["updated_at"]}
            Last Push: {safe_metadata["pushed_at"]}
            """

            docs.append(Document(page_content=page_content.strip(), metadata=safe_metadata))
            ids.append(f"repository-{repo.id}")

        try:
            self.vector_store.add_documents(documents=docs, ids=ids)
            logger.info(f"Embedded {len(docs)} repositories into collection {self.vector_store}")
        except Exception as e:
            logger.error(f"Failed to embed repositories: {e}")
