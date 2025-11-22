"""Ollama embedding strategy."""

from typing import List, Optional
import requests
from packages.memory.strategies.base_embedding_strategy import BaseEmbeddingStrategy
from packages.config.settings import Settings

settings = Settings()


class OllamaEmbeddingStrategy(BaseEmbeddingStrategy):
    """Strategy for Ollama embeddings."""
    
    def __init__(self, model: Optional[str] = None):
        """Initialize Ollama strategy."""
        model = model or settings.OLLAMA_EMBEDDING_MODEL
        super().__init__(model)
        self.base_url = settings.OLLAMA_BASE_URL
    
    def initialize(self) -> None:
        """Ollama doesn't need initialization - uses HTTP API directly."""
        pass
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text using Ollama."""
        self.validate_text(text)
        return self.embed_texts([text])[0]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using Ollama."""
        valid_texts = self.validate_texts(texts)
        
        embeddings = []
        for text in valid_texts:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            if response.status_code == 200:
                embeddings.append(response.json()["embedding"])
            else:
                raise Exception(
                    f"Ollama API error: {response.status_code} - {response.text}"
                )
        
        return embeddings
    
    def get_dimension(self) -> int:
        """Get Ollama embedding dimension from settings."""
        return settings.EMBEDDING_DIMENSION
