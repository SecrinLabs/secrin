"""
WebSocket Service Status Integration

This module provides easy integration between the service manager and WebSocket notifications.
It handles the setup and configuration of real-time service monitoring.
"""

from apps.api.utils.threading import service_manager
from apps.api.utils.websocket import (
    connection_manager, 
    service_notification_manager,
    create_service_notification_callback
)


def setup_service_monitoring():
    """
    Initialize the service monitoring system with WebSocket integration.
    
    This function should be called once during application startup to set up
    the connection between the service manager and WebSocket notifications.
    """
    # Create and register the notification callback
    notification_callback = create_service_notification_callback()
    service_manager.add_notification_callback(notification_callback)
    
    print("✅ Service monitoring with WebSocket notifications initialized")


def get_service_stats():
    """Get comprehensive service and connection statistics."""
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
        "websocket": {
            "active_connections": connection_manager.get_connection_count(),
            "connection_details": connection_manager.get_connection_info()
        },
        "is_any_running": len(running_services) > 0
    }


async def broadcast_custom_notification(message: str, notification_type: str = "info"):
    """
    Broadcast a custom notification to all connected WebSocket clients.
    
    Args:
        message: The message to broadcast
        notification_type: Type of notification (info, warning, error, success)
    """
    from datetime import datetime
    
    notification = {
        "type": "custom_notification",
        "notification_type": notification_type,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    await connection_manager.broadcast_json(notification)


class ServiceMonitor:
    """
    Context manager for monitoring service operations.
    
    Usage:
        async with ServiceMonitor("my_service", "Processing data"):
            # Your service logic here
            pass
    """
    
    def __init__(self, service_name: str, description: str = ""):
        self.service_name = service_name
        self.description = description
        self.service_id = None
    
    async def __aenter__(self):
        """Start monitoring the service."""
        import uuid
        from apps.api.utils.threading import service_manager
        
        self.service_id = str(uuid.uuid4())
        service_manager.register_service(self.service_id, self.service_name, self.description)
        
        # Broadcast start notification
        await broadcast_custom_notification(
            f"Service '{self.service_name}' started", 
            "info"
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop monitoring the service."""
        if self.service_id:
            service_manager.unregister_service(self.service_id)
            
            if exc_type is not None:
                # Service failed
                await broadcast_custom_notification(
                    f"Service '{self.service_name}' failed: {str(exc_val)}", 
                    "error"
                )
            else:
                # Service completed successfully
                await broadcast_custom_notification(
                    f"Service '{self.service_name}' completed successfully", 
                    "success"
                )


# Convenience functions for common operations
async def notify_service_warning(service_name: str, warning_message: str):
    """Send a warning notification for a specific service."""
    await broadcast_custom_notification(
        f"{service_name}: {warning_message}",
        "warning"
    )


async def notify_system_status(status_message: str):
    """Send a system-wide status update."""
    await broadcast_custom_notification(
        f"System: {status_message}",
        "info"
    )
