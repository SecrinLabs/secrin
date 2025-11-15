from fastapi import APIRouter
from packages.config.settings import Settings
from apps.api.utils import APIResponse

router = APIRouter(prefix="/health", tags=["Health"])
settings = Settings()

@router.get("")
async def health_check():
    return APIResponse.success(
        data={"version": "v1"}, message="Service is healthy"
    )
