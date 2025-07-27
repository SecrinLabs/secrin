from engine.embeddings.factory import get_embedder
from engine.retriever.factory import get_vectorstore
from engine.main import GraphBasedRAG, create_chatbot
from config import settings

config = settings

embedder = get_embedder("ollama")
vectorstore = get_vectorstore("chroma", collection_name=config.CHROMA_COLLECTION_NAME)

create_chatbot(embedder, vectorstore)