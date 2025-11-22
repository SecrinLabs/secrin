"""Sentence Transformer embedding strategy."""

from typing import List, Optional, TYPE_CHECKING
from packages.memory.strategies.base_embedding_strategy import BaseEmbeddingStrategy
from packages.config.settings import Settings

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer  # type: ignore

settings = Settings()


class SentenceTransformerStrategy(BaseEmbeddingStrategy):
    """Strategy for local sentence-transformers models."""
    
    def __init__(self, model: Optional[str] = None):
        """Initialize Sentence Transformer strategy."""
        model = model or settings.SENTENCE_TRANSFORMER_MODEL
        super().__init__(model)
        self._client: Optional['SentenceTransformer'] = None
    
    def initialize(self) -> None:
        """Initialize Sentence Transformer model."""
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._client = SentenceTransformer(self.model)
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text using Sentence Transformer."""
        self.validate_text(text)
        return self.embed_texts([text])[0]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using Sentence Transformer."""
        valid_texts = self.validate_texts(texts)
        
        if self._client is None:
            raise RuntimeError(
                "Sentence Transformer client not initialized. Call initialize() first."
            )
        
        embeddings = self._client.encode(valid_texts, convert_to_numpy=True)  # type: ignore
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get Sentence Transformer embedding dimension."""
        if self._client is not None:
            try:
                return self._client.get_sentence_embedding_dimension()  # type: ignore
            except Exception:
                pass
        return settings.EMBEDDING_DIMENSION  # fallback
