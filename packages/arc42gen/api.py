"""
Simple HTTP API for arc42gen.
Run with: uvicorn packages.arc42gen.api:app --port 8001
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional

# Load .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .models.config import Config
from .core.orchestrator import Orchestrator

app = FastAPI(title="Arc42gen API", version="0.1.0")

# Allow CORS for the web app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    """Request to generate docs for a repository."""
    source_repo_url: str  # GitHub URL like https://github.com/owner/repo
    branch: str = "main"
    github_token: Optional[str] = None  # Token for private repos


class GenerateResponse(BaseModel):
    """Response with generated documentation."""
    success: bool
    files: dict[str, str]  # filename -> content
    error: Optional[str] = None


@app.post("/generate", response_model=GenerateResponse)
async def generate_docs(request: GenerateRequest) -> GenerateResponse:
    """
    Generate Arc42 documentation for a GitHub repository.
    Returns the generated markdown files as a dict.
    """
    # Create temp directory for output
    output_dir = tempfile.mkdtemp()
    
    try:
        # Build the repo URL with authentication if token provided
        repo_url = request.source_repo_url
        
        # If we have a token, embed it in the URL for git clone
        if request.github_token:
            # Convert https://github.com/owner/repo to https://x-access-token:TOKEN@github.com/owner/repo
            if repo_url.startswith("https://github.com/"):
                repo_url = repo_url.replace(
                    "https://github.com/",
                    f"https://x-access-token:{request.github_token}@github.com/"
                )
        
        if not repo_url.endswith(".git"):
            repo_url = f"{repo_url}.git"
        
        # Create config
        provider = os.getenv('LLM_PROVIDER', 'gemini')
        
        # Set the correct model based on provider
        if provider == 'gemini':
            model = os.getenv('LLM_MODEL', 'gemini-2.0-flash')
            api_key = os.getenv('GEMINI_API_KEY')
        else:
            model = os.getenv('LLM_MODEL', 'claude-sonnet-4-5-20250929')
            api_key = os.getenv('ANTHROPIC_API_KEY')
        
        config_dict = {
            'llm': {
                'provider': provider,
                'model': model,
                'api_key': api_key,
            },
            'repository': {},
            'arc42': {'sections': [5]},
            'decomposition': {},
            'output': {'path': output_dir},
        }
        
        if not config_dict['llm']['api_key']:
            raise HTTPException(
                status_code=500, 
                detail="No API key configured. Set GEMINI_API_KEY or ANTHROPIC_API_KEY"
            )
        
        cfg = Config.from_dict(config_dict)
        orchestrator = Orchestrator(cfg)
        
        # Run generation
        success = orchestrator.run(
            repo_path=repo_url,
            output_path=output_dir,
        )
        
        if not success:
            return GenerateResponse(success=False, files={}, error="Generation failed")
        
        # Read generated files
        files = {}
        output_path = Path(output_dir)
        for file_path in output_path.rglob("*.md"):
            rel_path = file_path.relative_to(output_path)
            files[str(rel_path)] = file_path.read_text()
        
        # Also include mermaid diagrams if any
        for file_path in output_path.rglob("*.mmd"):
            rel_path = file_path.relative_to(output_path)
            files[str(rel_path)] = file_path.read_text()
        
        return GenerateResponse(success=True, files=files)
        
    except Exception as e:
        return GenerateResponse(success=False, files={}, error=str(e))
    
    finally:
        # Cleanup temp directory
        shutil.rmtree(output_dir, ignore_errors=True)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
