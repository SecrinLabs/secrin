import sys
import os

# Append root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routers import scraper, embed, chat, integration
from apps.api.utils.threading import service_manager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # set this to your frontend URL in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status")
def get_global_status():
    """Get the status of all running background services."""
    running_services = service_manager.get_running_services()
    
    # Group services by type
    scrapers = [s for s in running_services if s["name"].startswith("scraper")]
    embedders = [s for s in running_services if s["name"] == "embedder"]
    others = [s for s in running_services if not s["name"].startswith("scraper") and s["name"] != "embedder"]
    
    return {
        "services": {
            "scrapers": scrapers,
            "embedders": embedders,
            "others": others
        },
        "summary": {
            "total_running": len(running_services),
            "scrapers_running": len(scrapers),
            "embedders_running": len(embedders),
            "others_running": len(others)
        },
        "is_any_running": len(running_services) > 0
    }

app.include_router(scraper.router, prefix="/api/scraper")
app.include_router(embed.router, prefix="/api/embed")
app.include_router(chat.router, prefix="/api/chat")
app.include_router(integration.router, prefix="/api/integration")