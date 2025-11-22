from enum import Enum


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""
    
    OPENAI = "openai"
    OLLAMA = "ollama"
    SENTENCE_TRANSFORMER = "sentence_transformer"
