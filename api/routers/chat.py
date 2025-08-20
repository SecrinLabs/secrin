from fastapi import APIRouter, HTTPException, Depends
from fastapi_limiter.depends import RateLimiter

from engine.main import run_generator
from api.models.ChatRequest import ChatRequest

router = APIRouter()

@router.post("/", dependencies=[Depends(RateLimiter(times=3, seconds=60))])
def trigger_chat(request: ChatRequest):
    try:
        ans = run_generator(request.question)
        return {"answer": ans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))