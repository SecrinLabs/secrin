"""
Ollama LLM provider implementation.

Uses Ollama's REST API for local model inference with no API keys required.
"""

import logging
from typing import List, Optional

import requests

from .base import BaseLLMProvider, LLMMessage, LLMResponse


logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama LLM provider for local model inference.

    Uses Ollama's REST API to generate responses using locally-running models.
    No API key required - models run on the local machine.
    """

    DEFAULT_MODEL = "llama3"
    MODEL_ALIASES = {
        "codellama": "codellama:7b",
        "llama3": "qwen2.5-coder:0.5b",
        "mistral": "mistral:7b",
    }

    def __init__(
        self,
        api_key: str = "",
        model: str = DEFAULT_MODEL,
        base_url: str = "http://localhost:11434",
        timeout: int = 0,
    ):
        super().__init__(api_key, self._resolve_model(model))
        self.base_url = base_url.rstrip("/")
        # timeout=0 means no timeout (None for requests library)
        self.timeout = timeout if timeout > 0 else None
        self._verify_connection()

    def _resolve_model(self, model: str) -> str:
        """Resolve model alias to full model name."""
        return self.MODEL_ALIASES.get(model, model)

    def _verify_connection(self):
        """Verify that Ollama is running and accessible."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=10)
            resp.raise_for_status()
            logger.info(f"Connected to Ollama at {self.base_url}")
        except requests.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running: ollama serve"
            )
        except requests.RequestException as e:
            raise ConnectionError(
                f"Error connecting to Ollama at {self.base_url}: {e}"
            )

    @property
    def provider_name(self) -> str:
        return "ollama"

    def validate_api_key(self) -> bool:
        """No API key needed for local Ollama."""
        return True

    def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }
            if system_prompt:
                payload["system"] = system_prompt

            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            content = data.get("response", "")
            usage = None
            if "eval_count" in data or "prompt_eval_count" in data:
                usage = {
                    "input_tokens": data.get("prompt_eval_count", 0),
                    "output_tokens": data.get("eval_count", 0),
                }

            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                stop_reason=data.get("done_reason"),
            )

        except requests.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise

    def generate_chat(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        try:
            ollama_messages = []
            if system_prompt:
                ollama_messages.append({"role": "system", "content": system_prompt})

            for msg in messages:
                ollama_messages.append({"role": msg.role, "content": msg.content})

            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }

            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            content = data.get("message", {}).get("content", "")
            usage = None
            if "eval_count" in data or "prompt_eval_count" in data:
                usage = {
                    "input_tokens": data.get("prompt_eval_count", 0),
                    "output_tokens": data.get("eval_count", 0),
                }

            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                stop_reason=data.get("done_reason"),
            )

        except requests.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise
