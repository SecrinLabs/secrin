from fastapi import APIRouter, BackgroundTasks, HTTPException

from packages.ai.index import run_generator
from apps.api.models.ChatRequest import ChatRequest

router = APIRouter()

@router.post("/answer")
def trigger_chat(request: ChatRequest):
    try:
        ans = run_generator(request.question)
        return {"answer": ans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))