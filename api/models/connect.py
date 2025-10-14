from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

class GithubConnect(BaseModel):
    installation_id: str

class InstallationToken(BaseModel):
    installation_token: str
    user_guid: UUID

class OwnerSchema(BaseModel):
    login: Optional[str]
    type: Optional[str]

class RepositorySchema(BaseModel):
    id: int
    name: str
    full_name: str
    url: str

    html_url: Optional[str]
    description: Optional[str]
    private: Optional[bool]
    language: Optional[str]
    topics: Optional[List[str]] = []
    stargazers_count: Optional[int]
    forks_count: Optional[int]
    watchers_count: Optional[int]
    default_branch: Optional[str]
    open_issues_count: Optional[int]
    has_issues: Optional[bool]
    has_discussions: Optional[bool]
    archived: Optional[bool]
    created_at: Optional[str]
    updated_at: Optional[str]
    pushed_at: Optional[str]
    clone_url: Optional[str]
    owner: Optional[OwnerSchema]

class SaveRepository(BaseModel):
    repository_list: list[RepositorySchema]
    user_guid: UUID

class DisconnectService(BaseModel):
    user_guid: UUID
    service_type: str

class GetAllIntegrations(BaseModel):
    user_guid: UUID

class SaveDiscordTokenRequestDTO(BaseModel):
    code: str
    guild_id: str
