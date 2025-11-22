from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from pathlib import Path
from typing import Literal, Optional
import logging


class Settings(BaseSettings):
    """
    Production-grade settings with validation and type safety.
    All settings are configurable via environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore unknown env vars
        case_sensitive=False,  # Allow lowercase env vars
    )

    # ============================================================================
    # Environment & Deployment
    # ============================================================================
    
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment"
    )
    
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode (never use in production)"
    )
    
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    # ============================================================================
    # Neo4j Database Configuration
    # ============================================================================
    
    NEO4J_URI: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j connection URI"
    )
    
    NEO4J_USER: str = Field(
        default="neo4j",
        description="Neo4j username"
    )
    
    NEO4J_PASS: str = Field(
        default="",
        description="Neo4j password"
    )
    
    NEO4J_DB: str = Field(
        default="neo4j",
        description="Neo4j database name"
    )
    
    NEO4J_MAX_CONNECTION_LIFETIME: int = Field(
        default=3600,
        description="Maximum connection lifetime in seconds"
    )
    
    NEO4J_MAX_CONNECTION_POOL_SIZE: int = Field(
        default=50,
        description="Maximum connection pool size"
    )
    
    NEO4J_CONNECTION_TIMEOUT: int = Field(
        default=30,
        description="Connection timeout in seconds"
    )
    
    # ============================================================================
    # Embedding Configuration
    # ============================================================================
    
    EMBEDDING_PROVIDER: Literal["openai", "ollama", "sentence_transformer"] = Field(
        default="ollama",
        description="Embedding provider to use"
    )
    
    EMBEDDING_DIMENSION: int = Field(
        default=1024,
        description="Embedding vector dimension (provider-specific)"
    )
    
    EMBEDDING_BATCH_SIZE: int = Field(
        default=100,
        description="Batch size for embedding generation"
    )
    
    EMBEDDING_CACHE_TTL: int = Field(
        default=3600,
        description="Embedding cache TTL in seconds (if caching enabled)"
    )
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key"
    )
    
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model name"
    )
    
    OPENAI_MAX_RETRIES: int = Field(
        default=3,
        description="Maximum retry attempts for OpenAI API"
    )
    
    OPENAI_TIMEOUT: int = Field(
        default=60,
        description="OpenAI API timeout in seconds"
    )
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Ollama base URL"
    )
    
    OLLAMA_EMBEDDING_MODEL: str = Field(
        default="mxbai-embed-large",
        description="Ollama embedding model name"
    )
    
    OLLAMA_TIMEOUT: int = Field(
        default=120,
        description="Ollama request timeout in seconds"
    )
    
    # Sentence Transformer Configuration
    SENTENCE_TRANSFORMER_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence Transformer model name"
    )
    
    SENTENCE_TRANSFORMER_DEVICE: Literal["cpu", "cuda", "mps"] = Field(
        default="cpu",
        description="Device for sentence transformer inference"
    )
    
    # ============================================================================
    # Vector Search Configuration
    # ============================================================================
    
    VECTOR_SEARCH_DEFAULT_LIMIT: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Default limit for vector search results"
    )
    
    VECTOR_SEARCH_MAX_LIMIT: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum allowed limit for vector search"
    )
    
    HYBRID_SEARCH_VECTOR_WEIGHT: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Weight for vector score in hybrid search (0-1)"
    )
    
    VECTOR_INDEX_SIMILARITY_FUNCTION: Literal["cosine", "euclidean"] = Field(
        default="cosine",
        description="Similarity function for vector indexes"
    )
    
    # ============================================================================
    # API Configuration
    # ============================================================================
    
    API_HOST: str = Field(
        default="0.0.0.0",
        description="API host address"
    )
    
    API_PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="API port number"
    )
    
    API_VERSION: str = Field(
        default="v1",
        description="API version prefix"
    )
    
    API_TITLE: str = Field(
        default="Secrin API",
        description="API title for documentation"
    )
    
    API_DESCRIPTION: str = Field(
        default="Code analysis and vector search API",
        description="API description for documentation"
    )
    
    API_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["*"],
        description="CORS allowed origins"
    )
    
    API_RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        ge=1,
        description="API rate limit per minute per IP"
    )
    
    # ============================================================================
    # Performance & Optimization
    # ============================================================================
    
    QUERY_CACHE_SIZE: int = Field(
        default=1000,
        description="Maximum number of cached queries"
    )
    
    QUERY_CACHE_TTL: int = Field(
        default=300,
        description="Query cache TTL in seconds"
    )
    
    MAX_WORKERS: int = Field(
        default=4,
        ge=1,
        description="Maximum worker threads for parallel operations"
    )
    
    # ============================================================================
    # Observability & Monitoring
    # ============================================================================
    
    METRICS_ENABLED: bool = Field(
        default=False,
        description="Enable metrics collection"
    )
    
    METRICS_PORT: int = Field(
        default=9090,
        ge=1,
        le=65535,
        description="Metrics endpoint port"
    )
    
    TRACING_ENABLED: bool = Field(
        default=False,
        description="Enable distributed tracing"
    )
    
    TRACING_ENDPOINT: Optional[str] = Field(
        default=None,
        description="Tracing backend endpoint (e.g., Jaeger)"
    )
    
    # ============================================================================
    # Security
    # ============================================================================
    
    API_KEY: Optional[str] = Field(
        default=None,
        description="API authentication key"
    )
    
    ALLOWED_HOSTS: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed host headers"
    )
    
    # ============================================================================
    # Feature Flags (Environment-level overrides)
    # ============================================================================
    
    FEATURE_EMBEDDINGS: bool = Field(default=True, description="Enable embedding generation")
    FEATURE_VECTOR_SEARCH: bool = Field(default=True, description="Enable vector search")
    FEATURE_HYBRID_SEARCH: bool = Field(default=True, description="Enable hybrid search")
    FEATURE_BATCH_PROCESSING: bool = Field(default=True, description="Enable batch processing")
    FEATURE_CACHING: bool = Field(default=False, description="Enable caching layer")
    
    # ============================================================================
    # Validators
    # ============================================================================
    
    @field_validator("EMBEDDING_DIMENSION")
    @classmethod
    def validate_embedding_dimension(cls, v: int) -> int:
        """Validate embedding dimension is positive and reasonable."""
        if v <= 0:
            raise ValueError("Embedding dimension must be positive")
        if v > 10000:
            raise ValueError("Embedding dimension seems unreasonably large")
        return v
    
    @field_validator("HYBRID_SEARCH_VECTOR_WEIGHT")
    @classmethod
    def validate_vector_weight(cls, v: float) -> float:
        """Validate vector weight is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Vector weight must be between 0.0 and 1.0")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is recognized by logging module."""
        v_upper = v.upper()
        if v_upper not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid log level: {v}")
        return v_upper
    
    def get_log_level_int(self) -> int:
        """Get integer log level for logging module."""
        return getattr(logging, self.LOG_LEVEL)
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    def get_neo4j_config(self) -> dict:
        """Get Neo4j driver configuration."""
        return {
            "max_connection_lifetime": self.NEO4J_MAX_CONNECTION_LIFETIME,
            "max_connection_pool_size": self.NEO4J_MAX_CONNECTION_POOL_SIZE,
            "connection_timeout": self.NEO4J_CONNECTION_TIMEOUT,
        }
