import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

from apps.api.utils.websocket import connection_manager
from apps.api.utils.threading import service_manager

router = APIRouter()


@router.websocket("/status")
async def websocket_status(websocket: WebSocket):
    """WebSocket endpoint for real-time service status updates."""
    await connection_manager.connect(websocket, {"type": "status_monitor"})
    
    try:
        while True:
            # Get current service status
            running_services = service_manager.get_running_services()
            
            # Group services by type
            scrapers = [s for s in running_services if s["name"].startswith("scraper")]
            embedders = [s for s in running_services if s["name"] == "embedder"]
            others = [s for s in running_services if not s["name"].startswith("scraper") and s["name"] != "embedder"]
            
            status_data = {
                "type": "status_update",
                "timestamp": datetime.now().isoformat(),
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
                "is_any_running": len(running_services) > 0,
                "connections": connection_manager.get_connection_count()
            }
            
            # Send status update to this client
            await connection_manager.send_json_to_client(status_data, websocket)
            
            # Wait 2 seconds before next update
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket status error: {e}")
        connection_manager.disconnect(websocket)


@router.websocket("/notifications")
async def websocket_notifications(websocket: WebSocket):
    """WebSocket endpoint for service start/stop notifications."""
    await connection_manager.connect(websocket, {"type": "notification_listener"})
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "connected",
            "message": "Connected to service notifications",
            "timestamp": datetime.now().isoformat(),
            "client_id": id(websocket)
        }
        await connection_manager.send_json_to_client(welcome_message, websocket)
        
        # Keep connection alive and listen for notifications
        # The actual notifications are sent via the service_manager callbacks
        while True:
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket notifications error: {e}")
        connection_manager.disconnect(websocket)


@router.websocket("/live")
async def websocket_live_feed(websocket: WebSocket):
    """WebSocket endpoint combining both status updates and notifications."""
    await connection_manager.connect(websocket, {"type": "live_feed"})
    
    try:
        # Send initial connection message
        welcome_message = {
            "type": "live_feed_connected",
            "message": "Connected to live service feed",
            "timestamp": datetime.now().isoformat()
        }
        await connection_manager.send_json_to_client(welcome_message, websocket)
        
        # Send periodic status updates
        while True:
            running_services = service_manager.get_running_services()
            
            # Group services by type
            scrapers = [s for s in running_services if s["name"].startswith("scraper")]
            embedders = [s for s in running_services if s["name"] == "embedder"]
            others = [s for s in running_services if not s["name"].startswith("scraper") and s["name"] != "embedder"]
            
            live_data = {
                "type": "live_update",
                "timestamp": datetime.now().isoformat(),
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
                "is_any_running": len(running_services) > 0,
                "connection_info": {
                    "active_connections": connection_manager.get_connection_count(),
                    "update_interval": "3s"
                }
            }
            
            await connection_manager.send_json_to_client(live_data, websocket)
            
            # Wait 3 seconds for live feed (slightly longer than status)
            await asyncio.sleep(3)
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket live feed error: {e}")
        connection_manager.disconnect(websocket)


@router.get("/connections")
async def get_websocket_connections():
    """Get information about active WebSocket connections."""
    return {
        "active_connections": connection_manager.get_connection_count(),
        "connection_details": connection_manager.get_connection_info(),
        "timestamp": datetime.now().isoformat()
    }
