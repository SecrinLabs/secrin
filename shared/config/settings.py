from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

class Settings(BaseSettings):
    # Pydantic will automatically read from env vars or .env

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore unknown env vars
    )

    # ---- Database ----
    DATABASE_URL: str
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "devsecrin"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = ""
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ---- Ollama ----
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "deepseek-r1:1.5b"
    OLLAMA_GPU_LAYERS: int = 35
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.7

    # ---- Gemini ----
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-pro"

    # ---- API ----
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    RELOAD: bool = False
    WORKERS: int = 4

    # ---- Security ----
    API_KEY: str | None = None
    ALLOWED_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])
    RATE_LIMIT_PER_MINUTE: int = 60

    # ---- GitHub ----
    GITHUB_TOKEN: str | None = None
    GITHUB_APP_ID: str | None = None
    GITHUB_APP_SEC_KEY: str | None = None
    GITHUB_WEBHOOK_SECRET: str | None = None
    ENABLE_GITHUB_INTEGRATION: bool = True

    # ---- Redis ----
    REDIS_SERVER_URL: str | None = None

    # ---- Misc ----
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
