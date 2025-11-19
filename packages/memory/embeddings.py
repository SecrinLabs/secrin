"""
Embedding service for generating and managing vector embeddings.
Supports OpenAI, Ollama, and local sentence-transformers models.
"""

from typing import List, Optional, Literal, Union, TYPE_CHECKING
from enum import Enum
import numpy as np
import requests
from packages.config.settings import Settings

if TYPE_CHECKING:
    from openai import OpenAI
    from sentence_transformers import SentenceTransformer  # type: ignore

settings = Settings()


class EmbeddingProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    SENTENCE_TRANSFORMER = "sentence_transformer"


class EmbeddingService:
    """
    Service for generating vector embeddings using OpenAI, Ollama, or sentence-transformers.
    """
    
    def __init__(
        self, 
        provider: EmbeddingProvider = EmbeddingProvider.OLLAMA,
        model: Optional[str] = None
    ):
        """
        Initialize the embedding service.
        
        Args:
            provider: The embedding provider to use (openai, ollama, or sentence_transformer)
            model: The specific model to use. If None, uses default from settings.
        """
        self.provider = provider
        self.model = model or self._get_default_model()
        self.client: Optional[Union['OpenAI', 'SentenceTransformer']] = None
        self._initialize_client()
    
    def _get_default_model(self) -> str:
        """Get the default model based on provider."""
        if self.provider == EmbeddingProvider.OPENAI:
            return settings.OPENAI_EMBEDDING_MODEL
        elif self.provider == EmbeddingProvider.OLLAMA:
            return settings.OLLAMA_EMBEDDING_MODEL
        else:
            return settings.SENTENCE_TRANSFORMER_MODEL
    
    def _initialize_client(self):
        """Initialize the appropriate client based on provider."""
        if self.provider == EmbeddingProvider.OPENAI:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        elif self.provider == EmbeddingProvider.OLLAMA:
            # Ollama doesn't need a client, we'll use requests directly
            self.client = None
        else:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self.client = SentenceTransformer(self.model)
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if self.provider == EmbeddingProvider.OPENAI:
            return self._embed_openai([text])[0]
        elif self.provider == EmbeddingProvider.OLLAMA:
            return self._embed_ollama([text])[0]
        else:
            return self._embed_sentence_transformer([text])[0]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("All texts are empty")
        
        if self.provider == EmbeddingProvider.OPENAI:
            return self._embed_openai(valid_texts)
        elif self.provider == EmbeddingProvider.OLLAMA:
            return self._embed_ollama(valid_texts)
        else:
            return self._embed_sentence_transformer(valid_texts)
    
    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        if self.client is None:
            raise RuntimeError("OpenAI client not initialized")
        from openai import OpenAI
        if not isinstance(self.client, OpenAI):
            raise RuntimeError("Client is not an OpenAI instance")
        
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        return [item.embedding for item in response.data]
    
    def _embed_ollama(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama API."""
        embeddings = []
        for text in texts:
            response = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            if response.status_code == 200:
                embeddings.append(response.json()["embedding"])
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
        return embeddings
    
    def _embed_sentence_transformer(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers."""
        if self.client is None:
            raise RuntimeError("Sentence transformer client not initialized")
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            if not isinstance(self.client, SentenceTransformer):
                raise RuntimeError("Client is not a SentenceTransformer instance")
        except ImportError:
            raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
        
        embeddings = self.client.encode(texts, convert_to_numpy=True)  # type: ignore
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        if self.provider == EmbeddingProvider.OPENAI:
            # OpenAI dimensions
            if "text-embedding-3-small" in self.model:
                return 1536
            elif "text-embedding-3-large" in self.model:
                return 3072
            elif "text-embedding-ada-002" in self.model:
                return 1536
            else:
                return 1536  # default
        elif self.provider == EmbeddingProvider.OLLAMA:
            # Get dimension from Ollama by making a test embedding
            # Common Ollama models: mxbai-embed-large (768), mxbai-embed-large (1024)
            return settings.EMBEDDING_DIMENSION
        else:
            # For sentence-transformers, we can get it from the model
            if self.client is not None:
                try:
                    from sentence_transformers import SentenceTransformer  # type: ignore
                    if isinstance(self.client, SentenceTransformer):
                        return self.client.get_sentence_embedding_dimension()  # type: ignore
                except ImportError:
                    pass
            return settings.EMBEDDING_DIMENSION  # fallback
    
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


# Global singleton instances
_openai_service: Optional[EmbeddingService] = None
_ollama_service: Optional[EmbeddingService] = None
_local_service: Optional[EmbeddingService] = None


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
    global _openai_service, _ollama_service, _local_service
    
    if provider == EmbeddingProvider.OPENAI:
        if _openai_service is None:
            _openai_service = EmbeddingService(provider=provider)
        return _openai_service
    elif provider == EmbeddingProvider.OLLAMA:
        if _ollama_service is None:
            _ollama_service = EmbeddingService(provider=provider)
        return _ollama_service
    else:
        if _local_service is None:
            _local_service = EmbeddingService(provider=provider)
        return _local_service
