from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str

class DiscordRequest(BaseModel):
    question: str
    user: str
    channel: str
    guild: str