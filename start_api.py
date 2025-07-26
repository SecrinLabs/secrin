#!/usr/bin/env python3
"""
DevSecrin API Server
Starts the API server with configuration from environment variables
"""

import sys
import os
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / "packages"))

import uvicorn
from config import settings

def main():
    """Start the API server"""
    config = settings
    
    print(f"🚀 Starting DevSecrin API server...")
    print(f"📊 Host: {config.api_host}")
    print(f"🔧 Port: {config.api_port}")
    print(f"🗄️  Database: {config.database_url}")
    print(f"🤖 Ollama: {config.ollama_host}")
    print(f"🎯 Model: {config.ollama_model}")
    print(f"📁 Chroma: {config.chroma_persist_directory}")
    
    # Start the server
    uvicorn.run(
        "apps.api.index:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug,
        log_level="info" if not config.debug else "debug"
    )

if __name__ == "__main__":
    main()
