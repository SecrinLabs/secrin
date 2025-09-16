from engine.embeddings.store.gemini import GeminiStore
from engine.embeddings.store.ollama import OllamaStore
from engine.embeddings.base import BaseStore
from config import settings

def get_store() -> BaseStore:
    if settings.EMBEDDER_NAME == "gemini":
        return GeminiStore()
    elif settings.EMBEDDER_NAME == "ollama":
        return OllamaStore()
    else:
        raise ValueError(f"Unsupported embedder: {settings.EMBEDDER_NAME}")
