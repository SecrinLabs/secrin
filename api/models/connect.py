from pydantic import BaseModel
from typing import Dict, Any, List

class GithubConnect(BaseModel):
    installation_id: str

class InstallationToken(BaseModel):
    installation_token: str
    user_id: int

class RepositorySchema(BaseModel):
    name: str
    url: str

class SaveRepository(BaseModel):
    repository_list: list[RepositorySchema]
    user_id: int
