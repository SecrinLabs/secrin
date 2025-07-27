import asyncio
import json
from typing import List, Dict, Any
from fastapi import WebSocket
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time communication."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None):
        """Accept a new WebSocket connection and store metadata."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Store connection metadata (optional)
        if client_info:
            self.connection_metadata[websocket] = {
                **client_info,
                "connected_at": datetime.now().isoformat()
            }
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Clean up metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Failed to send message to client: {e}")
            self.disconnect(websocket)
    
    async def send_json_to_client(self, data: Dict[str, Any], websocket: WebSocket):
        """Send JSON data to a specific WebSocket connection."""
        try:
            message = json.dumps(data, default=str)  # default=str handles datetime objects
            await websocket.send_text(message)
        except Exception as e:
            print(f"Failed to send JSON to client: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Failed to broadcast to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_json(self, data: Dict[str, Any]):
        """Broadcast JSON data to all connected clients."""
        try:
            message = json.dumps(data, default=str)
            await self.broadcast(message)
        except Exception as e:
            print(f"Failed to broadcast JSON: {e}")
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all active connections."""
        return [
            {
                "connection_id": id(ws),
                "metadata": self.connection_metadata.get(ws, {})
            }
            for ws in self.active_connections
        ]


class ServiceNotificationManager:
    """Manages service-related notifications for WebSocket broadcasting."""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def notify_service_started(self, service_data: Dict[str, Any]):
        """Notify all clients that a service has started."""
        notification = {
            "type": "service_started",
            "service": service_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.connection_manager.broadcast_json(notification)
    
    async def notify_service_completed(self, service_data: Dict[str, Any]):
        """Notify all clients that a service has completed."""
        notification = {
            "type": "service_completed",
            "service": service_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.connection_manager.broadcast_json(notification)
    
    async def notify_service_error(self, service_data: Dict[str, Any], error_message: str):
        """Notify all clients that a service has encountered an error."""
        notification = {
            "type": "service_error",
            "service": service_data,
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
        await self.connection_manager.broadcast_json(notification)


# Global instances
connection_manager = ConnectionManager()
service_notification_manager = ServiceNotificationManager(connection_manager)


# Utility functions for handling async operations in sync context
def run_async_in_sync_context(coro):
    """Safely run async function in sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule the task
            asyncio.create_task(coro)
        else:
            # If no loop is running, run it
            asyncio.run(coro)
    except Exception as e:
        print(f"Error running async function in sync context: {e}")


def create_service_notification_callback():
    """Create a callback function for service manager notifications."""
    
    def notification_callback(notification: Dict[str, Any]):
        """Handle service notifications and broadcast them via WebSocket."""
        notification_type = notification.get("type")
        service_data = notification.get("service", {})
        
        if notification_type == "service_started":
            run_async_in_sync_context(
                service_notification_manager.notify_service_started(service_data)
            )
        elif notification_type == "service_completed":
            run_async_in_sync_context(
                service_notification_manager.notify_service_completed(service_data)
            )
    
    return notification_callback
