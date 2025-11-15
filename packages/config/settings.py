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

    # ---- API ----
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_VERSION: str = "v1"

    # ---- Misc ----
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
