"""
Gemini LLM provider implementation.
"""

import requests
import json
import os
from typing import List, Any, Optional, Iterator
from packages.memory.llm.base import BaseLLMProvider
from packages.config.settings import Settings

class GeminiProvider(BaseLLMProvider):
    """Gemini provider using Google's Generative Language API."""

    def __init__(
        self,
        model: Optional[str] = "gemini-2.5-flash",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None
    ):
        settings = Settings()
        
        # 1. Configuration
        model = model or "gemini-2.5-flash"
        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens)

        # 2. Auth: Try settings first, then fallback to OS environment
        self.api_key = api_key or getattr(settings, "GOOGLE_API_KEY", None) or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is missing. Please add it to your .env file.")

    def get_provider_name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_answer(self, question: str, context_items: List[Any], search_type: str) -> str:
        """Generate answer using Gemini."""
        prompt = self._build_prompt(question, context_items, search_type)
        return self.generate_text(prompt)

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text using Gemini REST API.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        # Combine system prompt if exists (Gemini supports system_instruction but simple concatenation is robust)
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens
            }
        }

        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            # Extract text from complex Gemini JSON response
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                return ""
                
        except Exception as e:
            raise Exception(f"Gemini API Error: {str(e)}")

    def stream_text(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[str]:
        """
        Stream text using Gemini (Simplified to non-streaming for stability first).
        """
        # For the initial setup, we simply yield the full result to avoid async complexities
        yield self.generate_text(prompt, system_prompt)