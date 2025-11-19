from typing import List, Optional, Any, Literal
from packages.database.graph.graph import neo4j_client
from packages.ingest.edges import Edge
from packages.memory.embeddings import get_embedding_service, EmbeddingProvider

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

    def search(self, text: str, node_label: Optional[str] = None) -> List[Any]:
        """Simple text search across nodes."""
        label_filter = f":{node_label}" if node_label else ""
        query = f"""
        MATCH (n{label_filter})
        WHERE n.name IS NOT NULL AND toLower(n.name) CONTAINS toLower($kw)
           OR n.id IS NOT NULL AND toLower(n.id) CONTAINS toLower($kw)
        RETURN n
        LIMIT 10
        """

        return [
            record["n"] 
            for record in neo4j_client.run_query(query, {"kw": text})
        ]
    
    def vector_search(
        self,
        query_text: str,
        node_label: Literal["Function", "Class", "File", "Doc", "Module", "Commit"],
        top_k: int = 10,
        provider: EmbeddingProvider = EmbeddingProvider.OLLAMA
    ) -> List[dict]:
        """
        Semantic search using vector embeddings.
        
        Args:
            query_text: The search query
            node_label: The type of nodes to search (Function, Class, File, Doc, Module, Commit)
            top_k: Number of results to return
            provider: Embedding provider to use
            
        Returns:
            List of nodes with their similarity scores
        """
        # Generate embedding for the query
        embedding_service = get_embedding_service(provider)
        query_embedding = embedding_service.embed_text(query_text)
        
        # Perform vector search in Neo4j
        query = f"""
        CALL db.index.vector.queryNodes('{node_label.lower()}_embedding_index', $top_k, $query_vector)
        YIELD node, score
        RETURN node, score
        ORDER BY score DESC
        """
        
        results = neo4j_client.run_query(query, {
            "query_vector": query_embedding,
            "top_k": top_k
        })
        
        return [
            {
                "node": record["node"],
                "score": record["score"]
            }
            for record in results
        ]
    
    def hybrid_search(
        self,
        query_text: str,
        node_label: Literal["Function", "Class", "File", "Doc", "Module", "Commit"],
        top_k: int = 10,
        vector_weight: float = 0.7,
        provider: EmbeddingProvider = EmbeddingProvider.OLLAMA
    ) -> List[dict]:
        """
        Hybrid search combining vector similarity and keyword matching.
        
        Args:
            query_text: The search query
            node_label: The type of nodes to search
            top_k: Number of results to return
            vector_weight: Weight for vector similarity (0-1). Keyword weight is (1 - vector_weight)
            provider: Embedding provider to use
            
        Returns:
            List of nodes with combined scores
        """
        # Get vector search results
        vector_results = self.vector_search(query_text, node_label, top_k * 2, provider)
        
        # Get keyword search results
        keyword_query = f"""
        MATCH (n:{node_label})
        WHERE any(k IN keys(n) WHERE toLower(toString(n[k])) CONTAINS toLower($kw))
        RETURN n, 1.0 as score
        LIMIT $limit
        """
        keyword_results = neo4j_client.run_query(keyword_query, {
            "kw": query_text,
            "limit": top_k * 2
        })
        
        # Combine and rerank results
        node_scores = {}
        
        # Add vector scores
        for result in vector_results:
            node_id = result["node"]["id"]
            node_scores[node_id] = {
                "node": result["node"],
                "vector_score": result["score"],
                "keyword_score": 0.0
            }
        
        # Add keyword scores
        for record in keyword_results:
            node_id = record["n"]["id"]
            if node_id in node_scores:
                node_scores[node_id]["keyword_score"] = record["score"]
            else:
                node_scores[node_id] = {
                    "node": record["n"],
                    "vector_score": 0.0,
                    "keyword_score": record["score"]
                }
        
        # Calculate combined scores
        combined_results = []
        for node_id, data in node_scores.items():
            combined_score = (
                vector_weight * data["vector_score"] + 
                (1 - vector_weight) * data["keyword_score"]
            )
            combined_results.append({
                "node": data["node"],
                "score": combined_score,
                "vector_score": data["vector_score"],
                "keyword_score": data["keyword_score"]
            })
        
        # Sort by combined score and return top_k
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        return combined_results[:top_k]
    
    def find_similar_nodes(
        self,
        node_id: str,
        top_k: int = 10
    ) -> List[dict]:
        """
        Find nodes similar to a given node using vector embeddings.
        
        Args:
            node_id: ID of the node to find similar nodes for
            top_k: Number of similar nodes to return
            
        Returns:
            List of similar nodes with their similarity scores
        """
        # First get the node and its embedding
        result = neo4j_client.run_query("MATCH (n {id: $id}) RETURN n, labels(n) as labels", {"id": node_id})
        
        if not result:
            return []
        
        node = result[0]["n"]
        labels = result[0]["labels"]
        
        if not labels or "embedding" not in node:
            return []
        
        node_label = labels[0]
        embedding = node["embedding"]
        
        # Search for similar nodes
        query = f"""
        CALL db.index.vector.queryNodes('{node_label.lower()}_embedding_index', $top_k, $query_vector)
        YIELD node, score
        WHERE node.id <> $node_id
        RETURN node, score
        ORDER BY score DESC
        """
        
        results = neo4j_client.run_query(query, {
            "query_vector": embedding,
            "top_k": top_k + 1,  # +1 to account for filtering out the query node
            "node_id": node_id
        })
        
        return [
            {
                "node": record["node"],
                "score": record["score"]
            }
            for record in results
        ]
