"""
Graph traversal search using Cypher.

For each seed node (typically from vector search), expands one hop to
surface callers, callees, co-located siblings, and imported files.

Relationship schema:
    Module  -[:CONTAINS]->  File
    File    -[:DEFINES]->   Class | Function
    Class   -[:CONTAINS]->  Function  (methods)
    Function-[:CALLS]->     Function
    File    -[:IMPORTS]->   File
    Class   -[:INHERITS]->  Class
"""
from __future__ import annotations

from dataclasses import dataclass

from packages.cli.graph.neo4j_client import NeoClient


@dataclass
class GraphHit:
    id: str
    label: str
    name: str
    path: str
    summary: str
    relation: str     # e.g. "CALLED_BY", "CALLS", "IMPORTS", "CO_LOCATED"
    via_node_id: str  # seed node ID that triggered this expansion


# ── Cypher templates ──────────────────────────────────────────────────────────

_CALLERS = """
MATCH (caller:Function)-[:CALLS]->(fn {id: $node_id})
WHERE caller.summary IS NOT NULL
RETURN caller.id AS id, 'Function' AS label,
       caller.name AS name, caller.path AS path, caller.summary AS summary
LIMIT 5
"""

_CALLEES = """
MATCH (fn {id: $node_id})-[:CALLS]->(callee:Function)
WHERE callee.summary IS NOT NULL
RETURN callee.id AS id, 'Function' AS label,
       callee.name AS name, callee.path AS path, callee.summary AS summary
LIMIT 5
"""

_FILE_IMPORTS = """
MATCH (f {id: $node_id})-[:IMPORTS]->(dep:File)
WHERE dep.summary IS NOT NULL
RETURN dep.id AS id, 'File' AS label,
       dep.name AS name, dep.path AS path, dep.summary AS summary
LIMIT 5
"""

_IMPORTED_BY = """
MATCH (other:File)-[:IMPORTS]->(f {id: $node_id})
WHERE other.summary IS NOT NULL
RETURN other.id AS id, 'File' AS label,
       other.name AS name, other.path AS path, other.summary AS summary
LIMIT 5
"""

_CO_LOCATED = """
MATCH (container)-[:CONTAINS|DEFINES]->(n {id: $node_id})
MATCH (container)-[:CONTAINS|DEFINES]->(sibling)
WHERE sibling.id <> $node_id AND sibling.summary IS NOT NULL
RETURN sibling.id AS id, labels(sibling)[0] AS label,
       sibling.name AS name, sibling.path AS path, sibling.summary AS summary
LIMIT 5
"""


# ── Helper ────────────────────────────────────────────────────────────────────

def _collect(rows: list[dict], relation: str, via_node_id: str) -> list[GraphHit]:
    hits = []
    for row in rows:
        if row.get("id"):
            hits.append(GraphHit(
                id=row["id"],
                label=row.get("label") or "",
                name=row.get("name") or "",
                path=row.get("path") or "",
                summary=row.get("summary") or "",
                relation=relation,
                via_node_id=via_node_id,
            ))
    return hits


# ── Core expansion ────────────────────────────────────────────────────────────

def expand_node(
    client: NeoClient,
    node_id: str,
    label: str,
) -> list[GraphHit]:
    """
    Run 1-hop traversal queries for one seed node.

    - Function: callers + callees + co-located siblings
    - Class:    co-located siblings (other classes/functions in same file)
    - File:     imports + imported-by + co-located files in same module

    Returns a list of GraphHit for each related node found.
    """
    hits: list[GraphHit] = []

    if label == "Function":
        hits += _collect(client.run(_CALLERS, node_id=node_id), "CALLED_BY", node_id)
        hits += _collect(client.run(_CALLEES, node_id=node_id), "CALLS", node_id)

    if label == "File":
        hits += _collect(client.run(_FILE_IMPORTS, node_id=node_id), "IMPORTS", node_id)
        hits += _collect(client.run(_IMPORTED_BY, node_id=node_id), "IMPORTED_BY", node_id)

    # Co-located siblings for all labels
    hits += _collect(client.run(_CO_LOCATED, node_id=node_id), "CO_LOCATED", node_id)

    return hits
