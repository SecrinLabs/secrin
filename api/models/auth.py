from pydantic import BaseModel
from typing import Dict, Any

class UserLogin(BaseModel):
    email: str
    password: str

class UserSignup(BaseModel):
    email: str
    username: str
    password: str