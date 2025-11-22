from typing import Optional
from packages.memory.models.embedding_provider import EmbeddingProvider
from packages.memory.strategies.base_embedding_strategy import BaseEmbeddingStrategy
from packages.memory.strategies.openai_strategy import OpenAIEmbeddingStrategy
from packages.memory.strategies.ollama_strategy import OllamaEmbeddingStrategy
from packages.memory.strategies.sentence_transformer_strategy import SentenceTransformerStrategy


class EmbeddingStrategyFactory:
    """Factory for creating embedding strategies based on provider."""
    
    _strategies = {
        EmbeddingProvider.OPENAI: OpenAIEmbeddingStrategy,
        EmbeddingProvider.OLLAMA: OllamaEmbeddingStrategy,
        EmbeddingProvider.SENTENCE_TRANSFORMER: SentenceTransformerStrategy,
    }
    
    @classmethod
    def create_strategy(
        cls, 
        provider: EmbeddingProvider, 
        model: Optional[str] = None
    ) -> BaseEmbeddingStrategy:
        """
        Create an embedding strategy for the given provider.
        
        Args:
            provider: The embedding provider
            model: Optional model name (uses default if not provided)
            
        Returns:
            An instance of the appropriate strategy
            
        Raises:
            ValueError: If provider is not supported
        """
        strategy_class = cls._strategies.get(provider)
        
        if strategy_class is None:
            raise ValueError(f"Unsupported embedding provider: {provider}")
        
        strategy = strategy_class(model=model)
        strategy.initialize()
        return strategy
