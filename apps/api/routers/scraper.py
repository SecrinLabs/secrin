from fastapi import APIRouter, HTTPException

from packages.scraper.src.index import run_all_scrapers, run_sitemap, run_github, run_localgit
from apps.api.utils.threading import run_in_thread

router = APIRouter()

@router.post("/start-scraper")
def trigger_scraper():
    try:
        run_in_thread(run_all_scrapers)
        return {"status": "Scraper started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-sitemap")
def trigger_sitemap():
    try:
        run_in_thread(run_sitemap)
        return {"status": "sitemap scrapper started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-github")
def trigger_github():
    try:
        run_in_thread(run_github)
        return {"status": "sitemap github started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-localgit")
def trigger_localgit():
    try:
        run_in_thread(run_localgit)
        return {"status": "sitemap localgit started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
