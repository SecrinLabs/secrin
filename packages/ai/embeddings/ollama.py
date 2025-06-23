import ollama
from typing import List, Union
from .base import Embedder

class OllamaEmbedder(Embedder):
    def __init__(self, model: str = "mxbai-embed-large"):
        self.model = model

    def embed(self, texts: Union[str, List[str]]) -> List[float]:
        if isinstance(texts, str):
            texts = [texts]

        response = ollama.embed(model=self.model, input=texts)
        
        # Ensure only one text was passed
        if len(response["embeddings"]) != 1:
            raise ValueError(f"Expected one embedding, got {len(response['embeddings'])}")
        
        return response["embeddings"]  # Flat list: [float, float, ...]

