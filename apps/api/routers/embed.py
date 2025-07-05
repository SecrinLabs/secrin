from fastapi import APIRouter, HTTPException

from packages.ai.index import run_embedder
from apps.api.utils.threading import run_in_thread

router = APIRouter()

@router.post("/start-embeding")
def trigger_scraper():
    try:
        run_in_thread(run_embedder)
        return {"status": "Embeder started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
