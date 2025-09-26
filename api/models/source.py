from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

class ConnectedSourceDTO(BaseModel):
  user_guid: UUID

class GetRemainingRepositoryDTO(BaseModel):
  user_guid: UUID

class RemoveRepositoryDTO(BaseModel):
  user_guid: UUID
  repo_id: int

class AddRepositoryDTO(BaseModel):
  user_guid: UUID
  repo_id: int