from pydantic import BaseModel
from typing import Optional, List

class ConnectedSourceDTO(BaseModel):
  user_id: str

class GetRemainingRepositoryDTO(BaseModel):
  user_id: int

class RemoveRepositoryDTO(BaseModel):
  user_id: int
  repo_id: int

class AddRepositoryDTO(BaseModel):
  user_id: int
  repo_id: int