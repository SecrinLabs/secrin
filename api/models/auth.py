from pydantic import BaseModel, EmailStr

class UserLogin(BaseModel):
    email: str
    password: str

class UserInvite(BaseModel):
    email: str
    username: str

class SetPassword(BaseModel):
    token: str
    password: str

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    subject: str