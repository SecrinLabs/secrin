from semantic.EmbeddingStore import EmbeddingStore
from langchain_chroma import Chroma

from config import settings

class VectorStore:
    def __init__(self, collection_name: str) -> None:
        self.collection_name = collection_name
        self.embedding = EmbeddingStore().get_embedding()

    def get_vector_store(self):
        return Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding,
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
        )
