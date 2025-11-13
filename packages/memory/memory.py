from typing import Dict, Any
from uuid import uuid4
from packages.database.graph.graph import neo4j_client
from packages.ingest.edges import Edge

class Memory:
    def add_memory(self, type: str, content: str, metadata: Dict[str, Any] | None = None):
        if metadata is None:
            metadata = {}

        node_id = str(uuid4())

        query = f"""
          CREATE (n:{type} {{
              id: $id,
              content: $content,
              metadata: $metadata,
              created_at: datetime()
          }})
          RETURN n.id AS id
          """

        result = neo4j_client.run_query(query, {
            "id": node_id,
            "content": content,
            "metadata": metadata
        })

        return node_id

    def get_memory(self, query_str: str):
        query = """
          MATCH (n)
          WHERE
              toString(n.content) CONTAINS $q OR
              any(k IN keys(n.metadata) WHERE toString(n.metadata[k]) CONTAINS $q)
          RETURN n
          """

        result = neo4j_client.run_query(query, {"q": query_str})

        return [r["n"] for r in result]
    
    def link(self, src_id: str, relation: Edge, dst_id: str):
        query = f"""
          MATCH (a {{id: $src}}), (b {{id: $dst}})
          MERGE (a)-[r:{relation}]->(b)
          RETURN type(r) AS relation
          """

        result = neo4j_client.run_query(query, {
            "src": src_id,
            "dst": dst_id
        })

        return True
