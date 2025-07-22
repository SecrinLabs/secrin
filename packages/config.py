"""
Configuration management for DevSecrin
Handles environment variables and configuration validation
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
import logging

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    # Load .env file if it exists
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    # dotenv not available, continue without it
    pass

logger = logging.getLogger(__name__)

class Config:
    """Configuration management class"""
    
    def __init__(self):
        self.load_environment()
        self.validate_config()
    
    def load_environment(self):
        """Load environment variables"""
        # Database Configuration
        print(os.getenv("DATABASE_URL", "postgresql://postgres:10514912@localhost:5432/devsecrin"))
        self.database_url = os.getenv("DATABASE_URL", "postgresql://postgres:10514912@localhost:5432/devsecrin")
        self.database_host = os.getenv("DATABASE_HOST", "localhost")
        self.database_port = int(os.getenv("DATABASE_PORT", "5432"))
        self.database_name = os.getenv("DATABASE_NAME", "devsecrin")
        self.database_user = os.getenv("DATABASE_USER", "postgres")
        self.database_password = os.getenv("DATABASE_PASSWORD", "10514912")
        
        # Ollama Configuration
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
        
        # ChromaDB Configuration
        self.chroma_persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_store")
        self.chroma_collection_name = os.getenv("CHROMA_COLLECTION_NAME", "docs")
        
        # GitHub Integration
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_owner = os.getenv("GITHUB_OWNER")
        self.github_repo = os.getenv("GITHUB_REPO")
        
        # Confluence Integration
        self.confluence_url = os.getenv("CONFLUENCE_URL")
        self.confluence_username = os.getenv("CONFLUENCE_USERNAME")
        self.confluence_api_token = os.getenv("CONFLUENCE_API_TOKEN")
        
        # API Configuration
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # Performance Configuration
        self.embedding_batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "50"))
        self.max_context_length = int(os.getenv("MAX_CONTEXT_LENGTH", "4000"))
        self.database_pool_size = int(os.getenv("DATABASE_POOL_SIZE", "10"))
        self.database_max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
        
        # Security Configuration
        self.api_key = os.getenv("API_KEY")
        self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        
        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_file = os.getenv("LOG_FILE", "logs/app.log")
    
    def validate_config(self):
        """Validate configuration and log warnings"""
        warnings = []
        
        # Check required directories
        Path(self.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Validate integrations
        if not self.github_token:
            warnings.append("GITHUB_TOKEN not set - GitHub integration will be disabled")
        
        if not self.confluence_url:
            warnings.append("CONFLUENCE_URL not set - Confluence integration will be disabled")
        
        # Validate Ollama configuration
        if not self.ollama_host.startswith(("http://", "https://")):
            warnings.append("OLLAMA_HOST should start with http:// or https://")
        
        # Log warnings
        for warning in warnings:
            logger.warning(warning)
    
    def get_database_url(self) -> str:
        """Get database URL"""
        return self.database_url
    
    def get_ollama_config(self) -> Dict[str, str]:
        """Get Ollama configuration"""
        return {
            "host": self.ollama_host,
            "model": self.ollama_model
        }
    
    def get_github_config(self) -> Optional[Dict[str, str]]:
        """Get GitHub configuration"""
        if not self.github_token:
            return None
        
        return {
            "token": self.github_token,
            "owner": self.github_owner,
            "repo": self.github_repo
        }
    
    def get_confluence_config(self) -> Optional[Dict[str, str]]:
        """Get Confluence configuration"""
        if not all([self.confluence_url, self.confluence_username, self.confluence_api_token]):
            return None
        
        return {
            "url": self.confluence_url,
            "username": self.confluence_username,
            "api_token": self.confluence_api_token
        }
    
    def is_integration_enabled(self, integration: str) -> bool:
        """Check if an integration is enabled"""
        if integration == "github":
            return self.github_token is not None
        elif integration == "confluence":
            return all([self.confluence_url, self.confluence_username, self.confluence_api_token])
        else:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)"""
        return {
            "database_host": self.database_host,
            "database_port": self.database_port,
            "database_name": self.database_name,
            "ollama_host": self.ollama_host,
            "ollama_model": self.ollama_model,
            "chroma_persist_directory": self.chroma_persist_directory,
            "chroma_collection_name": self.chroma_collection_name,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "debug": self.debug,
            "embedding_batch_size": self.embedding_batch_size,
            "max_context_length": self.max_context_length,
            "log_level": self.log_level,
            "integrations": {
                "github": self.is_integration_enabled("github"),
                "confluence": self.is_integration_enabled("confluence")
            }
        }

# Global configuration instance
config = Config()

def get_config() -> Config:
    """Get the global configuration instance"""
    return config
