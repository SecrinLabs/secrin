from pydantic import BaseModel
from typing import Dict, Any

class UpdateIntegrationRequest(BaseModel):
    name: str
    is_connected: bool
    config: Dict[str, Any]