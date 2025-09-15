"""
Main module for the Devsecrin RAG system.

This module provides the main entry points for creating and using
the Devsecrin RAG system with a clean, simple structure.
"""
from .embeddings.factory import get_embedder
from .retriever.factory import get_vectorstore
from .llm.factory import get_llm
from .graph import GraphBasedRAG
from .graph.chatbot import create_graph_chatbot, rebuild_knowledge_graph, clear_knowledge_graph_cache
from config import settings
from engine.ingest.builder import EmbeddingBuilder

config = settings

def run_graph_generator(question):
    embedder = get_embedder(config.EMBEDDER_NAME)
    vectorstore = get_vectorstore("chroma", collection_name=config.CHROMA_COLLECTION_NAME)
    llm = get_llm(config.LLM_PROVIDER)
    graph_rag = GraphBasedRAG(embedder, vectorstore, llm)
    graph_rag.build_knowledge_graph()
    return graph_rag.query_with_graph_context(question)

def run_graph_embedder():
    embedder = get_embedder(config.EMBEDDER_NAME)
    vectorstore = get_vectorstore("chroma", collection_name=config.CHROMA_COLLECTION_NAME)
    llm = get_llm(config.LLM_PROVIDER)
    graph_rag = GraphBasedRAG(embedder, vectorstore, llm)
    graph_rag.build_knowledge_graph()

# Legacy functions for backward compatibility
def run_generator(question):
    return run_graph_generator(question)

def run_embedder():
    return run_graph_embedder()

def create_chatbot(embedder, vectorstore, llm=None):
    if llm is None:
        llm = get_llm(config.LLM_PROVIDER)
    return create_graph_chatbot(embedder, vectorstore, llm)

def run_embedder_v2():
    embedder = get_embedder(config.EMBEDDER_NAME)
    vectorstore = get_vectorstore("chroma", collection_name=config.CHROMA_COLLECTION_NAME)
    llm = get_llm(config.LLM_PROVIDER)
    embedderV2 = EmbeddingBuilder(embedder, vectorstore, llm)
    embedderV2.embed_github_commits()