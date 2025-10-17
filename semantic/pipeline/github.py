from tqdm import tqdm
from langchain_core.documents import Document

from db.index import SessionLocal
from db.models.githubcommits import GithubCommit
from semantic.VectorStore import VectorStore
from semantic.LLMStore import LLMStore
from semantic.PromptStore import PromptStoreFactory, PromptType
from config import get_logger

logger = get_logger(__name__)


class GitHubPipeline:
    def __init__(self, collection_name: str) -> None:
        self.collection_name = collection_name
        self.session = SessionLocal()
        self.vector_store = VectorStore(collection_name).get_vector_store()

    def _serialize_commit(self, commit: GithubCommit) -> str:
        return (
            f"Commit: {commit.sha}\n"
            f"Author: {commit.author_name} <{commit.author_email}>\n"
            f"Date: {commit.author_date}\n"
            f"Message: {commit.message}\n"
            f"URL: {commit.html_url or ''}\n"
            f"commit_desc: {commit.diff_desc}\n"
            f"commit_diff: {commit.raw_payload}\n"
        )

    def _sanitize_metadata(self, metadata: dict) -> dict:
        clean: dict[str, str | int | float | bool] = {}
        for k, v in metadata.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            else:
                clean[k] = str(v)
        return clean

    def _commit_metadata(self, commit: GithubCommit) -> dict:
        raw = {
            "sha": commit.sha,
            "author_name": commit.author_name,
            "author_email": commit.author_email,
            "html_url": commit.html_url,
            "commit_desc": commit.diff_desc,
            "author_date": str(commit.author_date) if commit.author_date else None,
        }
        return self._sanitize_metadata(raw)

    def embed_github_commits(self, userId, batch_size: int = 100) -> None:
        try:
            total = self.session.query(GithubCommit).filter(GithubCommit.user_id == userId).count()
            query = self.session.query(GithubCommit).filter(GithubCommit.user_id == userId).yield_per(batch_size)

            for commit in tqdm(query, total=total, desc="Embedding commits"):
                try:
                    content = self._serialize_commit(commit)
                    metadata = self._commit_metadata(commit)
                    doc_id = f"commit-{commit.sha}"

                    document = Document(
                        page_content=content,
                        metadata=metadata,
                    )

                    self.vector_store.add_documents(
                        documents=[document],
                        ids=[doc_id],
                    )

                    logger.info(f"Embedded commit {commit.sha}")
                except Exception as e:
                    logger.error(f"Failed to embed commit {commit.sha}: {e}")
        finally:
            self.session.close()