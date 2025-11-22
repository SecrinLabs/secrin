"""Public API surface for memory package (legacy exports removed)."""

from packages.memory.services.embedding_service import (
    EmbeddingService,
    get_embedding_service,
    create_embedding_for_node,
)
from packages.memory.services.graph_service import GraphService
from packages.memory.models.embedding_provider import EmbeddingProvider
from packages.memory.models.search_result import SearchResult, VectorSearchResult

__all__ = [
    "EmbeddingService",
    "get_embedding_service",
    "create_embedding_for_node",
    "GraphService",
    "EmbeddingProvider",
    "SearchResult",
    "VectorSearchResult",
]
