"""
DevSecrin Centralized Configuration

Simple, centralized environment configuration that can be imported from anywhere.

Usage:
    from config import settings
    
    # Direct access to any environment variable
    db_url = settings.DATABASE_URL
    ollama_host = settings.OLLAMA_HOST
    debug_mode = settings.DEBUG
"""

from .env import Settings

# Create global settings instance
settings = Settings()

# Make it easy to import
__all__ = ['settings']
