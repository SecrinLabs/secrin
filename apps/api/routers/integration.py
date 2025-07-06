from fastapi import APIRouter, HTTPException

from packages.db.integrations import get_all_integrations, toggle_integration_connection, update_integration as db_update_integration
from apps.api.models.UpdateIntegrationRequest import UpdateIntegrationRequest

router = APIRouter()

@router.get("/")
def list_integrations():
    return get_all_integrations()

@router.patch("/toggle")
def toggle_integration(name: str):
    result = toggle_integration_connection(name)
    if "error" in result:
        if result["error"] == "Integration not found":
            raise HTTPException(status_code=404, detail=result["error"])
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.patch("/update")
def update_integration(request: UpdateIntegrationRequest):
    result = db_update_integration(request)
    if "error" in result:
        if result["error"] == "Integration not found":
            raise HTTPException(status_code=404, detail=result["error"])
        raise HTTPException(status_code=500, detail=result["error"])
    return result
