import os
from google import genai
from typing import List, Union

from ..base import Embedder

class GeminiEmbedder(Embedder):
    def __init__(self, model: str = "gemini-embedding-001"):
        self.model = model
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        self.client = genai.Client(api_key=api_key)
    
    def embed(self, text: str) -> List[float]:
        """
        Given a string, return a list of embeddings as floats.
        """
        result = self.client.models.embed_content(
            model=self.model,
            contents=[text]
        )
        
        if not result.embeddings or len(result.embeddings) == 0:
            raise ValueError("No embeddings returned from Gemini API")
        
        # Extract the values from the first (and only) embedding
        embedding_values = result.embeddings[0].values
        return list(embedding_values)
