import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status

from apps.api.routes.v1.schemas.qa import (
    QARequest,
    ContextItem,
    IssueRequest,
    IssueContextItem,
)
from apps.api.utils import APIResponse
from packages.memory.qa_service import QAService
from packages.memory.services.graph_service import GraphService
from packages.memory.services.issue_analysis import IssueAnalyzer
from packages.database.graph.graph import neo4j_client
from packages.config import Settings

router = APIRouter(prefix="/ask", tags=["Question Answering"])
settings = Settings()
logger = logging.getLogger(__name__)

# Initialize services once per module import
graph_service = GraphService(neo4j_client)
qa_service = QAService(graph_service)
issue_analyzer = IssueAnalyzer(graph_service)


@router.post(
    "",
    summary="Ask a question about the codebase",
    description=(
        "Submit a natural language question about the codebase. The system "
        "retrieves relevant code context (hybrid or vector search) and uses an LLM "
        "to generate an answer."
    ),
)
async def question_answer(request: QARequest):
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

        return APIResponse.success(
            data={
                "answer": result["answer"],
                "question": result["question"],
                "context": [ContextItem(**item) for item in result["context"]],
                "context_count": result["context_count"],
                "search_type": result["search_type"],
                "node_type": result.get("node_type"),
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
        logger.exception("Unexpected error in question_answer endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your question",
        )


@router.post(
    "/issue",
    summary="Analyze a GitHub issue",
    description=(
        "Analyze a GitHub issue to identify causes and solutions based on the Knowledge Graph. "
        "Returns a detailed report and the context used."
    ),
)
async def analyze_issue(request: IssueRequest):
    """Analyze an issue and return a report.

    Process:
    1. Search for relevant code and commit history using hybrid search.
    2. Use LLM to generate a root cause analysis and suggested fix.
    3. Return the report and context.
    """
    try:
        logger.info(f"Analyzing issue: {request.title}")

        result = issue_analyzer.analyze_issue(request.title, request.body)

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )

        return APIResponse.success(
            data={
                "report": result["report"],
                "context_used": [IssueContextItem(**item) for item in result["context_used"]],
            },
            message="Successfully analyzed the issue."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in analyze_issue endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
