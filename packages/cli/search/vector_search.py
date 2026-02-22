"""
Vector KNN search over Neo4j vector indexes.

Uses the pre-built summary_embeddings_{function|class|file} indexes
to find the top-K nearest neighbours for an embedded query string.

Config from packages.config.settings.Settings:
    OLLAMA_BASE_URL         Ollama host (default http://localhost:11434)
    OLLAMA_EMBEDDING_MODEL  Model for embeddings (default mxbai-embed-large)
"""
from __future__ import annotations

from dataclasses import dataclass

import requests

from packages.cli.graph.neo4j_client import NeoClient
from packages.config.settings import Settings

_LABELS = ("Function", "Class", "File")


@dataclass
class VectorHit:
    id: str
    label: str
    name: str
    path: str
    summary: str
    score: float


def embed_query(query: str, settings: Settings) -> list[float]:
    """Embed a query string via Ollama and return the vector."""
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/embeddings"
    resp = requests.post(
        url,
        json={"model": settings.OLLAMA_EMBEDDING_MODEL, "prompt": query},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


_VECTOR_KNN = """
CALL db.index.vector.queryNodes($index_name, $k, $embedding)
YIELD node, score
RETURN
    node.id      AS id,
    node.name    AS name,
    node.path    AS path,
    node.summary AS summary,
    score
"""


def vector_search(
    client: NeoClient,
    embedding: list[float],
    k: int = 10,
) -> list[VectorHit]:
    """
    Query each vector index and return all hits, unsorted.

    Args:
        client:    Connected NeoClient.
        embedding: Query vector (must match EMBEDDING_DIMENSION).
        k:         Nearest neighbours to fetch per label index.

    Returns:
        Flat list of VectorHit objects across all labels.
    """
    hits: list[VectorHit] = []

    for label in _LABELS:
        index_name = f"summary_embeddings_{label.lower()}"
        try:
            rows = client.run(
                _VECTOR_KNN,
                index_name=index_name,
                k=k,
                embedding=embedding,
            )
        except Exception:
            # Index may not exist yet (e.g. no nodes of this label were embedded)
            continue

        for row in rows:
            hits.append(VectorHit(
                id=row["id"] or "",
                label=label,
                name=row["name"] or "",
                path=row["path"] or "",
                summary=row["summary"] or "",
                score=float(row["score"]),
            ))

    return hits
