from typing import Dict, Any
from uuid import uuid4
import json
from packages.database.graph.graph import neo4j_client
from packages.ingest.edges import Edge

class Memory:
    def add_memory(self, type: str, content: str, metadata: Dict[str, Any] | None = None):
        if metadata is None:
            metadata = {}

        node_id = str(uuid4())

        # Convert metadata dict to JSON string for Neo4j storage
        metadata_json = json.dumps(metadata) if metadata else "{}"

        query = f"""
          CREATE (n:{type} {{
              id: $id,
              content: $content,
              metadata: $metadata_json,
              created_at: datetime()
          }})
          RETURN n.id AS id
          """

        result = neo4j_client.run_query(query, {
            "id": node_id,
            "content": content,
            "metadata_json": metadata_json
        })

        return node_id

    def get_memory(self, query_str: str):
        query = """
          MATCH (n)
          WHERE
              toString(n.content) CONTAINS $q OR
              toString(n.metadata) CONTAINS $q
          RETURN n
          """

        result = neo4j_client.run_query(query, {"q": query_str})

        return [r["n"] for r in result]
    
    def link(self, src_id: str, relation: Edge, dst_id: str):
        # Extract the value from the enum
        relation_type = relation.value if hasattr(relation, 'value') else relation
        
        query = f"""
          MATCH (a {{id: $src}}), (b {{id: $dst}})
          MERGE (a)-[r:{relation_type}]->(b)
          RETURN type(r) AS relation
          """

        result = neo4j_client.run_query(query, {
            "src": src_id,
            "dst": dst_id
        })

        return True

    def upsert_node(self, label: str, match_props: Dict[str, Any], set_props: Dict[str, Any]) -> str:
        if "id" not in set_props:
            raise ValueError("set_props must include a stable 'id'")

        # Build MERGE pattern map parameters
        merge_keys = ", ".join([f"{k}: $m_{k}" for k in match_props.keys()])
        query = f"""
          MERGE (n:{label} {{{merge_keys}}})
          ON CREATE SET n.created_at = datetime()
          SET n += $props
          RETURN n.id AS id
        """

        params = {**{f"m_{k}": v for k, v in match_props.items()}, "props": set_props}
        result = neo4j_client.run_query(query, params)
        return result[0]["id"] if result else set_props["id"]
