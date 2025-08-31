from pydantic import BaseModel
from typing import Dict, Any

class UserSignup(BaseModel):
    email: str
    username: str
    password: str