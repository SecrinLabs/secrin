"""
LLM Factory for DevSecrin

This module provides a factory function to create appropriate LLM instances
based on the configuration.
"""

from .providers.ollama import OllamaLLM
from .providers.gemini import GeminiLLM
from .base import LLM


def get_llm(name: str, **kwargs) -> LLM:
    """
    Factory function to create LLM instances.
    
    Args:
        name: The name of the LLM provider ('ollama' or 'gemini')
        **kwargs: Additional configuration options to pass to the LLM
        
    Returns:
        LLM instance based on the provider name
        
    Raises:
        ValueError: If the provider name is not supported
    """
    name_lower = name.lower()
    
    if name_lower == "ollama":
        return OllamaLLM(**kwargs)
    elif name_lower == "gemini":
        return GeminiLLM(**kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: {name}. Supported providers: ollama, gemini")


def get_available_providers():
    """
    Get list of available LLM providers.
    
    Returns:
        List of supported LLM provider names
    """
    return ["ollama", "gemini"]
