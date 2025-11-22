from packages.database.graph.graph import neo4j_client
from packages.ingest.edges import Edge

class Explain:
    """Provide explanations for a file without relying on legacy GraphQuery."""

    def _get_node(self, node_id: str):
        result = neo4j_client.run_query("MATCH (n {id: $id}) RETURN n", {"id": node_id})
        return result[0]["n"] if result else None

    def _related(self, node_id: str, edge: Edge):
        rel = edge.value
        query = f"""
        MATCH (n {{id: $id}})-[:{rel}]->(m)
        RETURN m
        """
        return [r["m"] for r in neo4j_client.run_query(query, {"id": node_id})]

    def explain_file(self, file_id: str) -> dict:
        node = self._get_node(file_id)
        if node is None:
            return {"error": "File not found", "file_id": file_id}

        classes = self._related(file_id, Edge.HAS_CLASS)
        functions = self._related(file_id, Edge.HAS_FUNCTION)
        commits = self._related(file_id, Edge.TOUCHED)
        packages = self._related(file_id, Edge.IMPORTS)

        path = node.get("path") or node.get("name")

        return {
            "file": node,
            "classes": classes,
            "functions": functions,
            "recent_commits": commits[:5],
            "imports": packages,
            "summary": (
                f"{path} has "
                f"{len(classes)} classes, "
                f"{len(functions)} functions, "
                f"is touched by {len(commits)} commits, "
                f"and imports {len(packages)} packages."
            )
        }
