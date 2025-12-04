"""
Question-Answering API schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from packages.memory.agents import AgentType


class QARequest(BaseModel):
    """Request model for question-answering."""
    
    question: str = Field(
        ...,
        min_length=1,
        description="The question to answer",
        examples=["How does the authentication system work?"]
    )
    
    agent_type: AgentType = Field(
        default=AgentType.PATHFINDER,
        description=(
            "Type of agent to use: "
            "pathfinder (code structure), "
            "chronicle (commit history), "
            "diagnostician (debugging), "
            "blueprint (architecture), "
            "sentinel (code review)"
        )
    )
    
    search_type: str = Field(
        default="hybrid",
        pattern="^(vector|hybrid)$",
        description="Type of search to use for context retrieval"
    )
    
    context_limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of context items to retrieve"
    )
    
    stream: bool = Field(
        default=False,
        description="Whether to stream the response"
    )




class ContextItem(BaseModel):
    """Context item from search results."""
    
    type: str = Field(description="Type of the node (Function, Class, etc.)")
    name: str = Field(description="Name of the code element")
    content: str = Field(description="Content/code snippet")
    score: Optional[float] = Field(None, description="Relevance score")


class QAResponse(BaseModel):
    """Response model for question-answering."""
    
    answer: str = Field(description="Natural language answer from LLM")
    question: str = Field(description="The original question")
    agent_type: AgentType = Field(description="Type of agent used")
    context: List[ContextItem] = Field(description="Context items used for the answer")
    context_count: int = Field(description="Number of context items retrieved")
    search_type: str = Field(description="Type of search used")
    node_types: List[str] = Field(description="Node types searched")
    model: str = Field(description="LLM model used")
    provider: str = Field(description="LLM provider used")
