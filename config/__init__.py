"""
DevSecrin Centralized Configuration

Simple, centralized environment configuration that can be imported from anywhere.

Usage:
    from config import settings, get_logger
    
    # Direct access to any environment variable
    db_url = settings.DATABASE_URL
    ollama_host = settings.OLLAMA_HOST
    debug_mode = settings.DEBUG
    
    # Get a logger instance
    logger = get_logger(__name__)
    logger.info("Application started")
"""

from .env import Settings
from .logging import setup_logging, get_logger

# Create global settings instance
settings = Settings()

# Setup logging with the settings
setup_logging(settings)

# Make it easy to import
__all__ = ['settings', 'get_logger']
