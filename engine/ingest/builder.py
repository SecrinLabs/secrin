from tqdm import tqdm

from db.index import SessionLocal
from db.models.githubcommits import GithubCommit
from config import settings, get_logger
from engine.llm.factory import get_llm

logger = get_logger(__name__)

class EmbeddingBuilder:
  def __init__(self, embedder, vectorstore, llm=None):
    self.embedder = embedder
    self.vectorstore = vectorstore
    self.session = SessionLocal()
        
        # Initialize LLM - use factory if not provided
    if llm is None:
        llm_provider = settings.LLM_PROVIDER
        self.llm = get_llm(llm_provider)
        logger.info(f"Initialized LLM with provider: {llm_provider}")
    else:
        self.llm = llm
        logger.info(f"Using provided LLM: {self.llm.get_model_info()}")

  def _serialize_commit(self, commit: GithubCommit) -> str:
    """Convert a commit row into canonical text for embedding."""
    return (
        f"Commit: {commit.sha}\n"
        f"Author: {commit.author_name} <{commit.author_email}>\n"
        f"Date: {commit.author_date}\n"
        f"Message: {commit.message}\n"
        f"URL: {commit.html_url or ''}\n"
    )
  
  def _sanitize_metadata(self, metadata: dict) -> dict:
    """Ensure metadata contains only str, int, float, bool."""
    clean = {}
    for k, v in metadata.items():
        if v is None:
            continue  # Option 1: drop field
            # clean[k] = ""   # Option 2: keep as empty string
        elif isinstance(v, (str, int, float, bool)):
            clean[k] = v
        else:
            clean[k] = str(v)  # fallback: stringify (e.g., datetime)
    return clean

  
  def _commit_metadata(self, commit: GithubCommit) -> dict:
    raw = {
        "sha": commit.sha,
        "author_name": commit.author_name,
        "author_email": commit.author_email,
        "committer_name": commit.committer_name,
        "committer_email": commit.committer_email,
        "html_url": commit.html_url,
        "inserted_at": str(commit.inserted_at) if commit.inserted_at else None,
    }
    return self._sanitize_metadata(raw)

  
  def embed_github_commits(self, batch_size: int = 100):
    """Embed all commits into vectorstore in batches with progress bar."""
    query = self.session.query(GithubCommit).yield_per(batch_size)
    total = self.session.query(GithubCommit).count()

    for commit in tqdm(query, total=total, desc="Embedding commits"):
        try:
            content = self._serialize_commit(commit)
            metadata = self._commit_metadata(commit)

            # Generate embedding
            embedding = self.embedder.embed(content)

            # Use commit sha as document id
            doc_id = f"commit-{commit.sha}"

            # Add to vectorstore
            self.vectorstore.add_document(
                doc_id=doc_id,
                embedding=embedding,
                document=content,
                metadata=metadata
            )
            logger.info(f"Embedded commit {commit.sha}")

        except Exception as e:
            logger.error(f"Failed to embed commit {commit.sha}: {e}")

    