from typing import List, Optional, Dict, Any
import logging
from packages.database.graph.graph import Neo4jClient
from packages.memory.services.embedding_service import EmbeddingService, get_embedding_service
from packages.memory.models.embedding_provider import EmbeddingProvider
from packages.memory.models.search_result import SearchResult, VectorSearchResult
from packages.config.settings import Settings
from packages.config.feature_flags import is_feature_enabled, FeatureFlag

settings = Settings()
logger = logging.getLogger(__name__)


class GraphService:
    """
    Service for graph database operations with vector search capabilities.
    """
    
    def __init__(
        self,
        neo4j_client: Neo4jClient,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """
        Initialize the graph service.
        
        Args:
            neo4j_client: Neo4j database client
            embedding_service: Optional embedding service (creates default if not provided)
        """
        self.neo4j_client = neo4j_client
        self.embedding_service = embedding_service or get_embedding_service()
    
    def get_node(
        self,
        node_id: str,
        node_type: str = "Function"
    ) -> Optional[Dict[str, Any]]:
        """
        Get a node by ID and type.
        
        Args:
            node_id: Unique identifier of the node
            node_type: Type/label of the node
            
        Returns:
            Dictionary containing node properties or None if not found
        """
        query = f"""
        MATCH (n:{node_type} {{id: $node_id}})
        RETURN n
        """
        
        result = self.neo4j_client.run_query(query, {"node_id": node_id})
        
        if result and len(result) > 0:
            node = result[0].get("n")
            if node:
                # Convert Neo4j node to dictionary
                node_dict = dict(node)
                node_dict["labels"] = list(node.labels)
                return node_dict
        
        return None
    
    def vector_search(
        self,
        query_text: str,
        node_type: str = "Function",
        limit: int = 5
    ) -> List[VectorSearchResult]:
        """
        Perform vector similarity search.
        
        Args:
            query_text: Text to search for
            node_type: Type of nodes to search (Function, Class, File, etc.)
            limit: Maximum number of results
            
        Returns:
            List of VectorSearchResult objects
            
        Raises:
            RuntimeError: If vector search feature is disabled
        """
        if not is_feature_enabled(FeatureFlag.ENABLE_VECTOR_SEARCH):
            raise RuntimeError("Vector search is disabled via feature flag")
        
        # Apply configured limits
        limit = min(limit, settings.VECTOR_SEARCH_MAX_LIMIT)
        
        logger.info(f"Vector search: query='{query_text[:50]}...', node_type={node_type}, limit={limit}")
        
        # Generate embedding for query
        query_vector = self.embedding_service.embed_text(query_text)
        
        # Get vector index name (align with migration naming *_embedding_index)
        index_name = f"{node_type.lower()}_embedding_index"
        
        # Perform vector search
        cypher_query = """
        CALL db.index.vector.queryNodes($index_name, $limit, $query_vector)
        YIELD node, score
        RETURN node, score
        ORDER BY score DESC
        """
        
        results = self.neo4j_client.run_query(
            cypher_query,
            {
                "index_name": index_name,
                "limit": limit,
                "query_vector": query_vector
            }
        )
        
        # Convert results to VectorSearchResult objects
        search_results = []
        for record in results:
            node = record.get("node")
            score = record.get("score")
            
            if node:
                node_dict = dict(node)
                node_dict["labels"] = list(node.labels)
                
                search_results.append(VectorSearchResult(
                    node=node_dict,
                    score=float(score),
                    vector_score=float(score)
                ))
        
        return search_results
    
    def hybrid_search(
        self,
        query_text: str,
        node_type: str = "Function",
        limit: int = 5,
        vector_weight: float = 0.7
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining vector similarity and text search.
        
        Args:
            query_text: Text to search for
            node_type: Type of nodes to search
            limit: Maximum number of results
            vector_weight: Weight for vector score (0-1), text score weight is (1 - vector_weight)
            
        Returns:
            List of SearchResult objects
            
        Raises:
            RuntimeError: If hybrid search feature is disabled
        """
        if not is_feature_enabled(FeatureFlag.ENABLE_HYBRID_SEARCH):
            raise RuntimeError("Hybrid search is disabled via feature flag")
        
        # Apply configured limits and weights
        limit = min(limit, settings.VECTOR_SEARCH_MAX_LIMIT)
        vector_weight = vector_weight if vector_weight is not None else settings.HYBRID_SEARCH_VECTOR_WEIGHT
        
        logger.info(f"Hybrid search: query='{query_text[:50]}...', node_type={node_type}, limit={limit}, weight={vector_weight}")
        
        # Generate embedding for query
        query_vector = self.embedding_service.embed_text(query_text)
        index_name = f"{node_type.lower()}_embedding_index"
        
        # Build text search scoring based on node type
        if node_type == "Commit":
            # For commits, search in content (commit message), author_name, and files_changed
            # Don't filter, just boost score if text matches
            text_score_case = """
                CASE 
                    WHEN toLower(coalesce(node.content, '')) CONTAINS toLower($query_text) THEN 1.0
                    WHEN toLower(coalesce(node.author_name, '')) CONTAINS toLower($query_text) THEN 0.9
                    WHEN any(file IN coalesce(node.files_changed, []) WHERE toLower(file) CONTAINS toLower($query_text)) THEN 0.8
                    ELSE 0.0
                END
            """
        else:
            # For code nodes (Function, Class, etc.), search in name and signature
            text_score_case = """
                CASE 
                    WHEN toLower(coalesce(node.name, '')) CONTAINS toLower($query_text) THEN 1.0
                    WHEN toLower(coalesce(node.signature, '')) CONTAINS toLower($query_text) THEN 0.8
                    ELSE 0.0
                END
            """
        
        # Perform hybrid search with both vector and text matching
        # Note: Removed WHERE clause to allow pure vector results when text doesn't match
        cypher_query = f"""
        CALL db.index.vector.queryNodes($index_name, $limit * 2, $query_vector)
        YIELD node, score as vector_score
        WITH node, vector_score,
             {text_score_case} as text_score
        WITH node,
             ($vector_weight * vector_score + (1 - $vector_weight) * text_score) as hybrid_score
        RETURN node, hybrid_score
        ORDER BY hybrid_score DESC
        LIMIT $limit
        """
        
        results = self.neo4j_client.run_query(
            cypher_query,
            {
                "index_name": index_name,
                "limit": limit,
                "query_vector": query_vector,
                "query_text": query_text,
                "vector_weight": vector_weight
            }
        )
        
        # Convert results to SearchResult objects
        search_results = []
        for record in results:
            node = record.get("node")
            score = record.get("hybrid_score")
            
            if node:
                node_dict = dict(node)
                node_dict["labels"] = list(node.labels)
                
                search_results.append(SearchResult(
                    node=node_dict,
                    metadata={"score": float(score), "search_type": "hybrid"}
                ))
        
        return search_results
    
    def find_similar_nodes(
        self,
        node_id: str,
        node_type: str = "Function",
        limit: int = 5
    ) -> List[VectorSearchResult]:
        """
        Find nodes similar to a given node using vector similarity.
        
        Args:
            node_id: ID of the reference node
            node_type: Type of the node
            limit: Maximum number of results
            
        Returns:
            List of VectorSearchResult objects
        """
        # Get the node and its embedding
        node = self.get_node(node_id, node_type)
        
        if not node or "embedding" not in node:
            return []
        
        query_vector = node["embedding"]
        index_name = f"{node_type.lower()}_embedding_index"
        
        # Find similar nodes (excluding the query node itself)
        cypher_query = """
        CALL db.index.vector.queryNodes($index_name, $limit + 1, $query_vector)
        YIELD node, score
        WHERE node.id <> $node_id
        RETURN node, score
        ORDER BY score DESC
        LIMIT $limit
        """
        
        results = self.neo4j_client.run_query(
            cypher_query,
            {
                "index_name": index_name,
                "limit": limit,
                "query_vector": query_vector,
                "node_id": node_id
            }
        )
        
        # Convert results
        search_results = []
        for record in results:
            result_node = record.get("node")
            score = record.get("score")
            
            if result_node:
                node_dict = dict(result_node)
                node_dict["labels"] = list(result_node.labels)
                
                search_results.append(VectorSearchResult(
                    node=node_dict,
                    score=float(score),
                    vector_score=float(score)
                ))
        
        return search_results
    
    def search(
        self,
        query_text: str,
        node_type: str = "Function",
        search_type: str = "vector",
        limit: int = 5,
        **kwargs
    ) -> List[SearchResult]:
        """
        Generic search method that dispatches to specific search implementations.
        
        Args:
            query_text: Text to search for
            node_type: Type of nodes to search
            search_type: Type of search ('vector' or 'hybrid')
            limit: Maximum number of results
            **kwargs: Additional arguments passed to specific search methods
            
        Returns:
            List of SearchResult objects
        """
        if search_type == "vector":
            results = self.vector_search(query_text, node_type, limit)
            # Convert VectorSearchResult to SearchResult
            return [
                SearchResult(
                    node=r.node,
                    metadata={"score": r.score, "search_type": "vector"}
                )
                for r in results
            ]
        elif search_type == "hybrid":
            vector_weight = kwargs.get("vector_weight", 0.7)
            return self.hybrid_search(query_text, node_type, limit, vector_weight)
        else:
            raise ValueError(f"Unknown search type: {search_type}")
