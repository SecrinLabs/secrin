from fastapi import APIRouter
from apps.api.routes.v1 import ask, health, connect, integrations, projects, github

v1_router = APIRouter(prefix="/v1")

# Include all v1 route modules
v1_router.include_router(health.router)
v1_router.include_router(connect.router)
v1_router.include_router(ask.router)
v1_router.include_router(integrations.router)
v1_router.include_router(projects.router)
v1_router.include_router(github.router)