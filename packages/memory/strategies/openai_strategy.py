"""OpenAI embedding strategy."""

from typing import List, Optional, TYPE_CHECKING
from packages.memory.strategies.base_embedding_strategy import BaseEmbeddingStrategy
from packages.config.settings import Settings

if TYPE_CHECKING:
    from openai import OpenAI

settings = Settings()


class OpenAIEmbeddingStrategy(BaseEmbeddingStrategy):
    """OpenAI embedding strategy using their API."""
    
    def __init__(self, model: Optional[str] = None):
        """Initialize OpenAI strategy."""
        model = model or settings.OPENAI_EMBEDDING_MODEL
        super().__init__(model)
        self._client: Optional['OpenAI'] = None
    
    def initialize(self) -> None:
        """Initialize OpenAI client."""
        from openai import OpenAI
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text using OpenAI."""
        self.validate_text(text)
        return self.embed_texts([text])[0]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI."""
        valid_texts = self.validate_texts(texts)
        
        if self._client is None:
            raise RuntimeError("OpenAI client not initialized. Call initialize() first.")
        
        response = self._client.embeddings.create(
            input=valid_texts,
            model=self.model
        )
        return [item.embedding for item in response.data]
    
    def get_dimension(self) -> int:
        """Get OpenAI embedding dimension."""
        if "text-embedding-3-small" in self.model:
            return 1536
        elif "text-embedding-3-large" in self.model:
            return 3072
        elif "text-embedding-ada-002" in self.model:
            return 1536
        else:
            return 1536  # default
