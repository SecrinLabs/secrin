from fastapi import APIRouter, HTTPException

from packages.scraper.src.index import run_all_scrapers
from apps.api.utils.threading import run_in_thread

router = APIRouter()

@router.post("/start-scraper")
def trigger_scraper():
    try:
        run_in_thread(run_all_scrapers)
        return {"status": "Scraper started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
