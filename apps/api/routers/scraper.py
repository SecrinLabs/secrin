from fastapi import APIRouter, HTTPException, Query

from packages.scraper.src.index import run_all_scrapers, run_scraper_by_name
from apps.api.utils.threading import run_in_thread
from packages.db.db import SessionLocal
from packages.models.integrations import Integration

router = APIRouter()

@router.post("/start-scraper")
def trigger_scraper():
    try:
        run_in_thread(run_all_scrapers)
        return {"status": "Scraper started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-scraper/{scraper_name}")
def trigger_single_scraper(scraper_name: str):
    """Start a single scraper by name in a background thread."""
    try:
        run_in_thread(lambda: run_scraper_by_name(scraper_name))
        return {"status": f"Scraper '{scraper_name}' started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list-scrapers")
def list_scrapers():
    """Return the names of all connected scrapers (integrations)."""
    session = SessionLocal()
    try:
        integrations = session.query(Integration).filter_by(is_connected=True).all()
        names = [integration.name for integration in integrations]
        return {"scrapers": names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
