from .ollama import OllamaEmbedder
from .base import Embedder

def get_embedder(name: str) -> Embedder:
    if name.lower() == "ollama":
        return OllamaEmbedder()
    else:
        raise ValueError(f"Unsupported embedder type: {name}")
