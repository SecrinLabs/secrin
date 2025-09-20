from fastapi import APIRouter, HTTPException, Depends
from fastapi_limiter.depends import RateLimiter
import requests
from fastapi import Request

from api.models.chat import ChatRequest
from engine.query.main import qa_chain
from api.utils.standard_response import standard_response
from api.utils.github_token import get_github_access_token

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
    
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.post("/github")
async def github_app_webhook_event(request: Request):
    try:
        payload = await request.json()

        action = payload.get("action")
        repo = payload.get("repository", {}).get("full_name")
        installation_id = payload.get("installation", {}).get("id")

        issue = payload.get("issue", {})
        issue_number = issue.get("number")
        issue_title = issue.get("title")
        issue_body = issue.get("body")   # the original issue description

        comment = payload.get("comment", {})
        comment_author = comment.get("user", {}).get("login")
        comment_body = comment.get("body")

        if action == "created" and comment:
            context_msg = (
                f"[{repo}] Issue #{issue_number}: {issue_title}\n\n"
                f"Issue description:\n{issue_body}\n\n"
                f"New comment by {comment_author}:\n{comment_body}"
            )
            print(context_msg)

            res = qa_chain(context_msg)
            reply_body = res.get("result", "Sorry, I couldn't generate a reply.")

            token = get_github_access_token(installation_id)

            answer = f"Hi @{payload['comment']['user']['login']}, here’s an automated answer to your comment! \n"

            # Post back to GitHub
            url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            r = requests.post(url, headers=headers, json={"body": answer + reply_body})
            r.raise_for_status()


            return standard_response(
                success=True,
                message="Webhook received",
                data={"issue_number": issue_number, "repo": repo}
            )
        else:
            return standard_response(
                success=True,
                message="Webhook received",
                data={}
            )

    except Exception as e:
        print("Error processing webhook:", e)
        raise HTTPException(status_code=500, detail=str(e))

