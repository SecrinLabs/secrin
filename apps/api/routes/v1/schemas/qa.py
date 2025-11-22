"""
Question-Answering API schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class QARequest(BaseModel):
    """Request model for question-answering."""
    
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The question to answer",
        examples=["How does the authentication system work?"]
    )
    
    search_type: str = Field(
        default="hybrid",
        pattern="^(vector|hybrid)$",
        description="Type of search to use for context retrieval"
    )
    
    node_type: str = Field(
        default="Function",
        description="Type of code nodes to search (Function, Class, File, etc.)"
    )
    
    context_limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of context items to retrieve"
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
    context: List[ContextItem] = Field(description="Context items used for the answer")
    context_count: int = Field(description="Number of context items retrieved")
    search_type: str = Field(description="Type of search used")
    node_type: Optional[str] = Field(None, description="Node type searched")
    node_types: Optional[List[str]] = Field(None, description="Node types searched (multi-type)")
    model: str = Field(description="LLM model used")
    provider: str = Field(description="LLM provider used")


