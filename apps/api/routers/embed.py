from fastapi import APIRouter, BackgroundTasks, HTTPException
from packages.ai.index import run_enbedder

router = APIRouter()

@router.post("/start-embeding")
def trigger_scraper(background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(run_enbedder)
        return {"status": "Embeder started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
