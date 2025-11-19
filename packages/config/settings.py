from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

class Settings(BaseSettings):
    # Pydantic will automatically read from env vars or .env

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore unknown env vars
    )

    print(Path(__file__).resolve().parent.parent.parent)

    # ---- Neo4J ----
    NEO4J_URI: str = ""
    NEO4J_USER: str = ""
    NEO4J_PASS: str = ""
    NEO4J_DB: str = ""

    # ---- Embeddings ----
    OPENAI_API_KEY: str = ""
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_EMBEDDING_MODEL: str = "mxbai-embed-large"
    SENTENCE_TRANSFORMER_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_PROVIDER: str = "ollama"  # "openai", "ollama", or "sentence_transformer"
    EMBEDDING_DIMENSION: int = 1024  # 1536 for OpenAI, 1024 for mxbai-embed-large, 384 for MiniLM

    # ---- API ----
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_VERSION: str = "v1"

    # ---- Misc ----
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
