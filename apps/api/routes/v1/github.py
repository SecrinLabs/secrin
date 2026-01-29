from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from apps.api.utils.response import APIResponse
import logging

router = APIRouter(prefix="/github", tags=["GitHub"])
logger = logging.getLogger(__name__)

# In-memory storage for installations (replace with database in production)
# Key: user_id (or session), Value: installation details
_installations: dict[str, dict] = {}


class InstallationCallback(BaseModel):
    installation_id: int
    setup_action: str
    code: Optional[str] = None


@router.post("/installation/callback")
async def save_installation(data: InstallationCallback):
    """
    Save the GitHub App installation details after user installs the app.
    Called from the frontend callback page.
    """
    try:
        # For now, use a simple key. In production, use actual user ID from session
        user_key = "default_user"
        
        _installations[user_key] = {
            "installation_id": data.installation_id,
            "setup_action": data.setup_action,
            "code": data.code,
        }
        
        logger.info(f"Saved GitHub App installation: {data.installation_id} for user: {user_key}")
        
        return APIResponse.success(
            message="Installation saved successfully",
            data={"installation_id": data.installation_id}
        )
    except Exception as e:
        logger.error(f"Failed to save installation: {str(e)}")
        return APIResponse.error(
            message="Failed to save installation",
            error=str(e)
        )


@router.get("/installation/status")
async def check_installation_status():
    """
    Check if the user has installed the GitHub App.
    """
    try:
        # For now, use a simple key. In production, use actual user ID from session
        user_key = "default_user"
        
        installation = _installations.get(user_key)
        installed = installation is not None
        
        logger.info(f"GitHub App installation status for {user_key}: {installed}")
        
        return APIResponse.success(
            message="Installation status retrieved",
            data={
                "installed": installed,
                "installationId": installation.get("installation_id") if installation else None,
                "accountLogin": None  # Would need GitHub API call to get this
            }
        )
    except Exception as e:
        logger.error(f"Failed to check installation status: {str(e)}")
        return APIResponse.error(
            message="Failed to check installation status",
            error=str(e)
        )
