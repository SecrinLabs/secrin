from typing import List, Optional, Any
from packages.database.graph.graph import neo4j_client
from packages.ingest.edges import Edge

class GraphQuery:
    def get_node(self, node_id: str) -> Optional[Any]:
        query = """
        MATCH (n {id: $id})
        RETURN n
        """
        result = neo4j_client.run_query(query, {"id": node_id})
        return result[0]["n"] if result else None

    def get_neighbors(self, node_id: str) -> List[dict]:
        query = """
        MATCH (n {id: $id})-[r]-(m)
        RETURN n AS start, r AS rel, m AS end
        """
        return [
            {
                "start": record["start"],
                "rel": record["rel"],
                "end": record["end"]
            }
            for record in neo4j_client.run_query(query, {"id": node_id})
        ]

    def related(self, node_id: str, edge: Edge, direction: str = "out") -> List[Any]:
        rel = edge.value

        if direction == "out":
            query = f"""
            MATCH (n {{id: $id}})-[:{rel}]->(m)
            RETURN m
            """
        elif direction == "in":
            query = f"""
            MATCH (m)-[:{rel}]->(n {{id: $id}})
            RETURN m
            """
        else:  # both directions
            query = f"""
            MATCH (n {{id: $id}})-[:{rel}]-(m)
            RETURN m
            """

        return [record["m"] for record in neo4j_client.run_query(query, {"id": node_id})]

    def search(self, text: str) -> List[Any]:
        query = """
        MATCH (n)
        WHERE any(k IN keys(n) WHERE toLower(toString(n[k])) CONTAINS toLower($kw))
        RETURN n
        """

        return [
            record["n"] 
            for record in neo4j_client.run_query(query, {"kw": text})
        ]
