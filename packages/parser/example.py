"""
Example script demonstrating how to use the repository parser

This script shows how to:
1. Analyze a repository
2. Ingest the parsed data into Neo4j
3. Query the graph database
"""

import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from packages.parser import RepositoryAnalyzer, graph_ingestion_service
from packages.parser.models import FileNode, ClassNode, FunctionNode


def main():
    # You can use either:
    # 1. Local path: "/path/to/your/repository"
    # 2. GitHub URL: "https://github.com/user/repo"
    # 3. Git URL: "git@github.com:user/repo.git"
    
    repo_path = "git@github.com:supermemoryai/supermemory.git"
    # Or try a public repo:
    # repo_path = "https://github.com/psf/requests"
    
    # Initialize the analyzer
    print("Initializing repository analyzer...")
    analyzer = RepositoryAnalyzer()
    
    # Show supported languages
    print(f"Supported languages: {analyzer.get_supported_languages()}")
    
    # Analyze the repository (works with URLs too!)
    print(f"\nAnalyzing repository: {repo_path}")
    graph_data = analyzer.analyze_repository(repo_path)
    
    # Print some statistics
    print(f"\nParsed data summary:")
    print(f"  Total nodes: {len(graph_data.nodes)}")
    print(f"  Total relationships: {len(graph_data.relationships)}")
        
    files = len(graph_data.get_nodes_by_type(FileNode))
    classes = len(graph_data.get_nodes_by_type(ClassNode))
    functions = len(graph_data.get_nodes_by_type(FunctionNode))
    
    print(f"  Files: {files}")
    print(f"  Classes: {classes}")
    print(f"  Functions: {functions}")
    
    # Ingest into Neo4j
    print("\nIngesting data into Neo4j...")
    graph_ingestion_service.ingest_graph_data(graph_data)
    
    # Get stats from Neo4j
    from packages.parser.utils import is_git_url, extract_repo_info
    
    if is_git_url(repo_path):
        repo_info = extract_repo_info(repo_path)
        repo_name = repo_info['name']
    else:
        repo_name = Path(repo_path).name
    
    stats = graph_ingestion_service.get_repository_stats(repo_name)
    print(f"\nNeo4j statistics for '{repo_name}':")
    print(f"  Files: {stats['files']}")
    print(f"  Classes: {stats['classes']}")
    print(f"  Functions: {stats['functions']}")
    
    print("\nDone! You can now query the graph database using Neo4j Browser or Cypher queries.")


if __name__ == "__main__":
    main()
