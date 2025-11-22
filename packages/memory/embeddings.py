"""Thin embedding module exposing only current embedding service API."""

from packages.memory.models.embedding_provider import EmbeddingProvider
from packages.memory.services.embedding_service import (
    EmbeddingService,
    get_embedding_service,
    create_embedding_for_node,
)

__all__ = [
    "EmbeddingProvider",
    "EmbeddingService",
    "get_embedding_service",
    "create_embedding_for_node",
]
