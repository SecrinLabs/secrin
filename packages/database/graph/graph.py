from neo4j import GraphDatabase
from typing import LiteralString, cast
import logging

from packages.config.settings import Settings

settings = Settings()
logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Neo4j database client with configurable connection pooling and timeouts.
    All settings are configurable via environment variables.
    """
    
    def __init__(self):
        """Initialize Neo4j driver with settings from configuration."""
        driver_config = settings.get_neo4j_config()
        
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASS),
            **driver_config
        )
        self.database = settings.NEO4J_DB
        
        logger.info(
            f"Neo4j client initialized: {settings.NEO4J_URI} "
            f"(database={self.database}, pool_size={driver_config['max_connection_pool_size']})"
        )

    def run_query(self, query: str, params: dict | None = None):
        """
        Execute a Cypher query with optional parameters.
        
        Args:
            query: Cypher query string
            params: Optional query parameters
            
        Returns:
            List of query results
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(cast(LiteralString, query), params or {})
            return list(result)

    def close(self):
        """Close the database connection."""
        logger.info("Closing Neo4j connection")
        self.driver.close()


# Singleton instance - configuration loaded at import time
neo4j_client = Neo4jClient()