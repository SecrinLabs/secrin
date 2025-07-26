import sys
import os

# Append root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routers import scraper, embed, chat, integration, websocket
from apps.api.utils.monitoring import setup_service_monitoring, get_service_stats
from config import settings

config = settings

app = FastAPI(
    title="DevSecRin API",
    description="API for web scraping, document embedding, and real-time service monitoring",
    version="1.0.0"
)

# Initialize WebSocket notification system
setup_service_monitoring()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # set this to your frontend URL in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "message": "DevSecRin API",
        "version": "1.0.0",
        "endpoints": {
            "scraper": "/api/scraper",
            "embed": "/api/embed", 
            "chat": "/api/chat",
            "integration": "/api/integration",
            "websocket": "/ws",
            "status": "/api/status",
            "health": "/health"
        }
    }

@app.get("/api/status")
def get_global_status():
    """Get the status of all running background services."""
    return get_service_stats()

@app.get("/health")
def health_check():
    """Health check endpoint for load balancers and monitoring."""
    stats = get_service_stats()
    return {
        "status": "healthy",
        "timestamp": "2025-07-12T10:30:00",  # This will be updated by get_service_stats
        "services_running": stats["summary"]["total_running"],
        "websocket_connections": stats["websocket"]["active_connections"]
    }

# Include routers
app.include_router(scraper.router, prefix="/api/scraper", tags=["scraper"])
app.include_router(embed.router, prefix="/api/embed", tags=["embed"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(integration.router, prefix="/api/integration", tags=["integration"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])