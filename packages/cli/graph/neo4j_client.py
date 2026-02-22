"""
Neo4j connection wrapper — supports local Neo4j Desktop and AuraDB.

Connection config is read from packages.config.settings.Settings
(which loads from the project .env file):

    NEO4J_URI   bolt://localhost:7687  or  neo4j+s://xxx.databases.neo4j.io
    NEO4J_USER  neo4j
    NEO4J_PASS  <password>
"""
from __future__ import annotations

import time
from typing import Any

from neo4j import GraphDatabase, Driver

from packages.config.settings import Settings


class NeoClient:
    """Thin wrapper around neo4j.GraphDatabase.driver with retry + helper methods."""

    _MAX_RETRIES = 3
    _RETRY_DELAY = 2.0

    def __init__(self) -> None:
        settings = Settings()
        self._uri      = settings.NEO4J_URI
        self._user     = settings.NEO4J_USER
        self._password = settings.NEO4J_PASS
        self._driver: Driver | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open the driver, retrying up to _MAX_RETRIES times."""
        last_exc: Exception | None = None
        for attempt in range(1, self._MAX_RETRIES + 1):
            try:
                self._driver = GraphDatabase.driver(
                    self._uri,
                    auth=(self._user, self._password),
                )
                self._driver.verify_connectivity()
                return
            except Exception as exc:
                last_exc = exc
                if attempt < self._MAX_RETRIES:
                    time.sleep(self._RETRY_DELAY)
        raise ConnectionError(
            f"Cannot connect to Neo4j at {self._uri} "
            f"after {self._MAX_RETRIES} attempts: {last_exc}"
        )

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None

    def __enter__(self) -> "NeoClient":
        self.connect()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    @property
    def driver(self) -> Driver:
        if not self._driver:
            raise RuntimeError(
                "NeoClient not connected. "
                "Call .connect() or use as a context manager."
            )
        return self._driver

    def run(self, cypher: str, **params: Any) -> list[dict]:
        """Execute a Cypher query in a new auto-commit session."""
        with self.driver.session() as session:
            result = session.run(cypher, **params)
            return [dict(record) for record in result]

    def ping(self) -> bool:
        """Return True if the connection is alive."""
        try:
            self.run("RETURN 1 AS ok")
            return True
        except Exception:
            return False
