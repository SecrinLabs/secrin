"""
Anthropic (Claude) LLM provider implementation.
"""

import logging
from typing import List, Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import BaseLLMProvider, LLMMessage, LLMResponse


logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude LLM provider.

    Uses the Anthropic API to generate responses using Claude models.
    """

    # Default model mappings
    DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
    MODEL_ALIASES = {
        "claude-sonnet": "claude-sonnet-4-5-20250929",
        "claude-opus": "claude-opus-4-20250514",
        "claude-haiku": "claude-3-5-haiku-20241022",
    }

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-sonnet-4-5-20250929)
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        super().__init__(api_key, self._resolve_model(model))
        self.client = anthropic.Anthropic(api_key=api_key)

    def _resolve_model(self, model: str) -> str:
        """Resolve model alias to full model name."""
        return self.MODEL_ALIASES.get(model, model)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate a response using Claude.

        Args:
            prompt: User prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with generated content
        """
        messages = [{"role": "user", "content": prompt}]

        try:
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": messages,
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            if temperature != 0.7:
                kwargs["temperature"] = temperature

            response = self.client.messages.create(**kwargs)

            return LLMResponse(
                content=response.content[0].text,
                model=response.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                stop_reason=response.stop_reason,
            )

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Anthropic: {e}")
            raise

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
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with generated content
        """
        # Convert to Anthropic format
        anthropic_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
            if msg.role != "system"  # System messages handled separately
        ]

        try:
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": anthropic_messages,
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            if temperature != 0.7:
                kwargs["temperature"] = temperature

            response = self.client.messages.create(**kwargs)

            return LLMResponse(
                content=response.content[0].text,
                model=response.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                stop_reason=response.stop_reason,
            )

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Anthropic: {e}")
            raise
