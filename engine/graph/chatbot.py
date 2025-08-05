"""
Chatbot interface for the graph-enhanced RAG system.
"""
import time
import os
from .rag import GraphBasedRAG
from ..llm.factory import get_llm
from config import settings

config = settings


def create_graph_chatbot(embedder, vectorstore, llm=None):
    """Create enhanced chatbot with graph-based RAG"""
    if llm is None:
        llm = get_llm(config.LLM_PROVIDER)
    
    graph_rag = GraphBasedRAG(embedder, vectorstore, llm)
    
    # Build knowledge graph
    graph_rag.build_knowledge_graph()
    
    print("\n🤖 Welcome to the Graph-Enhanced Documentation Assistant!")
    print("Ask any question about the documentation (type 'exit' to quit)")
    print("Now with enhanced context from connected issues, PRs, and commits!\n")
    
    while True:
        try:
            print("👤 You:", end=" ")
            question = input().strip()
            if question.lower() in ['exit', 'quit', 'bye']:
                print("\n🤖 Goodbye! Have a great day!")
                break
            if not question:
                print("Please ask a question!")
                continue

            print("🤖 Thinking", end="")
            for _ in range(3):
                time.sleep(0.3)
                print(".", end="", flush=True)
            print("\n")

            answer = graph_rag.query_with_graph_context(question)
            print(f"\n🤖 Assistant: {answer}")
            print("\n" + "-"*50)

        except KeyboardInterrupt:
            print("\n\n🤖 Goodbye! Have a great day!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


def rebuild_knowledge_graph():
    """Force rebuild the knowledge graph (useful when data changes)"""
    from ..embeddings.factory import get_embedder
    from ..retriever.factory import get_vectorstore
    from ..llm.factory import get_llm
    from config import settings
    
    embedder = get_embedder(settings.EMBEDDER_NAME)
    vectorstore = get_vectorstore("chroma", collection_name=settings.CHROMA_COLLECTION_NAME)
    llm = get_llm(settings.LLM_PROVIDER)
    graph_rag = GraphBasedRAG(embedder, vectorstore, llm)
    graph_rag.build_knowledge_graph(force_rebuild=True)
    print("🎉 Knowledge graph rebuilt successfully!")


def clear_knowledge_graph_cache():
    """Clear the knowledge graph cache"""
    cache_path = "./chroma_store/knowledge_graph.pkl"
    if os.path.exists(cache_path):
        os.remove(cache_path)
        print("🗑️ Knowledge graph cache cleared!")
    else:
        print("ℹ️ No cache file found to clear.")
