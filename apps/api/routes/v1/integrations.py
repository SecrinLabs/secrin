from fastapi import APIRouter, Request, Header, BackgroundTasks
from packages.config.settings import Settings
from packages.app_store.github.utils import verify_github_signature, SignatureVerificationError
from packages.app_store.github.webhook import handle_github_event, run_ingestion
from apps.api.utils.response import APIResponse
from apps.api.utils.exceptions import BadRequestException, UnauthorizedException
import logging

router = APIRouter(prefix="/integrations", tags=["Integrations"])
settings = Settings()
logger = logging.getLogger(__name__)

@router.post("/github/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(None)
):
    """
    Handle GitHub Webhooks.
    """
    if not x_github_event:
        raise BadRequestException(message="Missing X-GitHub-Event header")

    # Always verify signature in production
    try:
        await verify_github_signature(request, settings.GITHUB_WEBHOOK_SECRET)
    except SignatureVerificationError as e:
        logger.warning(f"GitHub signature verification failed: {str(e)}")
        raise UnauthorizedException(message=str(e))
    
    payload = await request.json()
    
    result = handle_github_event(x_github_event, payload)
    
    if result.get("status") == "triggered" and result.get("task") == "ingest":
        repo_url = result.get("repo_url")
        branch = result.get("branch")
        if repo_url:
            background_tasks.add_task(run_ingestion, repo_url, branch)
            return APIResponse.success(
                message=f"Ingestion triggered for {repo_url} on {branch}",
                data={"status": "accepted", "repo_url": repo_url, "branch": branch}
            )
            
    return APIResponse.success(
        message="Webhook processed",
        data=result
    )
