#!/usr/bin/env python3
"""
DevSecrin API Server
Starts the API server with configuration from environment variables
"""

import sys
import os
from pathlib import Path

# Add packages to path
# sys.path.insert(0, str(Path(__file__).parent / "packages"))

import uvicorn
from config import settings

def main():
    """Start the API server"""
    config = settings
    
    print(f"🚀 Starting DevSecrin API server...")
    print(f"📊 Host: {config.API_HOST}")
    print(f"🔧 Port: {config.API_PORT}")
    print(f"🗄️  Database: {config.DATABASE_URL}")
    print(f"🤖 Ollama: {config.OLLAMA_HOST}")
    print(f"🎯 Model: {config.OLLAMA_MODEL}")
    print(f"📁 Chroma: {config.CHROMA_PERSIST_DIRECTORY}")
    
    # Start the server
    uvicorn.run(
        "api.index:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG,
        log_level="info" if not config.DEBUG else "debug"
    )

if __name__ == "__main__":
    main()
