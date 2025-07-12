from fastapi import APIRouter, HTTPException

from packages.ai.index import run_embedder
from apps.api.utils.threading import run_in_thread, service_manager

router = APIRouter()

@router.post("/start-embeding")
def trigger_scraper():
    try:
        # Check if embedder is already running
        if service_manager.is_service_running("embedder"):
            return {
                "status": "Embedder is already running",
                "message": "Please wait for the current embedding process to complete"
            }
        
        service_id = run_in_thread(
            run_embedder,
            service_name="embedder",
            description="Processing and embedding documents from database"
        )
        
        return {
            "status": "Embedder started",
            "service_id": service_id,
            "message": "Embedding process started in background"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def get_embedding_status():
    """Get the current status of background embedding services."""
    try:
        running_services = service_manager.get_running_services()
        embedding_services = [
            service for service in running_services 
            if service["name"] == "embedder"
        ]
        
        return {
            "embedding_services": embedding_services,
            "total_running": len(embedding_services),
            "is_running": len(embedding_services) > 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
