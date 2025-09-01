from pydantic import BaseModel
from typing import Dict, Any

class GithubConnect(BaseModel):
    installation_id: str

class InstallationToken(BaseModel):
    installation_token: str
    user_id: int