"""
Ollama LLM provider implementation.
"""

import requests
from typing import List, Any, Optional
from packages.memory.llm.base import BaseLLMProvider
from packages.config.settings import Settings


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider for local model inference."""
    
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize Ollama provider.
        
        Args:
            model: Model name (defaults to config)
            temperature: Sampling temperature (defaults to config)
            max_tokens: Max response tokens (defaults to config)
            base_url: Ollama server URL (defaults to config)
            timeout: Request timeout in seconds (defaults to config)
        """
        settings = Settings()
        
        # Use provided values or fall back to config
        model = model or settings.LLM_MODEL_OLLAMA
        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens)
        
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.timeout = timeout or settings.LLM_TIMEOUT
        self._validate_connection()
    
    def _validate_connection(self) -> None:
        """Validate connection to Ollama server."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
        except Exception as e:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Ensure Ollama is running: 'ollama serve'. Error: {e}"
            )
    
    def generate_answer(
        self,
        question: str,
        context_items: List[Any],
        search_type: str
    ) -> str:
        """
        Generate answer using Ollama.
        
        Args:
            question: User's question
            context_items: Search results as context
            search_type: Type of search performed
        
        Returns:
            Generated answer
        
        Raises:
            Exception: If generation fails
        """
        prompt = self._build_prompt(question, context_items, search_type)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.Timeout:
            raise TimeoutError(
                f"Ollama request timed out after {self.timeout}s. "
                "Try increasing LLM_TIMEOUT or reducing context size."
            )
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API error: {e}")
    
    def get_provider_name(self) -> str:
        """Return provider name."""
        return "ollama"
    
    def is_available(self) -> bool:
        """
        Check if Ollama is available.
        
        Returns:
            True if server is reachable, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models on Ollama server.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            raise Exception(f"Failed to list Ollama models: {e}")
