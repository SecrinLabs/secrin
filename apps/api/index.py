import sys
import os

# Append root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routers import scraper, embed, chat, integration

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # set this to your frontend URL in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scraper.router, prefix="/api/scraper")
app.include_router(embed.router, prefix="/api/embed")
app.include_router(chat.router, prefix="/api/chat")
app.include_router(integration.router, prefix="/api/integration")