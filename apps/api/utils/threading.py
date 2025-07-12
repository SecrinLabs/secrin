import threading
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

class ServiceManager:
    """Manages background services and their status."""
    
    def __init__(self):
        self._running_services: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def register_service(self, service_id: str, service_name: str, description: str = "") -> None:
        """Register a new running service."""
        with self._lock:
            self._running_services[service_id] = {
                "id": service_id,
                "name": service_name,
                "description": description,
                "started_at": datetime.now().isoformat(),
                "status": "running"
            }
    
    def unregister_service(self, service_id: str) -> None:
        """Unregister a completed service."""
        with self._lock:
            if service_id in self._running_services:
                del self._running_services[service_id]
    
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
            
            # Run the actual target function
            target(*args, **kwargs)
        except Exception as e:
            print(f"❌ Error in service '{service_name}': {str(e)}")
        finally:
            # Always unregister the service when done
            service_manager.unregister_service(service_id)
    
    thread = threading.Thread(target=wrapped_target)
    thread.daemon = True  # Make thread daemon so it doesn't block app shutdown
    thread.start()
    
    return service_id
