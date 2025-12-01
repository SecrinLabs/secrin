from fastapi import APIRouter
from apps.api.routes.v1 import v1_router

api_router = APIRouter(prefix="/api")

# Include versioned routes
api_router.include_router(v1_router)
