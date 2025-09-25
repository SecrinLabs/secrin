from fastapi import APIRouter, HTTPException, Depends
from fastapi_limiter.depends import RateLimiter
import requests
from fastapi import Request
from langchain_ollama import ChatOllama

from api.models.chat import ChatRequest
from engine.query.main import qa_chain
from api.utils.standard_response import standard_response
from api.utils.github_token import get_github_access_token
from api.utils.common import clean_reply
from api.core.chat import verify_github_signature
from semantic.search.SimilaritySearch import SimilaritySearch
from config import settings

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
    
@router.post("/v2")
def trigger_chat_v2(request: ChatRequest):
    try:
        searcher = SimilaritySearch("github")  # TODO: pass collection name
        res = searcher.get_similar_answer(request.question)

        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            reasoning=False
        )
        messages = [
            ("system", "You are a helpful translator. Translate the user sentence to French."),
            ("human", f"You are an assistant. Use the context to answer the question.\n\n"
                      f"Context:\n{res}\n\n"
                      f"Question: {request.question}\n\n"
                      "Answer clearly and concisely:"),
        ]

        llm_res = llm.invoke(messages)  # await if async supported

        print(llm_res.content)

        return standard_response(
            success=True,
            message="success",
            data={"repos": llm_res.content}
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.post("/github")
async def github_app_webhook_event(request: Request):
    try:
        await verify_github_signature(request)
        
        payload = await request.json()

        BOT_USERNAME = "devsecrin[bot]"
        BOT_TRIGGER = "@secrin"

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
            comment_author = comment.get("user", {}).get("login")
    
            # prevent replying to your own bot
            if comment_author == BOT_USERNAME:
                return standard_response(
                    success=True,
                    message="Ignored self-comment",
                    data={}
                )
            
            if BOT_TRIGGER not in comment_body:
                return standard_response(
                    success=True,
                    message="Comment ignored (no bot trigger found)",
                    data={}
                )
            
            context_msg = (
                f"[{repo}] Issue #{issue_number}: {issue_title}\n\n"
                f"Issue description:\n{issue_body}\n\n"
                f"New comment by {comment_author}:\n{comment_body}"
            )
            footer = "\n\n---\nTo reply, just mention [@secrin](https://github.com/apps/devsecrin)."

            res = qa_chain(context_msg)
            reply_body = res.get("result", "Sorry, I couldn't generate a reply.")
            reply_body = clean_reply(reply_body)

            token = get_github_access_token(installation_id)

            mention = f"Hi @{payload['comment']['user']['login']},\n"

            # Post back to GitHub
            url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            r = requests.post(url, headers=headers, json={"body": mention + reply_body + footer})
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

