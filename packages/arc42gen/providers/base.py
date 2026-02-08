"""
Abstract base class for LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LLMMessage:
    """Represents a message in a conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str


@dataclass
class LLMResponse:
    """Represents a response from an LLM provider."""
    content: str
    model: str
    usage: Optional[dict] = None
    stop_reason: Optional[str] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Defines the interface that all LLM providers must implement.
    This allows arc42gen to work with different LLM backends.
    """

    def __init__(self, api_key: str, model: str):
        """
        Initialize the provider.

        Args:
            api_key: API key for the provider
            model: Model identifier to use
        """
        self.api_key = api_key
        self.model = model

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            prompt: The user prompt to send
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with the generated content
        """
        pass

    @abstractmethod
    def generate_chat(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate a response from a conversation.

        Args:
            messages: List of conversation messages
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with the generated content
        """
        pass

    def validate_api_key(self) -> bool:
        """
        Validate that the API key is set.

        Returns:
            True if API key is set, False otherwise
        """
        return bool(self.api_key and self.api_key.strip())
