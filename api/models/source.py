from pydantic import BaseModel
from typing import Optional, List

class ConnectedSourceDTO(BaseModel):
  user_id: str