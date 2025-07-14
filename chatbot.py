from packages.ai.newindex import get_embedder, get_vectorstore, GraphBasedRAG, create_chatbot
from packages.config import get_config

config = get_config()

embedder = get_embedder("ollama")
vectorstore = get_vectorstore("chroma", collection_name=config.chroma_collection_name)
graph_rag = GraphBasedRAG(embedder, vectorstore)
graph_rag.build_knowledge_graph()

create_chatbot(embedder, vectorstore)