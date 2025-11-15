from pydantic import BaseModel, Field
from typing import Optional

class GitHubRepoConnect(BaseModel):
    repo_url: str = Field(
        ..., 
        description="GitHub repository URL (e.g., https://github.com/owner/repo)",
        examples=["https://github.com/facebook/react"]
    )
    token: Optional[str] = Field(
        None, 
        description="GitHub personal access token (optional for public repos)"
    )
