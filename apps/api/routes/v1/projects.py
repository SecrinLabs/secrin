from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from apps.api.utils.response import APIResponse
import uuid
from datetime import datetime
import logging

router = APIRouter(prefix="/projects", tags=["Projects"])
logger = logging.getLogger(__name__)


class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    repoName: str


class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    repoName: str
    repoUrl: Optional[str] = None
    createdAt: str
    status: str = "active"


@router.post("")
async def create_project(request: CreateProjectRequest):
    """
    Create a new project with a sample repository in the user's GitHub account.
    
    TODO: Implement actual GitHub App integration:
    1. Get installation access token
    2. Create repository via GitHub API
    3. Add initial content to the repository
    """
    try:
        # Generate project ID
        project_id = str(uuid.uuid4())
        
        # TODO: Use GitHub App to create the repository
        # For now, we create a mock response
        # In production, this would:
        # 1. Get the user's GitHub App installation
        # 2. Create a new repository using the installation access token
        # 3. Add sample files to the repository
        
        # Mock repo URL (replace with actual GitHub API integration)
        repo_url = f"https://github.com/owner/{request.repoName}"
        
        project = Project(
            id=project_id,
            name=request.name,
            description=request.description,
            repoName=request.repoName,
            repoUrl=repo_url,
            createdAt=datetime.utcnow().isoformat(),
            status="active"
        )
        
        logger.info(f"Created project: {project.name} with repo: {project.repoName}")
        
        return APIResponse.success(
            message="Project created successfully",
            data={
                "project": project.model_dump(),
                "repoUrl": repo_url
            }
        )
    except Exception as e:
        logger.error(f"Failed to create project: {str(e)}")
        return APIResponse.error(
            message="Failed to create project",
            error=str(e)
        )
