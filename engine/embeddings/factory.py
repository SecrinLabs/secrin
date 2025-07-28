from .store.ollama import OllamaEmbedder
from .store.gemini import GeminiEmbedder
from .base import Embedder

def get_embedder(name: str) -> Embedder:
    if name.lower() == "ollama":
        return OllamaEmbedder()
    elif name.lower() == "gemini":
        return GeminiEmbedder()
    else:
        raise ValueError(f"Unsupported embedder type: {name}")
