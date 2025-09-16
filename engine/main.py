"""
Main module for the Devsecrin RAG system.

This module provides the main entry points for creating and using
the Devsecrin RAG system with a clean, simple structure.
"""
from .retriever.factory import get_vectorstore
from config import settings
from engine.ingest.builder import EmbeddingBuilder
from engine.embeddings.factory import get_store

config = settings

def run_embedder_v2():
    store = get_store()
    embedder = store.getEmbedder()
    vectorstore = get_vectorstore("chroma", collection_name=config.CHROMA_COLLECTION_NAME)
    llm = store.getLlm()
    embedderV2 = EmbeddingBuilder(embedder, vectorstore, llm)
    embedderV2.embed_github_commits()