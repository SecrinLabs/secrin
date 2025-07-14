from packages.ai.newindex import get_embedder, get_vectorstore, GraphBasedRAG, create_chatbot

embedder = get_embedder("ollama")
vectorstore = get_vectorstore("chroma", collection_name="docs")
graph_rag = GraphBasedRAG(embedder, vectorstore)
graph_rag.build_knowledge_graph()

create_chatbot(embedder, vectorstore)