"""Base embedding strategy interface."""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingStrategy(ABC):
    """Abstract base class for embedding strategies."""
    
    def __init__(self, model: str):
        """
        Initialize the embedding strategy.
        
        Args:
            model: The model name/identifier to use
        """
        self.model = model
        self._client = None
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the embedding client/model."""
        pass
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        pass
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        
        Returns:
            Dimension size
        """
        pass
    
    def validate_text(self, text: str) -> None:
        """
        Validate text input.
        
        Args:
            text: Text to validate
            
        Raises:
            ValueError: If text is empty or invalid
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
    
    def validate_texts(self, texts: List[str]) -> List[str]:
        """
        Validate and filter texts.
        
        Args:
            texts: List of texts to validate
            
        Returns:
            List of valid texts
            
        Raises:
            ValueError: If all texts are invalid
        """
        if not texts:
            return []
        
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("All texts are empty")
        
        return valid_texts
