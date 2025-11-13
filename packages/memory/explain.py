from packages.memory.graph import GraphQuery
from packages.ingest.edges import Edge

class Explain:
    def __init__(self):
        self.q = GraphQuery()

    def explain_file(self, file_id: str) -> dict:
      node = self.q.get_node(file_id)

      if node is None:
          return {
              "error": "File not found",
              "file_id": file_id
          }

      classes = self.q.related(file_id, Edge.HAS_CLASS)
      functions = self.q.related(file_id, Edge.HAS_FUNCTION)
      commits = self.q.related(file_id, Edge.TOUCHED)
      packages = self.q.related(file_id, Edge.IMPORTS)

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
