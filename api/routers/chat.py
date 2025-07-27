from fastapi import APIRouter, HTTPException

from engine.main import run_generator
from api.models.ChatRequest import ChatRequest

router = APIRouter()

@router.post("/")
def trigger_chat(request: ChatRequest):
    try:
        ans = run_generator(request.question)
        return {"answer": ans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))