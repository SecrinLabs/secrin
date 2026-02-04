"""
Simple HTTP API for arc42gen.
Run with: uvicorn packages.arc42gen.api:app --port 8001
"""

import tempfile
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Use unified config from packages/config
from packages.config.settings import Settings

from .models.config import Config
from .core.orchestrator import Orchestrator

# Load settings from unified config
settings = Settings()

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
            if repo_url.startswith("https://github.com/"):
                repo_url = repo_url.replace(
                    "https://github.com/",
                    f"https://x-access-token:{request.github_token}@github.com/"
                )
        
        if not repo_url.endswith(".git"):
            repo_url = f"{repo_url}.git"
        
        # Get API key from unified config based on provider
        provider = settings.ARC42GEN_LLM_PROVIDER
        if provider == "gemini":
            api_key = settings.GEMINI_API_KEY
        else:
            api_key = settings.OPENAI_API_KEY  # Using OPENAI for anthropic fallback
        
        if not api_key:
            raise HTTPException(
                status_code=500, 
                detail=f"No API key configured for {provider}. Set GEMINI_API_KEY in your .env file"
            )
        
        # Create arc42gen config from unified settings
        config_dict = {
            'llm': {
                'provider': settings.ARC42GEN_LLM_PROVIDER,
                'model': settings.ARC42GEN_LLM_MODEL,
                'api_key': api_key,
                'max_tokens': settings.ARC42GEN_MAX_TOKENS,
            },
            'repository': {
                'include': settings.ARC42GEN_INCLUDE_PATTERNS,
                'exclude': settings.ARC42GEN_EXCLUDE_PATTERNS,
            },
            'arc42': {
                'sections': settings.ARC42GEN_SECTIONS,
                'diagram_style': settings.ARC42GEN_DIAGRAM_STYLE,
                'output_format': settings.ARC42GEN_OUTPUT_FORMAT,
            },
            'decomposition': {
                'max_module_size': settings.ARC42GEN_MAX_MODULE_SIZE,
                'max_depth': settings.ARC42GEN_MAX_DEPTH,
            },
            'output': {'path': output_dir},
        }
        
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
    return {
        "status": "ok",
        "provider": settings.ARC42GEN_LLM_PROVIDER,
        "model": settings.ARC42GEN_LLM_MODEL,
    }
