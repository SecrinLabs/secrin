"""
Unified LLM client for Secrin.

Routes completion and embedding calls to:
  - Ollama    (local, default)
  - OpenAI    (cloud)
  - Anthropic (cloud; embeddings fall back to Ollama)

Construction
------------
    # From environment / .env:
    client = client_from_settings(Settings())

    # From .secrin.yml + secrets supplied separately:
    yml    = secrin_yml.load(cwd)
    client = client_from_yml(yml, api_key="sk-...")

API
---
    text   = client.complete(prompt)
    vector = client.embed(text)
    ok     = client.ping_llm()
    ok     = client.ping_embed()

Note on embeddings for Anthropic
---------------------------------
Anthropic does not expose an embeddings API.  When provider="anthropic",
embed() uses Ollama (base_url + embed_model).  Ensure Ollama is running
and embed_model is set to a local embedding model (e.g. nomic-embed-text).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import requests

from packages.config.settings import Settings
from packages.cli.core.secrin_yml import SecrinYml

# ---------------------------------------------------------------------------
# Default models
# ---------------------------------------------------------------------------

_DEFAULT_MODELS: dict[str, str] = {
    "ollama":    "llama3",
    "openai":    "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
}

_DEFAULT_EMBED_MODELS: dict[str, str] = {
    "ollama":    "nomic-embed-text",
    "openai":    "text-embedding-3-small",
    "anthropic": "nomic-embed-text",  # via Ollama
}


# ---------------------------------------------------------------------------
# LLMClient
# ---------------------------------------------------------------------------

@dataclass
class LLMClient:
    """
    Unified interface for LLM completions and text embeddings.

    Attributes
    ----------
    provider    : "ollama" | "openai" | "anthropic"
    model       : Completion model name.
    embed_model : Embedding model name.
    base_url    : Ollama base URL (used for ollama completions + embeddings
                  and as the embedding back-end for Anthropic).
    api_key     : API key for OpenAI / Anthropic (empty for Ollama).
    timeout     : HTTP timeout in seconds for completion calls. 0 = no timeout.
    """

    provider:    str
    model:       str
    embed_model: str
    base_url:    str  = "http://localhost:11434"
    api_key:     str  = ""
    timeout:     int  = 120

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def complete(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.2,
    ) -> str:
        """Generate a completion. Returns the response text (stripped)."""
        if self.provider == "ollama":
            return self._ollama_complete(prompt, max_tokens, temperature)
        elif self.provider == "openai":
            return self._openai_complete(prompt, max_tokens, temperature)
        elif self.provider == "anthropic":
            return self._anthropic_complete(prompt, max_tokens, temperature)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider!r}")

    def embed(self, text: str) -> list[float]:
        """
        Generate an embedding vector.

        OpenAI provider → OpenAI embeddings API.
        Ollama / Anthropic → Ollama embeddings API (base_url).
        """
        if self.provider == "openai":
            return self._openai_embed(text)
        else:
            return self._ollama_embed(text)

    def ping_llm(self) -> bool:
        """Return True if the completion endpoint responds successfully."""
        try:
            self.complete("Say ok", max_tokens=5)
            return True
        except Exception:
            return False

    def ping_embed(self) -> bool:
        """Return True if the embedding endpoint responds successfully."""
        try:
            vec = self.embed("test")
            return isinstance(vec, list) and len(vec) > 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Ollama
    # ------------------------------------------------------------------

    def _ollama_complete(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> str:
        url = f"{self.base_url.rstrip('/')}/api/chat"
        resp = requests.post(
            url,
            json={
                "model":   self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream":  False,
                "options": {"num_predict": max_tokens, "temperature": temperature},
            },
            timeout=self.timeout or None,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()

    def _ollama_embed(self, text: str) -> list[float]:
        url = f"{self.base_url.rstrip('/')}/api/embeddings"
        resp = requests.post(
            url,
            json={"model": self.embed_model, "prompt": text},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------

    def _openai_complete(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> str:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model":       self.model,
                "messages":    [{"role": "user", "content": prompt}],
                "max_tokens":  max_tokens,
                "temperature": temperature,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    def _openai_embed(self, text: str) -> list[float]:
        resp = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.embed_model, "input": text},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]

    # ------------------------------------------------------------------
    # Anthropic
    # ------------------------------------------------------------------

    def _anthropic_complete(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> str:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":       self.model,
                "max_tokens":  max_tokens,
                "temperature": temperature,
                "messages":    [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def _api_key_from_env(provider: str) -> str:
    """Read the API key from environment for cloud providers."""
    env_map = {
        "openai":    "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    var = env_map.get(provider.lower(), "")
    return os.environ.get(var, "") if var else ""


def client_from_settings(settings: Settings) -> LLMClient:
    """
    Build an LLMClient from pydantic Settings (env / .env).

    Reads:
        LLM_PROVIDER       → provider
        LLM_MODEL_OLLAMA   → model (ollama)
        LLM_MODEL_OPENAI   → model (openai)
        LLM_MODEL_ANTHROPIC→ model (anthropic)
        OLLAMA_BASE_URL    → base_url
        OLLAMA_EMBEDDING_MODEL → embed_model (ollama + anthropic)
        OPENAI_EMBEDDING_MODEL → embed_model (openai)
        OPENAI_API_KEY / ANTHROPIC_API_KEY → api_key
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "ollama":
        return LLMClient(
            provider    = "ollama",
            model       = settings.LLM_MODEL_OLLAMA,
            embed_model = settings.OLLAMA_EMBEDDING_MODEL,
            base_url    = settings.OLLAMA_BASE_URL,
            timeout     = settings.LLM_TIMEOUT,
        )
    elif provider == "openai":
        return LLMClient(
            provider    = "openai",
            model       = settings.LLM_MODEL_OPENAI,
            embed_model = settings.OPENAI_EMBEDDING_MODEL,
            api_key     = settings.OPENAI_API_KEY,
            timeout     = settings.LLM_TIMEOUT,
        )
    elif provider == "anthropic":
        return LLMClient(
            provider    = "anthropic",
            model       = settings.LLM_MODEL_ANTHROPIC,
            embed_model = settings.OLLAMA_EMBEDDING_MODEL,   # embed via Ollama
            base_url    = settings.OLLAMA_BASE_URL,
            api_key     = settings.ANTHROPIC_API_KEY,
            timeout     = settings.LLM_TIMEOUT,
        )
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER {provider!r}. "
            "Supported values: ollama, openai, anthropic"
        )


def client_from_yml(yml: SecrinYml, api_key: str = "") -> LLMClient:
    """
    Build an LLMClient from a SecrinYml config.

    api_key is required for openai and anthropic.  If not provided it is
    read from the matching environment variable (OPENAI_API_KEY /
    ANTHROPIC_API_KEY).
    """
    provider = yml.provider.lower()
    resolved_key = api_key or _api_key_from_env(provider)

    return LLMClient(
        provider    = provider,
        model       = yml.model or _DEFAULT_MODELS.get(provider, ""),
        embed_model = yml.embed_model or _DEFAULT_EMBED_MODELS.get(provider, ""),
        base_url    = yml.base_url,
        api_key     = resolved_key,
    )
