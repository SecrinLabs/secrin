from fastapi import APIRouter
from packages import models

router = APIRouter()

@router.get("/")
async def list_integrations():
    return await models.get_integrations()

@router.patch("/{name}")
async def toggle_integration(name: str, is_connected: bool):
    await models.set_integration_status(name, is_connected)
    return {"message": "Updated", "name": name, "is_connected": is_connected}
