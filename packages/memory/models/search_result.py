from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Result from a search operation."""
    
    node: Any
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class VectorSearchResult(SearchResult):
    """Result from a vector search operation with similarity score."""
    
    score: float = 0.0
    vector_score: float = 0.0
    keyword_score: float = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        if self.score == 0.0 and self.vector_score > 0.0:
            self.score = self.vector_score
