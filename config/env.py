"""
Environment Configuration for DevSecrin

Centralized environment variable management with smart defaults.
"""

import os
from pathlib import Path
from typing import Optional, List

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ Loaded environment from {env_file}")
except ImportError:
    # Continue without dotenv if not available
    pass


class Settings:
    """
    Centralized settings class that provides easy access to all environment variables.
    
    All environment variables are accessible as class attributes with smart defaults.
    """
    
    def __init__(self):
        self._load_settings()
    
    def _load_settings(self):
        """Load all environment variables with defaults"""
        
        # Database Configuration
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
            
        self.DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
        self.DATABASE_PORT = int(os.getenv("DATABASE_PORT", "5432"))
        self.DATABASE_NAME = os.getenv("DATABASE_NAME", "devsecrin")
        self.DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
        self.DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
        self.DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
        self.DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
        
        # Ollama AI Configuration
        self.OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
        self.OLLAMA_GPU_LAYERS = int(os.getenv("OLLAMA_GPU_LAYERS", "35"))
        self.MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
        self.TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

        # Gemini AI Configurations
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        
        # Embedder Configuration
        self.EMBEDDER_NAME = os.getenv("EMBEDDER_NAME", "ollama")  # Options: ollama, gemini
        
        # LLM Configuration
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", self.EMBEDDER_NAME)  # Use same as embedder by default
        
        # ChromaDB Configuration
        self.CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_store")
        self.CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "docs")
        self.CHROMA_COLLECTION_SIZE = int(os.getenv("CHROMA_COLLECTION_SIZE", "100000"))
        
        # API Configuration
        self.API_HOST = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT = int(os.getenv("API_PORT", "8000"))
        self.API_BASE_URL = os.getenv("API_BASE_URL", f"http://{self.API_HOST}:{self.API_PORT}")
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.RELOAD = os.getenv("RELOAD", "false").lower() == "true"
        self.WORKERS = int(os.getenv("WORKERS", "4"))
        
        # Security Configuration
        self.API_KEY = os.getenv("API_KEY")
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
        self.ALLOWED_ORIGINS = [origin.strip() for origin in allowed_origins.split(",")]
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        
        # GitHub Integration
        self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        self.GITHUB_OWNER = os.getenv("GITHUB_OWNER")
        self.GITHUB_REPO = os.getenv("GITHUB_REPO")
        self.ENABLE_GITHUB_INTEGRATION = os.getenv("ENABLE_GITHUB_INTEGRATION", "true").lower() == "true"
        
        # Performance Configuration
        self.EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "50"))
        self.MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "4000"))
        self.METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
        self.METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))
        self.HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        self.LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
        
        # Storage Configuration
        self.UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
        self.TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
        self.BACKUP_DIR = os.getenv("BACKUP_DIR", "./backups")
        
        # Feature Flags
        self.ENABLE_WEBSOCKET = os.getenv("ENABLE_WEBSOCKET", "true").lower() == "true"
        self.ENABLE_GRAPH_RAG = os.getenv("ENABLE_GRAPH_RAG", "true").lower() == "true"
        
        # Environment
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        
        # Frontend Configuration
        self.NEXT_PUBLIC_API_BASE_URL = os.getenv("NEXT_PUBLIC_API_BASE_URL", self.API_BASE_URL)
        self.FRONTEND_URL = os.getenv("FRONTEND_URL")
        
        # SSL Configuration (for production)
        self.SSL_CERT_FILE = os.getenv("SSL_CERT_FILE")
        self.SSL_KEY_FILE = os.getenv("SSL_KEY_FILE")

        # Redis Configurations
        self.REDIS_SERVER_URL = os.getenv("REDIS_SERVER_URL")
        
        # Github App Configurations
        self.GITHUB_APP_SEC_KEY = os.getenv("GITHUB_APP_SEC_KEY")
        self.GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")

        # Github Webhook Secret
        self.GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

        # User session setting
        self.SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
        self.SESSION_ALGORITHM = os.getenv("SESSION_ALGORITHM")
        self.SESSION_ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("SESSION_ACCESS_TOKEN_EXPIRE_MINUTES")

        # smtp config
        self.SMTP_HOST = os.getenv("SMTP_HOST")
        self.SMTP_PORT = os.getenv("SMTP_PORT")
        self.SMTP_USER = os.getenv("SMTP_USER")
        self.SMTP_PASS = os.getenv("SMTP_PASS")
        self.SMTP_USE_TLS = True
    
    def _create_directories(self):
        """Create required directories if they don't exist"""
        directories = [
            self.CHROMA_PERSIST_DIRECTORY,
            Path(self.LOG_FILE).parent,
            self.UPLOAD_DIR,
            self.TEMP_DIR,
            self.BACKUP_DIR
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Legacy compatibility methods for existing code
    def get_database_url(self) -> str:
        """Get database URL (for backward compatibility)"""
        return self.DATABASE_URL
    
    def get_ollama_config(self) -> dict:
        """Get Ollama configuration (for backward compatibility)"""
        return {
            "host": self.OLLAMA_HOST,
            "model": self.OLLAMA_MODEL
        }
    
    def get_github_config(self) -> Optional[dict]:
        """Get GitHub configuration (for backward compatibility)"""
        if not self.GITHUB_TOKEN:
            return None
        
        return {
            "token": self.GITHUB_TOKEN,
            "owner": self.GITHUB_OWNER,
            "repo": self.GITHUB_REPO
        }
    
    def get_confluence_config(self) -> Optional[dict]:
        """Get Confluence configuration (for backward compatibility)"""
        if not all([self.CONFLUENCE_URL, self.CONFLUENCE_USERNAME, self.CONFLUENCE_API_TOKEN]):
            return None
        
        return {
            "url": self.CONFLUENCE_URL,
            "username": self.CONFLUENCE_USERNAME,
            "api_token": self.CONFLUENCE_API_TOKEN
        }
    
    def is_integration_enabled(self, integration: str) -> bool:
        """Check if an integration is enabled (for backward compatibility)"""
        if integration == "github":
            return self.GITHUB_TOKEN is not None and self.ENABLE_GITHUB_INTEGRATION
        elif integration == "confluence":
            return (all([self.CONFLUENCE_URL, self.CONFLUENCE_USERNAME, self.CONFLUENCE_API_TOKEN]) 
                   and self.ENABLE_CONFLUENCE_INTEGRATION)
        return False
    
    def reload(self):
        """Reload configuration from environment variables"""
        self._load_settings()
    
    def __repr__(self) -> str:
        return f"<Settings environment={self.ENVIRONMENT}>"


# For backward compatibility - create a get_config function
def get_config() -> Settings:
    """Get settings instance (for backward compatibility)"""
    return Settings()
