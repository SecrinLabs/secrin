from pydantic import BaseModel

class UserLogin(BaseModel):
    email: str
    password: str

class UserSignup(BaseModel):
    email: str
    username: str
    password: str