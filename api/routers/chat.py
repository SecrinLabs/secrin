from fastapi import APIRouter, HTTPException, Depends
from fastapi_limiter.depends import RateLimiter

from api.models.chat import ChatRequest

from engine.query.main import qa_chain
from api.utils.standard_response import standard_response

router = APIRouter()

dependencies=[Depends(RateLimiter(times=3, seconds=60))]
@router.post("/")
def trigger_chat(request: ChatRequest):
    try:
        res = qa_chain(request.question)
        return standard_response(
            success=True,
            message="",
            data={
                "repos": res
            }
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))