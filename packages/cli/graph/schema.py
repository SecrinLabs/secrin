"""
Neo4j schema initialisation.

Node labels:   File, Module, Class, Function
Relationships: CONTAINS, DEFINES, CALLS, IMPORTS, INHERITS

Idempotent — safe to call on every startup.
"""
from __future__ import annotations

from packages.cli.graph.neo4j_client import NeoClient

# ---------------------------------------------------------------------------
# Constraints (also create implicit indexes)
# ---------------------------------------------------------------------------

_CONSTRAINTS = [
    "CREATE CONSTRAINT file_id     IF NOT EXISTS FOR (f:File)     REQUIRE f.id IS UNIQUE",
    "CREATE CONSTRAINT module_id   IF NOT EXISTS FOR (m:Module)   REQUIRE m.id IS UNIQUE",
    "CREATE CONSTRAINT class_id    IF NOT EXISTS FOR (c:Class)    REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT function_id IF NOT EXISTS FOR (fn:Function) REQUIRE fn.id IS UNIQUE",
]

# ---------------------------------------------------------------------------
# Additional indexes for name-based lookups
# ---------------------------------------------------------------------------

_INDEXES = [
    "CREATE INDEX file_path     IF NOT EXISTS FOR (f:File)     ON (f.path)",
    "CREATE INDEX function_name IF NOT EXISTS FOR (fn:Function) ON (fn.name)",
    "CREATE INDEX class_name    IF NOT EXISTS FOR (c:Class)    ON (c.name)",
]


def init_schema(client: NeoClient) -> None:
    """Create constraints and indexes. Idempotent."""
    for stmt in _CONSTRAINTS + _INDEXES:
        client.run(stmt)
