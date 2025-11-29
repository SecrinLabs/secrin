import argparse
from pathlib import Path
from typing import Optional
from packages.parser.core.repository_analyzer import RepositoryAnalyzer
from packages.ingest.commit_decisions import process_repository
from packages.ingest.add_embeddings import add_embeddings_to_all_nodes
from packages.memory.embeddings import EmbeddingProvider
from packages.config.settings import Settings

settings = Settings()

def full_ingest(repo_path: str, branch: Optional[str] = None, max_commits: int = 100):
    """
    Run full ingestion pipeline:
    1. Parse Code (AST)
    2. Ingest Git History
    3. Generate Embeddings
    """
    print("="*50)
    print(f"🚀 Starting Full Ingestion for: {repo_path}")
    print("="*50)
    
    # 1. Parse Code
    print("\n[1/3] Parsing Codebase (AST)...")
    analyzer = RepositoryAnalyzer()
    # cleanup_after=True if it's a URL, but RepositoryAnalyzer handles that.
    # If it's a URL, RepositoryAnalyzer clones it.
    # If we want to reuse the cloned repo for commit ingestion, we might need to coordinate.
    # However, RepositoryAnalyzer cleans up by default.
    # And process_repository also clones if it's a URL.
    # This is inefficient (cloning twice) but simpler for now.
    
    graph_data = analyzer.analyze_repository(repo_path)
    print(f"✓ Code parsing complete. {len(graph_data.nodes)} nodes created.")
    
    # 2. Ingest Git History
    print("\n[2/3] Ingesting Git History...")
    # process_repository handles cloning internally too.
    commit_stats = process_repository(repo_path, branch=branch, max_commits=max_commits)
    print(f"✓ Git ingestion complete. {commit_stats['counts']['commits']} commits processed.")
    
    # 3. Generate Embeddings
    print("\n[3/3] Generating Embeddings...")
    # We need to ensure vector indexes exist first (usually handled by migrations, but let's assume they exist)
    # add_embeddings_to_all_nodes handles all node types
    add_embeddings_to_all_nodes(
        node_types=["Function", "Class", "File", "Doc", "Module", "Commit"],
        provider=EmbeddingProvider(settings.EMBEDDING_PROVIDER)
    )
    
    print("\n" + "="*50)
    print("✅ Full Ingestion Complete!")
    print("="*50)

def main():
    parser = argparse.ArgumentParser(description="Full Ingestion Pipeline")
    parser.add_argument("repo_path", help="Path or URL to repository")
    parser.add_argument("--branch", help="Branch to checkout", default=None)
    parser.add_argument("--max-commits", type=int, default=100, help="Max commits to ingest")
    
    args = parser.parse_args()
    
    full_ingest(args.repo_path, branch=args.branch, max_commits=args.max_commits)

if __name__ == "__main__":
    main()
