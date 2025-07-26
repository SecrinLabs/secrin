from abc import ABC, abstractmethod
from typing import List, Union

class Embedder(ABC):
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Given a string or list of strings, return a list of embeddings.
        Each embedding is a list of floats.
        """
        pass