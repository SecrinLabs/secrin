"""
Hybrid search: vector KNN + graph traversal, merged and re-ranked.

Algorithm:
  1. Embed the query via Ollama
  2. Vector KNN across Function, Class, File indexes (top K each)
  3. For each of the top-5 vector hits, run 1-hop Cypher traversal
  4. Merge all results, deduplicate by node ID
  5. Re-rank: vector hits weighted by cosine score, graph hits by source score
  6. Return top N
"""
from __future__ import annotations

from dataclasses import dataclass, field

from packages.cli.graph.neo4j_client import NeoClient
from packages.config.settings import Settings
from packages.cli.search.vector_search import VectorHit, embed_query, vector_search
from packages.cli.search.graph_search import GraphHit, expand_node


@dataclass
class SearchResult:
    id: str
    label: str
    name: str
    path: str
    summary: str
    score: float         # combined relevance score (higher = more relevant)
    matched_by: str      # "vector" | "graph" | "both"
    relation: str = ""   # non-empty for graph-only hits


def hybrid_search(
    query: str,
    client: NeoClient,
    settings: Settings,
    k: int = 10,
    top_n: int = 5,
    vector_weight: float = 0.7,
    graph_weight: float = 0.3,
) -> list[SearchResult]:
    """
    Run hybrid search and return the top_n ranked results.

    Args:
        query:          Natural-language query string.
        client:         Connected NeoClient.
        settings:       Project settings (Ollama config for embedding).
        k:              Nearest neighbours to fetch per vector index.
        top_n:          Final number of results to return.
        vector_weight:  Weight applied to cosine similarity score (0–1).
        graph_weight:   Weight applied to graph-traversal-derived scores (0–1).

    Returns:
        List of SearchResult sorted by descending combined score.
    """
    # ── 1. Embed query ────────────────────────────────────────────────────────
    embedding = embed_query(query, settings)

    # ── 2. Vector KNN ─────────────────────────────────────────────────────────
    vector_hits: list[VectorHit] = vector_search(client, embedding, k=k)

    # Map node_id → raw cosine score and metadata
    raw_scores: dict[str, float] = {h.id: h.score for h in vector_hits}
    vector_meta: dict[str, VectorHit] = {h.id: h for h in vector_hits}

    # ── 3. Graph traversal for top-5 vector hits ──────────────────────────────
    graph_hits: list[GraphHit] = []
    for hit in sorted(vector_hits, key=lambda h: h.score, reverse=True)[:5]:
        graph_hits.extend(expand_node(client, hit.id, hit.label))

    # ── 4. Merge & deduplicate ────────────────────────────────────────────────
    # Graph-derived score = source node's cosine score * graph_weight
    graph_meta: dict[str, GraphHit] = {}
    graph_scores: dict[str, float] = {}
    for g in graph_hits:
        source_score = raw_scores.get(g.via_node_id, 0.5)
        derived = source_score * graph_weight
        if g.id not in graph_scores or graph_scores[g.id] < derived:
            graph_scores[g.id] = derived
            graph_meta[g.id] = g

    # ── 5. Build result list ──────────────────────────────────────────────────
    results: list[SearchResult] = []
    seen: set[str] = set()

    # Vector hits first, sorted by raw cosine score descending
    for hit in sorted(vector_hits, key=lambda h: h.score, reverse=True):
        if hit.id in seen:
            continue
        seen.add(hit.id)

        matched_by = "both" if hit.id in graph_meta else "vector"
        results.append(SearchResult(
            id=hit.id,
            label=hit.label,
            name=hit.name,
            path=hit.path,
            summary=hit.summary,
            score=hit.score * vector_weight,
            matched_by=matched_by,
        ))

    # Graph-only hits (nodes surfaced by traversal but not in vector results)
    for gid, g in sorted(
        graph_meta.items(),
        key=lambda kv: graph_scores[kv[0]],
        reverse=True,
    ):
        if gid in seen:
            continue
        seen.add(gid)
        results.append(SearchResult(
            id=gid,
            label=g.label,
            name=g.name,
            path=g.path,
            summary=g.summary,
            score=graph_scores[gid],
            matched_by="graph",
            relation=g.relation,
        ))

    # ── 6. Final sort and trim ────────────────────────────────────────────────
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_n]
