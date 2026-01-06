"""
LLM service factory for creating configured LLM clients.

Supports multiple providers:
- OpenAI (and OpenAI-compatible APIs like LiteLLM)
- Google Gemini (native support via google-genai)

Provider is auto-detected based on model name prefix:
- "gemini-*" -> Uses Google Gemini
- Everything else -> Uses OpenAI-compatible API
"""

from typing import Optional, Union, Any
import os

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModelSettings
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.models.gemini import GeminiModelSettings
from pydantic_ai.models.fallback import FallbackModel
from openai import OpenAI
from google import genai  # type: ignore[attr-defined]
from google.genai import types  # type: ignore[import-untyped]

from packages.config import WikiConfig
from packages.config.settings import Settings


def is_gemini_model(model_name: str) -> bool:
    """Check if the model is a Gemini model based on naming convention."""
    return model_name.lower().startswith("gemini")


def get_gemini_api_key() -> str:
    """Get Gemini API key from settings."""
    settings = Settings()
    return settings.GEMINI_API_KEY


def create_gemini_model(model_name: str, api_key: Optional[str] = None) -> GeminiModel:
    """
    Create a Gemini model for pydantic-ai.
    
    Args:
        model_name: Gemini model name (e.g., "gemini-2.0-flash", "gemini-1.5-pro")
        api_key: Optional API key (falls back to GEMINI_API_KEY env var)
        
    Returns:
        Configured GeminiModel instance
    """
    key = api_key or get_gemini_api_key()
    return GeminiModel(
        model_name=model_name,
        provider=GoogleGLAProvider(api_key=key),
    )


def create_openai_model(model_name: str, config: WikiConfig) -> OpenAIModel:
    """Create an OpenAI-compatible model."""
    return OpenAIModel(
        model_name=model_name,
        provider=OpenAIProvider(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key
        ),
    )


def create_main_model(config: WikiConfig) -> Union[OpenAIModel, GeminiModel]:
    """Create the main LLM model from configuration."""
    if is_gemini_model(config.main_model):
        return create_gemini_model(config.main_model)
    return create_openai_model(config.main_model, config)


def create_fallback_model(config: WikiConfig) -> Union[OpenAIModel, GeminiModel]:
    """Create the fallback LLM model from configuration."""
    if is_gemini_model(config.fallback_model):
        return create_gemini_model(config.fallback_model)
    return create_openai_model(config.fallback_model, config)


def create_model_by_name(
    model_name: str, 
    config: WikiConfig
) -> Union[OpenAIModel, GeminiModel]:
    """
    Create a model instance based on model name.
    
    Auto-detects provider based on model name prefix.
    """
    if is_gemini_model(model_name):
        return create_gemini_model(model_name)
    return create_openai_model(model_name, config)


def create_fallback_models(config: WikiConfig) -> FallbackModel:
    """Create fallback models chain from configuration."""
    main = create_main_model(config)
    fallback = create_fallback_model(config)
    return FallbackModel(main, fallback)


def create_openai_client(config: WikiConfig) -> OpenAI:
    """Create OpenAI client from configuration."""
    return OpenAI(
        base_url=config.llm_base_url,
        api_key=config.llm_api_key
    )


def create_gemini_client(model_name: str = "gemini-2.0-flash", api_key: Optional[str] = None) -> genai.Client:
    """
    Create a native Gemini client.
    
    Args:
        model_name: Gemini model name to use
        api_key: Optional API key (falls back to GEMINI_API_KEY)
        
    Returns:
        Configured genai.Client instance
    """
    key = api_key or get_gemini_api_key()
    return genai.Client(api_key=key)


def call_llm(
    prompt: str,
    config: WikiConfig,
    model: Optional[str] = None,
    temperature: float = 0.0
) -> str:
    """
    Call LLM with the given prompt.
    
    Auto-detects provider based on model name:
    - gemini-* models use Google Gemini API
    - Other models use OpenAI-compatible API
    
    Args:
        prompt: The prompt to send
        config: Configuration containing LLM settings
        model: Model name (defaults to config.main_model)
        temperature: Temperature setting
        
    Returns:
        LLM response text
    """
    if model is None:
        model = config.main_model
    
    if is_gemini_model(model):
        return _call_gemini(prompt, model, temperature)
    else:
        return _call_openai(prompt, config, model, temperature)


def _call_gemini(
    prompt: str,
    model: str,
    temperature: float = 0.0
) -> str:
    """Call Gemini API directly using the new google-genai SDK."""
    api_key = get_gemini_api_key()
    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=32768,
        )
    )
    
    return response.text or ""


def _call_openai(
    prompt: str,
    config: WikiConfig,
    model: str,
    temperature: float = 0.0
) -> str:
    """Call OpenAI-compatible API."""
    client = create_openai_client(config)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=32768
    )
    return response.choices[0].message.content or ""