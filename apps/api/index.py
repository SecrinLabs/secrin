import sys
import os

# Append root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routers import scraper

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # set this to your frontend URL in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scraper.router, prefix="/scraper")