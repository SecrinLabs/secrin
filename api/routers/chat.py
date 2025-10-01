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
from semantic.LLMStore import LLMStore
from config import settings, get_logger
from semantic.PromptStore import PromptStoreFactory, PromptType

router = APIRouter()

logger = get_logger(__name__)

dependencies=[Depends(RateLimiter(times=3, seconds=60))]
@router.post("/")
def trigger_chat(request: ChatRequest):
    try:
        logger.info(f"Triggering chat with question: {request.question}")
        res = qa_chain(request.question)

        logger.debug(f"qa_chain response: {res}")
        return standard_response(
            success=True,
            message="",
            data={
                "repos": res
            }
        )
    except Exception as e:
        logger.error(f"Error in trigger_chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/v2")
async def trigger_chat_v2(request: ChatRequest):
    try:
        logger.info(f"Triggering chat_v2 with question: {request.question}")
        
        # Retrieve similar context
        searcher = SimilaritySearch("f37c42d6-a775-4fd5-bbbe-4bd3b9fe029a")  # TODO: pass collection name dynamically
        res = searcher.get_similar_answer(request.question)

        # Get LLM instance
        llm = LLMStore().get_llm()

        # Construct prompt
        messages = (
            f"You are an assistant. Use the context to answer the question.\n\n"
            f"Context:\n{res}\n\n"
            f"Question: {request.question}\n\n"
            "Answer clearly and concisely:"
        )

        answer = llm.invoke(messages).content
            

        return standard_response(
            success=True,
            message="success",
            data={"repos": answer}
        )
    except Exception as e:
        logger.error(f"Error in trigger_chat_v2: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/github")
async def github_app_webhook_event(request: Request):
    try:
        logger.info("Received GitHub webhook event")
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
            
            footer = "\n\nTo reply, just mention [@secrin](https://github.com/apps/devsecrin)."

            text_body = (
                f"[{repo}] Issue #{issue_number}: {issue_title}\n\n"
                f"Issue description:\n{issue_body}\n\n"
                f"New comment by {comment_author}: \n {comment_body}"
            )

            searcher = SimilaritySearch("f37c42d6-a775-4fd5-bbbe-4bd3b9fe029a")
            res = searcher.get_similar_answer(text_body)

            llm = LLMStore().get_llm()

            prompt_store = PromptStoreFactory.create(PromptType.BUSINESS_ANALYST)
            prompt = prompt_store.format_prompt(comment_body, res)

            res = llm.invoke(prompt).content
            reply_body = clean_reply(res)

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
        logger.error(f"Error in github_app_webhook_event: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

