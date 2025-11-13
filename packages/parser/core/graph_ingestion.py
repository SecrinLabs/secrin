"""Service for ingesting parsed data into Neo4j"""
from typing import Any, Dict
from datetime import datetime

from packages.database.graph.graph import neo4j_client
from packages.parser.models import (
    GraphData,
    RepoNode,
    FileNode,
    ClassNode,
    FunctionNode,
    VariableNode,
    DocNode,
    PackageNode,
    CommitNode,
    ModuleNode,
    TestNode,
    IssueNode,
    Relationship,
)


class GraphIngestionService:
    """Service to ingest parsed graph data into Neo4j"""
    
    def __init__(self):
        self.client = neo4j_client
    
    def ingest_graph_data(self, graph_data: GraphData):
        """
        Ingest all nodes and relationships from GraphData into Neo4j
        
        Args:
            graph_data: Parsed graph data containing nodes and relationships
        """
        print("Starting Neo4j ingestion...")
        
        # Create constraints and indexes first (idempotent)
        self._create_constraints()
        
        # Ingest nodes
        print(f"Ingesting {len(graph_data.nodes)} nodes...")
        for node in graph_data.nodes:
            self._ingest_node(node)
        
        # Ingest relationships
        print(f"Ingesting {len(graph_data.relationships)} relationships...")
        for rel in graph_data.relationships:
            self._ingest_relationship(rel)
        
        print("Ingestion complete!")
    
    def _create_constraints(self):
        """Create unique constraints and indexes for node types"""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repo) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Class) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (fn:Function) REQUIRE fn.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (v:Variable) REQUIRE v.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Doc) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Package) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (cm:Commit) REQUIRE cm.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Module) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Test) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Issue) REQUIRE i.id IS UNIQUE",
        ]
        
        for constraint in constraints:
            try:
                self.client.run_query(constraint)
            except Exception as e:
                print(f"Warning: Could not create constraint: {e}")
    
    def _ingest_node(self, node: Any):
        """
        Ingest a single node into Neo4j
        
        Args:
            node: Node object (RepoNode, FileNode, etc.)
        """
        # Determine node label
        node_type = type(node).__name__.replace("Node", "")
        
        # Convert node to properties dict
        props = self._node_to_properties(node)
        
        # Create MERGE query to avoid duplicates
        query = f"""
        MERGE (n:{node_type} {{id: $id}})
        SET n += $props
        RETURN n
        """
        
        try:
            self.client.run_query(query, {"id": node.id, "props": props})
        except Exception as e:
            print(f"Error ingesting node {node.id}: {e}")
    
    def _ingest_relationship(self, rel: Relationship):
        """
        Ingest a relationship into Neo4j
        
        Args:
            rel: Relationship object
        """
        # Determine node labels from IDs (simple heuristic)
        source_label = self._infer_label_from_id(rel.source_id)
        target_label = self._infer_label_from_id(rel.target_id)
        
        # Convert relationship properties for Neo4j compatibility
        props = self._sanitize_properties(rel.properties)
        
        query = f"""
        MATCH (source:{source_label} {{id: $source_id}})
        MATCH (target:{target_label} {{id: $target_id}})
        MERGE (source)-[r:{rel.type.value}]->(target)
        SET r += $props
        RETURN r
        """
        
        try:
            self.client.run_query(query, {
                "source_id": rel.source_id,
                "target_id": rel.target_id,
                "props": props
            })
        except Exception as e:
            print(f"Error ingesting relationship {rel.source_id} -> {rel.target_id}: {e}")
    
    def _sanitize_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize properties for Neo4j compatibility
        
        Args:
            properties: Dictionary of properties
        
        Returns:
            Sanitized properties dictionary
        """
        import json
        sanitized = {}
        
        for key, value in properties.items():
            if isinstance(value, datetime):
                sanitized[key] = value.isoformat()
            elif value is None:
                # Skip None values
                continue
            elif isinstance(value, dict):
                # Convert dictionaries to JSON strings
                sanitized[key] = json.dumps(value)
            elif isinstance(value, list):
                # Check if list contains only primitive types
                if value and not all(isinstance(item, (str, int, float, bool)) for item in value):
                    # Convert to JSON string if list contains complex objects
                    sanitized[key] = json.dumps(value)
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _node_to_properties(self, node: Any) -> Dict[str, Any]:
        """
        Convert a node object to a properties dictionary for Neo4j
        
        Args:
            node: Node object
        
        Returns:
            Dictionary of properties
        """
        props = node.model_dump()
        return self._sanitize_properties(props)
    
    def _infer_label_from_id(self, node_id: str) -> str:
        """
        Infer node label from ID structure
        
        Args:
            node_id: Node ID string
        
        Returns:
            Inferred node label
        """
        # IDs are structured like: repo:name:type:...
        # or package:name
        if node_id.startswith("repo:"):
            return "Repo"
        elif node_id.startswith("package:"):
            return "Package"
        elif ":file:" in node_id or node_id.endswith(":file"):
            return "File"
        elif ":class:" in node_id:
            return "Class"
        elif ":function:" in node_id or ":method:" in node_id:
            return "Function"
        elif ":variable:" in node_id:
            return "Variable"
        elif ":doc:" in node_id:
            return "Doc"
        elif ":commit:" in node_id:
            return "Commit"
        elif ":module:" in node_id:
            return "Module"
        elif ":test:" in node_id:
            return "Test"
        elif ":issue:" in node_id:
            return "Issue"
        else:
            # Default fallback
            return "Node"
    
    def clear_repository_data(self, repo_name: str):
        """
        Clear all data for a specific repository
        
        Args:
            repo_name: Name of the repository to clear
        """
        query = """
        MATCH (r:Repo {name: $repo_name})
        OPTIONAL MATCH (r)-[*]-(n)
        DETACH DELETE r, n
        """
        
        self.client.run_query(query, {"repo_name": repo_name})
        print(f"Cleared data for repository: {repo_name}")
    
    def get_repository_stats(self, repo_name: str) -> Dict[str, int]:
        """
        Get comprehensive statistics for a repository in the graph
        
        Args:
            repo_name: Name of the repository
        
        Returns:
            Dictionary with counts of different node types
        """
        query = """
        MATCH (r:Repo {name: $repo_name})
        OPTIONAL MATCH (r)-[:HAS_FILE]->(f:File)
        OPTIONAL MATCH (f)-[:CONTAINS_CLASS]->(c:Class)
        OPTIONAL MATCH (f)-[:CONTAINS_FUNCTION]->(fn:Function)
        OPTIONAL MATCH (f)-[:HAS_TEST]->(t:Test)
        OPTIONAL MATCH (f)-[:HAS_DOC]->(d:Doc)
        OPTIONAL MATCH (commit:Commit)-[:TOUCHED]->(f)
        OPTIONAL MATCH (f)-[:IMPORTS]->(p:Package)
        RETURN 
            count(DISTINCT f) as files,
            count(DISTINCT c) as classes,
            count(DISTINCT fn) as functions,
            count(DISTINCT t) as tests,
            count(DISTINCT d) as docs,
            count(DISTINCT commit) as commits,
            count(DISTINCT p) as packages
        """
        
        result = self.client.run_query(query, {"repo_name": repo_name})
        
        if result:
            record = result[0]
            return {
                "files": record["files"],
                "classes": record["classes"],
                "functions": record["functions"],
                "tests": record["tests"],
                "docs": record["docs"],
                "commits": record["commits"],
                "packages": record["packages"],
            }
        
        return {
            "files": 0,
            "classes": 0,
            "functions": 0,
            "tests": 0,
            "docs": 0,
            "commits": 0,
            "packages": 0,
        }


# Singleton instance
graph_ingestion_service = GraphIngestionService()
