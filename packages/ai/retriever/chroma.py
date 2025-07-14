import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
from .base import VectorStore
from packages.config import get_config

config = get_config()

class ChromaVectorStore(VectorStore):
    def __init__(self, collection_name=None, db_path=None):
        # Use config defaults if not provided
        if collection_name is None:
            collection_name = config.chroma_collection_name
        if db_path is None:
            db_path = config.chroma_persist_directory
            
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection_name = collection_name

        existing = self.client.list_collections()
        if any(col.name == collection_name for col in existing):
            self.collection = self.client.get_collection(name=collection_name)
        else:
            self.collection = self.client.create_collection(name=collection_name)

    def add_document(
        self,
        doc_id: str,
        embedding: List[float],
        document: str,
        metadata: Optional[Dict] = None
    ) -> None:
        self.collection.add(
            ids=[doc_id],
            embeddings=embedding,
            documents=[document],
            metadatas=[metadata or {}]
        )

    def query(
        self,
        embedding: List[float],
        n_results: int = 5
    ) -> List[str]:
        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )
        return [doc for sublist in result["documents"] for doc in sublist]

    def document_exists(self, doc_id: str) -> bool:
        try:
            result = self.collection.get(ids=[doc_id])
            return bool(result["ids"])
        except Exception:
            return False
