"""
Factory for creating LLM provider instances.
Uses configuration to determine which provider to instantiate.
"""

from typing import Optional
from packages.memory.llm.base import BaseLLMProvider
from packages.memory.llm.providers.ollama import OllamaProvider
from packages.config import Settings


class LLMProviderFactory:
    """Factory for creating LLM providers based on configuration."""
    
    _instance: Optional[BaseLLMProvider] = None
    
    @classmethod
    def create_provider(
        cls,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider: Provider name (defaults to config LLM_PROVIDER)
            model: Model name (defaults to provider-specific config)
            temperature: Sampling temperature (defaults to config)
            max_tokens: Max tokens (defaults to config)
        
        Returns:
            Configured LLM provider instance
        
        Raises:
            ValueError: If provider is unsupported
            ConnectionError: If provider is unavailable
        """
        settings = Settings()
        provider = provider or settings.LLM_PROVIDER
        
        if provider.lower() == "ollama":
            return OllamaProvider(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Currently supported: ['ollama']"
            )
    
    @classmethod
    def get_or_create_provider(
        cls,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> BaseLLMProvider:
        """
        Get cached provider or create new one (singleton pattern).
        
        Args:
            provider: Provider name
            model: Model name
            temperature: Sampling temperature
            max_tokens: Max tokens
        
        Returns:
            Cached or new provider instance
        """
        if cls._instance is None:
            cls._instance = cls.create_provider(
                provider=provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset cached provider instance."""
        cls._instance = None


def create_llm_provider(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> BaseLLMProvider:
    """
    Convenience function to create an LLM provider.
    
    Args:
        provider: Provider name (defaults to config)
        model: Model name (defaults to config)
        temperature: Sampling temperature (defaults to config)
        max_tokens: Max tokens (defaults to config)
    
    Returns:
        Configured LLM provider
    """
    return LLMProviderFactory.create_provider(
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
