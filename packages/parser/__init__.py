"""
Language-agnostic code parser for repository analysis

This package provides tools to parse code repositories using tree-sitter
and extract structured data (classes, functions, imports, etc.) for 
ingestion into a Neo4j graph database.

Main components:
- RepositoryAnalyzer: Orchestrates the parsing of an entire repository
- BaseLanguageParser: Abstract base class for language-specific parsers
- GraphIngestionService: Ingests parsed data into Neo4j
- Language-specific parsers (Python, JavaScript, etc.)

Usage:
    from packages.parser import RepositoryAnalyzer, graph_ingestion_service
    
    # Analyze a repository
    analyzer = RepositoryAnalyzer()
    graph_data = analyzer.analyze_repository("/path/to/repo")
    
    # Ingest into Neo4j
    graph_ingestion_service.ingest_graph_data(graph_data)
"""

from .core import (
    RepositoryAnalyzer,
    GraphIngestionService,
    graph_ingestion_service,
)
from .models import GraphData

__all__ = [
    "RepositoryAnalyzer",
    "GraphIngestionService",
    "graph_ingestion_service",
    "GraphData",
]

__version__ = "0.1.0"
