import logging
import json
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from apps.api.routes.v1.schemas.qa import QARequest, ContextItem
from apps.api.utils import APIResponse
from packages.memory.qa_service import QAService
from packages.memory.services.graph_service import GraphService
from packages.database.graph.graph import neo4j_client
from packages.config import Settings


router = APIRouter(prefix="/ask", tags=["Question Answering"])
settings = Settings()
logger = logging.getLogger(__name__)

# Initialize services once per module import
graph_service = GraphService(neo4j_client)
qa_service = QAService(graph_service)


@router.post(
    "",
    summary="Ask a question about the codebase",
    description=(
        "Submit a question about the codebase with different agent types. "
        "Supports streaming responses and specialized agents: "
        "pathfinder (code structure), chronicle (history), diagnostician (debugging), "
        "blueprint (architecture), sentinel (code review)."
    ),
)
async def ask(request: QARequest):
    """Ask a question using different agent types."""
    try:
        logger.info(
            f"Processing question with {request.agent_type.value} agent: {request.question[:50]}..."
        )

        # If streaming is requested, return streaming response
        if request.stream:
            return StreamingResponse(
                _stream_answer(request),
                media_type="text/event-stream"
            )

        # Non-streaming response
        result: dict[str, Any] = qa_service.ask(
            question=request.question,
            agent_type=request.agent_type.value,
            search_type=request.search_type,
            context_limit=request.context_limit,
        )

        return APIResponse.success(
            data={
                "answer": result["answer"],
                "question": result["question"],
                "agent_type": result["agent_type"],
                "context": [ContextItem(**item) for item in result["context"]],
                "context_count": result["context_count"],
                "search_type": result["search_type"],
                "node_types": result.get("node_types"),
                "model": result["model"],
                "provider": result["provider"],
            },
            message="Successfully answered the question."
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service error: {str(e)}",
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected error in ask endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your question",
        )


def _stream_answer(request: QARequest):
    """Generator for streaming answers."""
    try:
        for chunk in qa_service.ask_stream(
            question=request.question,
            agent_type=request.agent_type.value,
            search_type=request.search_type,
            context_limit=request.context_limit,
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
    except Exception as e:
        logger.exception("Error during streaming")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    finally:
        yield "data: [DONE]\n\n"
