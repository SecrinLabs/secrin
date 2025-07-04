import os
import sys

# Add root directory (monorepo root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from packages.scraper.src.index import run_all_scrapers

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # set this to your frontend URL in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/start-scraper")
def trigger_scraper(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_all_scrapers)
    return {"status": "Scraper started"}
