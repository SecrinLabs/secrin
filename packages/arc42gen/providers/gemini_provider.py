"""
Google Gemini LLM provider implementation.
"""

import logging
from typing import List, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base import BaseLLMProvider, LLMMessage, LLMResponse


logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini LLM provider.

    Uses the Google Generative AI API to generate responses using Gemini models.
    """

    # Default model mappings
    DEFAULT_MODEL = "gemini-2.0-flash"
    MODEL_ALIASES = {
        "gemini-pro": "gemini-1.5-pro",
        "gemini-flash": "gemini-2.0-flash",
        "gemini-2-flash": "gemini-2.0-flash",
        "gemini-1.5-pro": "gemini-1.5-pro",
        "gemini-1.5-flash": "gemini-1.5-flash",
    }

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key
            model: Model to use (default: gemini-2.0-flash)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        super().__init__(api_key, self._resolve_model(model))

        # Configure the API
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(self.model)

    def _resolve_model(self, model: str) -> str:
        """Resolve model alias to full model name."""
        return self.MODEL_ALIASES.get(model, model)

    @property
    def provider_name(self) -> str:
        return "gemini"

    def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate a response using Gemini.

        Args:
            prompt: User prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with generated content
        """
        try:
            # Build full prompt with system instruction if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Configure generation settings
            generation_config = genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            response = self.client.generate_content(
                full_prompt,
                generation_config=generation_config,
            )

            # Extract text from response
            content = response.text if response.text else ""

            # Get usage info if available
            usage = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = {
                    "input_tokens": response.usage_metadata.prompt_token_count,
                    "output_tokens": response.usage_metadata.candidates_token_count,
                }

            # Get stop reason
            stop_reason = None
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    stop_reason = str(candidate.finish_reason)

            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                stop_reason=stop_reason,
            )

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
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
        try:
            # Create a new model with system instruction if provided
            if system_prompt:
                model = genai.GenerativeModel(
                    self.model,
                    system_instruction=system_prompt
                )
            else:
                model = self.client

            # Start a chat session
            chat = model.start_chat(history=[])

            # Add conversation history
            for msg in messages[:-1]:  # All except the last message
                if msg.role == "user":
                    chat.send_message(msg.content)
                elif msg.role == "assistant":
                    # Simulate assistant response in history
                    chat.history.append({
                        "role": "model",
                        "parts": [msg.content]
                    })

            # Configure generation settings
            generation_config = genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            # Send the last message
            last_message = messages[-1]
            response = chat.send_message(
                last_message.content,
                generation_config=generation_config,
            )

            # Extract content
            content = response.text if response.text else ""

            # Get usage info if available
            usage = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = {
                    "input_tokens": response.usage_metadata.prompt_token_count,
                    "output_tokens": response.usage_metadata.candidates_token_count,
                }

            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
            )

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
