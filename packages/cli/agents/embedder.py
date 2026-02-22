"""
Embedding agent.

Fetches nodes that have a summary but no embedding from Neo4j,
generates a vector via the configured LLM client, and writes it back.

Also creates Neo4j vector indexes on first run.

Config from packages.config.settings.Settings:
    LLM_PROVIDER            ollama | openai | anthropic
    OLLAMA_BASE_URL         Ollama host  (ollama + anthropic embed back-end)
    OLLAMA_EMBEDDING_MODEL  Embed model  (ollama + anthropic)
    OPENAI_EMBEDDING_MODEL  Embed model  (openai)
    OPENAI_API_KEY          Required when LLM_PROVIDER=openai
    EMBEDDING_DIMENSION     Vector dimensions (must match the model)
"""
from __future__ import annotations

from typing import Any

from packages.cli.agents.llm_client import client_from_settings
from packages.cli.graph.neo4j_client import NeoClient
from packages.config.settings import Settings

_LABELS = ("Function", "Class", "File")

# ---------------------------------------------------------------------------
# Vector index creation
# ---------------------------------------------------------------------------

def ensure_vector_indexes(client: NeoClient, dimensions: int) -> None:
    """Create Neo4j vector indexes for all node labels. Idempotent."""
    for label in _LABELS:
        cypher = (
            f"CREATE VECTOR INDEX summary_embeddings_{label.lower()} IF NOT EXISTS "
            f"FOR (n:{label}) ON (n.summary_embedding) "
            f"OPTIONS {{indexConfig: {{`vector.dimensions`: {dimensions}, "
            f"`vector.similarity_function`: 'cosine'}}}}"
        )
        client.run(cypher)


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

_FETCH_UNEMBEDDED = """
MATCH (n:{label})
WHERE n.summary IS NOT NULL AND n.summary_embedding IS NULL
RETURN n.id AS id, n.summary AS summary
ORDER BY n.id
LIMIT $batch_size
"""

_WRITE_EMBEDDING = """
MATCH (n {id: $node_id})
SET n.summary_embedding = $embedding
"""


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_embedder(
    client: NeoClient,
    settings: Settings,
    batch_size: int = 50,
    progress_cb: Any = None,
) -> dict[str, int]:
    """
    Embed all summarized-but-unembedded nodes across all labels.

    Args:
        client:       Connected NeoClient.
        settings:     Project settings (controls Ollama host + model).
        batch_size:   Nodes per label fetched per round-trip.
        progress_cb:  Optional callable(label, done) for progress display.

    Returns:
        dict mapping label → count of nodes embedded this run.
    """
    ensure_vector_indexes(client, settings.EMBEDDING_DIMENSION)

    llm = client_from_settings(settings)
    counts: dict[str, int] = {label: 0 for label in _LABELS}

    def _write(tx: Any, node_id: str, embedding: list[float]) -> None:
        tx.run(_WRITE_EMBEDDING, node_id=node_id, embedding=embedding)

    for label in _LABELS:
        query = _FETCH_UNEMBEDDED.format(label=label)

        while True:
            rows = client.run(query, batch_size=batch_size)
            if not rows:
                break

            for node in rows:
                try:
                    embedding = llm.embed(node["summary"])
                except Exception as exc:
                    print(f"    [warn] embedding failed for {node['id']}: {exc}")
                    continue

                with client.driver.session() as session:
                    session.execute_write(_write, node["id"], embedding)

                counts[label] += 1
                if progress_cb:
                    progress_cb(label, counts[label])

    return counts
