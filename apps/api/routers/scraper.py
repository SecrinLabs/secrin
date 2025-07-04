from fastapi import APIRouter, BackgroundTasks
from packages.scraper.src.index import run_all_scrapers, run_sitemap, run_github, run_localgit

router = APIRouter()

@router.post("/start-scraper")
def trigger_scraper(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_all_scrapers)
    return {"status": "Scraper started"}

@router.post("/start-sitemap")
def trigger_sitemap(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_sitemap)
    return {"status": "sitemap scrapper started"}

@router.post("/start-github")
def trigger_sitemap(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_github)
    return {"status": "sitemap github started"}

@router.post("/start-localgit")
def trigger_sitemap(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_localgit)
    return {"status": "sitemap localgit started"}
