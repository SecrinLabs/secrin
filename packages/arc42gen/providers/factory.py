"""
Factory function for creating LLM providers.
"""

import logging
from typing import Optional

from ..models.config import LLMConfig
from .base import BaseLLMProvider


logger = logging.getLogger(__name__)


def create_llm_provider(config: LLMConfig) -> BaseLLMProvider:
    """
    Create an LLM provider based on configuration.

    Args:
        config: LLM configuration with provider, model, and API key

    Returns:
        An instance of the appropriate LLM provider

    Raises:
        ValueError: If provider is not supported
        ImportError: If required package is not installed
    """
    provider = config.provider.lower()

    if provider == "anthropic":
        from .anthropic_provider import AnthropicProvider
        logger.info(f"Creating Anthropic provider with model: {config.model}")
        return AnthropicProvider(
            api_key=config.api_key,
            model=config.model,
        )

    elif provider == "gemini":
        from .gemini_provider import GeminiProvider
        logger.info(f"Creating Gemini provider with model: {config.model}")
        return GeminiProvider(
            api_key=config.api_key,
            model=config.model,
        )

    elif provider == "ollama":
        from .ollama_provider import OllamaProvider
        logger.info(f"Creating Ollama provider with model: {config.model}")
        return OllamaProvider(
            api_key=config.api_key,
            model=config.model,
            base_url=getattr(config, 'base_url', '') or "http://localhost:11434",
            timeout=getattr(config, 'timeout', 0),
        )

    else:
        supported = ["anthropic", "gemini", "ollama"]
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: {', '.join(supported)}"
        )


def get_default_model(provider: str) -> str:
    """
    Get the default model for a provider.

    Args:
        provider: Provider name ('anthropic' or 'gemini')

    Returns:
        Default model identifier for the provider
    """
    defaults = {
        "anthropic": "claude-sonnet-4-5-20250929",
        "gemini": "gemini-2.0-flash",
        "ollama": "llama3.2",
    }
    return defaults.get(provider.lower(), "")


def get_api_key_env_var(provider: str) -> str:
    """
    Get the environment variable name for API key.

    Args:
        provider: Provider name

    Returns:
        Environment variable name for the API key
    """
    env_vars = {
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "ollama": "OLLAMA_BASE_URL",
    }
    return env_vars.get(provider.lower(), "LLM_API_KEY")
