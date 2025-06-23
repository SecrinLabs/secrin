from .chroma import ChromaVectorStore
from .base import VectorStore

def get_vectorstore(store_type: str, **kwargs) -> VectorStore:
    if store_type.lower() == "chroma":
        return ChromaVectorStore(**kwargs)
    else:
        raise ValueError(f"Unsupported vectorstore type: {store_type}")
