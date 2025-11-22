from typing import List, Optional
import numpy as np
from packages.memory.models.embedding_provider import EmbeddingProvider
from packages.memory.strategies.base_embedding_strategy import BaseEmbeddingStrategy
from packages.memory.factories.embedding_factory import EmbeddingStrategyFactory
from packages.config.settings import Settings

settings = Settings()


class EmbeddingService:
    """
    Service for generating vector embeddings.
    Uses Strategy pattern to support multiple embedding providers.
    """
    
    def __init__(
        self, 
        provider: EmbeddingProvider = EmbeddingProvider.OLLAMA,
        model: Optional[str] = None
    ):
        """
        Initialize the embedding service.
        
        Args:
            provider: The embedding provider to use
            model: Optional model name (uses default if not provided)
        """
        self.provider = provider
        self.model = model
        self._strategy: BaseEmbeddingStrategy = EmbeddingStrategyFactory.create_strategy(
            provider, model
        )
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        return self._strategy.embed_text(text)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        return self._strategy.embed_texts(texts)
    
    def get_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        
        Returns:
            Dimension size
        """
        return self._strategy.get_dimension()
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0 to 1)
        """
        a = np.array(vec1)
        b = np.array(vec2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# Singleton pattern for embedding services
_embedding_services = {}


def get_embedding_service(
    provider: EmbeddingProvider = EmbeddingProvider.OLLAMA
) -> EmbeddingService:
    """
    Get or create a singleton embedding service instance.
    
    Args:
        provider: The embedding provider to use
        
    Returns:
        EmbeddingService instance
    """
    if provider not in _embedding_services:
        _embedding_services[provider] = EmbeddingService(provider=provider)
    
    return _embedding_services[provider]


def create_embedding_for_node(node_type: str, node_data: dict) -> str:
    """
    Create a text representation for embedding based on node type.
    
    Args:
        node_type: Type of the node (e.g., 'Function', 'Class', 'File')
        node_data: Dictionary containing node properties
        
    Returns:
        Text representation suitable for embedding
    """
    if node_type == "Function":
        signature = node_data.get("signature", "")
        name = node_data.get("name", "")
        snippet = node_data.get("snippet", "")
        return f"Function: {name}\nSignature: {signature}\nCode:\n{snippet}"
    
    elif node_type == "Class":
        name = node_data.get("name", "")
        snippet = node_data.get("snippet", "")
        return f"Class: {name}\nCode:\n{snippet}"
    
    elif node_type == "File":
        path = node_data.get("path", "")
        language = node_data.get("language", "")
        return f"File: {path}\nLanguage: {language}"
    
    elif node_type == "Doc":
        doc_type = node_data.get("type", "")
        text = node_data.get("text", "")
        return f"Documentation ({doc_type}):\n{text}"
    
    elif node_type == "Module":
        name = node_data.get("name", "")
        package = node_data.get("package", "")
        return f"Module: {name}\nPackage: {package}"
    
    elif node_type == "Commit":
        message = node_data.get("message", "")
        author = node_data.get("author", "")
        return f"Commit by {author}:\n{message}"
    
    else:
        # Generic fallback
        return str(node_data.get("name", "") or node_data.get("id", ""))
