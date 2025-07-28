import ollama
from typing import List, Union
from ..base import Embedder

class OllamaEmbedder(Embedder):
    def __init__(self, model: str = "mxbai-embed-large"):
        self.model = model

    def embed(self, text: str) -> List[float]:
        """
        Given a string, return a list of embeddings as floats.
        """
        response = ollama.embed(model=self.model, input=[text])
        
        # Ensure only one text was passed
        if len(response["embeddings"]) != 1:
            raise ValueError(f"Expected one embedding, got {len(response['embeddings'])}")
        
        return response["embeddings"][0]  # Return the first (and only) embedding as a flat list

