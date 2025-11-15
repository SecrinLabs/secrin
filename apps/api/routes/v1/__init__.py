from fastapi import APIRouter
from apps.api.routes.v1 import health, connect

v1_router = APIRouter(prefix="/v1")

# Include all v1 route modules
v1_router.include_router(health.router)
v1_router.include_router(connect.router)