from neo4j import GraphDatabase
from typing import LiteralString, cast

from packages.config.settings import Settings

settings = Settings()

class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASS)
        )

    def run_query(self, query: str, params: dict | None = None):
        with self.driver.session() as session:
            result = session.run(cast(LiteralString, query), params or {})
            return list(result)

    def close(self):
        self.driver.close()

# singleton
neo4j_client = Neo4jClient()