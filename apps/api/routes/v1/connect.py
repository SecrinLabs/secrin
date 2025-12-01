from fastapi import APIRouter, BackgroundTasks
from apps.api.utils import APIResponse
from apps.api.routes.v1.schemas.connect import (
    GitHubRepoConnect
)
from packages.ingest.commit_decisions import process_repository


router = APIRouter(prefix="/connect", tags=["Connect"])


@router.post("/github")
async def connect_github_repo(repo_data: GitHubRepoConnect, background_tasks: BackgroundTasks):
    repo_path = repo_data.repo_url.replace("https://github.com/", "").replace("http://github.com/", "").strip("/")
    parts = repo_path.split("/")
    
    if len(parts) >= 2:
        owner = parts[0]
        repo = parts[1]
    else:
        owner = "unknown"
        repo = "unknown"

    background_tasks.add_task(process_repository, repo_data.repo_url)
        
    return APIResponse.success(
        data={
            "connection_id": "gh_conn_123456",
            "provider": "github",
            "repo_url": repo_data.repo_url,
            "owner": owner,
            "repository": repo,
            "full_name": f"{owner}/{repo}",
            "status": "connected",
            "has_token": repo_data.token is not None,
        },
        message=f"Successfully connected to {owner}/{repo}"
    )