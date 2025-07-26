from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class VectorStore(ABC):
    @abstractmethod
    def add_document(
        self,
        doc_id: str,
        embedding: List[float],
        document: str,
        metadata: Optional[Dict] = None
    ) -> None:
        pass

    @abstractmethod
    def query(
        self,
        embedding: List[float],
        n_results: int = 5
    ) -> List[str]:
        pass

    @abstractmethod
    def document_exists(self, doc_id: str) -> bool:
        pass
