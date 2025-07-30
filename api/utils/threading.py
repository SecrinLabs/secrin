import threading
import time
import uuid
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from config import get_logger

# Setup logger for this module
logger = get_logger(__name__)

class ServiceManager:
    """Manages background services and their status."""
    
    def __init__(self):
        self._running_services: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._notification_callbacks: List[Callable] = []
    
    def add_notification_callback(self, callback: Callable):
        """Add a callback function to be called when services start/stop."""
        self._notification_callbacks.append(callback)
    
    def remove_notification_callback(self, callback: Callable):
        """Remove a notification callback."""
        if callback in self._notification_callbacks:
            self._notification_callbacks.remove(callback)
    
    def _notify_service_change(self, event_type: str, service_data: Dict[str, Any]):
        """Notify all callbacks about service changes."""
        notification = {
            "type": event_type,
            "service": service_data,
            "timestamp": datetime.now().isoformat()
        }
        
        for callback in self._notification_callbacks:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Notification callback error: {e}")
    
    def register_service(self, service_id: str, service_name: str, description: str = "") -> None:
        """Register a new running service."""
        with self._lock:
            service_data = {
                "id": service_id,
                "name": service_name,
                "description": description,
                "started_at": datetime.now().isoformat(),
                "status": "running"
            }
            self._running_services[service_id] = service_data
            
        # Notify about service start
        self._notify_service_change("service_started", service_data)
    
    def unregister_service(self, service_id: str) -> None:
        """Unregister a completed service."""
        service_data = None
        with self._lock:
            if service_id in self._running_services:
                service_data = self._running_services[service_id].copy()
                service_data["status"] = "completed"
                service_data["completed_at"] = datetime.now().isoformat()
                del self._running_services[service_id]
        
        # Notify about service completion
        if service_data:
            self._notify_service_change("service_completed", service_data)
    
    def get_running_services(self) -> List[Dict[str, Any]]:
        """Get list of all running services."""
        with self._lock:
            return list(self._running_services.values())
    
    def get_service_count(self) -> int:
        """Get count of running services."""
        with self._lock:
            return len(self._running_services)
    
    def is_service_running(self, service_name: str) -> bool:
        """Check if a service with given name is running."""
        with self._lock:
            return any(service["name"] == service_name for service in self._running_services.values())

# Global service manager instance
service_manager = ServiceManager()

def run_in_thread(target, service_name: str, description: str = "", *args, **kwargs):
    """
    Run a function in a background thread and track it as a service.
    
    Args:
        target: Function to run in thread
        service_name: Name of the service for tracking
        description: Optional description of what the service does
        *args, **kwargs: Arguments to pass to the target function
    """
    service_id = str(uuid.uuid4())
    
    def wrapped_target():
        try:
            # Register the service
            service_manager.register_service(service_id, service_name, description)
            
            # Set up event loop for the thread to handle async operations
            # This is needed for libraries like ollama that use async HTTP clients
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                # No event loop exists in this thread, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            try:
                # Run the actual target function
                target(*args, **kwargs)
            finally:
                # Clean up the event loop if we created it
                try:
                    pending = asyncio.all_tasks(loop)
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    if loop.is_running():
                        loop.stop()
                except Exception as e:
                    logger.error(f"⚠️  Warning: Error cleaning up event loop: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error in service '{service_name}': {str(e)}")
        finally:
            # Always unregister the service when done
            service_manager.unregister_service(service_id)
    
    thread = threading.Thread(target=wrapped_target)
    thread.daemon = True  # Make thread daemon so it doesn't block app shutdown
    thread.start()
    
    return service_id
