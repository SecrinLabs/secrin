"""Expose GraphService directly (legacy GraphQuery removed)."""

from packages.database.graph.graph import neo4j_client
from packages.memory.services.graph_service import GraphService

graph_service = GraphService(neo4j_client)

__all__ = ["GraphService", "graph_service"]
