import logging
from typing import Any
from fastapi import APIRouter, HTTPException, status

from apps.api.routes.v1.schemas.qa import (
    QARequest,
    QAResponse,
    ContextItem,
)
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
    response_model=QAResponse,
    summary="Ask a question about the codebase",
    description=(
        "Submit a natural language question about the codebase. The system "
        "retrieves relevant code context (hybrid or vector search) and uses an LLM "
        "to generate an answer."
    ),
)
async def question_answer(request: QARequest) -> QAResponse:
    """Return an AI-generated answer with supporting context.

    Process:
    1. Retrieve relevant code elements using the selected search strategy.
    2. Provide context snippets to the configured LLM provider.
    3. Return an answer plus the context used.
    """
    try:
        logger.info(f"Processing question: {request.question[:50]}...")

        result: dict[str, Any] = qa_service.ask(
            question=request.question,
            search_type=request.search_type,
            node_type=request.node_type,
            context_limit=request.context_limit,
        )

        return QAResponse(
            answer=result["answer"],
            question=result["question"],
            context=[ContextItem(**item) for item in result["context"]],
            context_count=result["context_count"],
            search_type=result["search_type"],
            node_type=result.get("node_type"),
            node_types=result.get("node_types"),
            model=result["model"],
            provider=result["provider"],
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
        logger.exception("Unexpected error in question_answer endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your question",
        )
