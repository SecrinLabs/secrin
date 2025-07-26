from packages.ai.newindex import get_embedder, get_vectorstore, GraphBasedRAG, create_chatbot
from config import settings

config = settings

embedder = get_embedder("ollama")
vectorstore = get_vectorstore("chroma", collection_name=config.chroma_collection_name)
graph_rag = GraphBasedRAG(embedder, vectorstore)
graph_rag.build_knowledge_graph()

create_chatbot(embedder, vectorstore)