#!/usr/bin/env python3
"""
Command-line interface for the repository parser

Usage:
    python cli.py analyze /path/to/repo
    python cli.py analyze /path/to/repo --skip-ingest
    python cli.py stats my-repo
    python cli.py clear my-repo
    python cli.py languages
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from packages.parser import RepositoryAnalyzer, graph_ingestion_service


def analyze_command(args):
    """Analyze a repository and optionally ingest into Neo4j"""
    repo_input = args.repo_path
    
    # Check if it's a URL or local path
    from packages.parser.utils import is_git_url
    
    if is_git_url(repo_input):
        print(f"Analyzing Git repository: {repo_input}")
    else:
        repo_path = Path(repo_input).resolve()
        if not repo_path.exists():
            print(f"Error: Repository path does not exist: {repo_path}")
            sys.exit(1)
        print(f"Analyzing repository: {repo_path}")
    
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = RepositoryAnalyzer()
    
    # Analyze (works with both URLs and local paths)
    try:
        graph_data = analyzer.analyze_repository(repo_input, cleanup_after=not args.keep_clone)
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Analysis Summary")
    print("=" * 60)
    
    from packages.parser.models import (
        FileNode, ClassNode, FunctionNode, 
        VariableNode, PackageNode, DocNode
    )
    
    files = len(graph_data.get_nodes_by_type(FileNode))
    classes = len(graph_data.get_nodes_by_type(ClassNode))
    functions = len(graph_data.get_nodes_by_type(FunctionNode))
    variables = len(graph_data.get_nodes_by_type(VariableNode))
    packages = len(graph_data.get_nodes_by_type(PackageNode))
    docs = len(graph_data.get_nodes_by_type(DocNode))
    
    print(f"Nodes extracted:")
    print(f"  Files:       {files}")
    print(f"  Classes:     {classes}")
    print(f"  Functions:   {functions}")
    print(f"  Variables:   {variables}")
    print(f"  Packages:    {packages}")
    print(f"  Docs:        {docs}")
    print(f"  Total:       {len(graph_data.nodes)}")
    print(f"\nRelationships: {len(graph_data.relationships)}")
    
    # Ingest if not skipped
    if not args.skip_ingest:
        print("\n" + "=" * 60)
        print("Ingesting into Neo4j...")
        print("=" * 60)
        
        try:
            graph_ingestion_service.ingest_graph_data(graph_data)
            print("\n✓ Successfully ingested into Neo4j!")
            
            # Show stats - extract repo name from input
            from packages.parser.utils import extract_repo_info
            if is_git_url(repo_input):
                repo_info = extract_repo_info(repo_input)
                repo_name = repo_info['name']
            else:
                repo_name = Path(repo_input).name
            
            stats = graph_ingestion_service.get_repository_stats(repo_name)
            print(f"\nNeo4j statistics for '{repo_name}':")
            print(f"  Files:     {stats['files']}")
            print(f"  Classes:   {stats['classes']}")
            print(f"  Functions: {stats['functions']}")
            print(f"  Tests:     {stats['tests']}")
            print(f"  Commits:   {stats['commits']}")
            print(f"  Packages:  {stats['packages']}")
            print(f"  Docs:      {stats['docs']}")
            
        except Exception as e:
            print(f"Error during ingestion: {e}")
            sys.exit(1)
    else:
        print("\n⊘ Skipping Neo4j ingestion (--skip-ingest)")


def stats_command(args):
    """Get statistics for a repository in Neo4j"""
    repo_name = args.repo_name
    
    try:
        stats = graph_ingestion_service.get_repository_stats(repo_name)
        
        print(f"Neo4j Statistics for '{repo_name}':")
        print("=" * 60)
        print(f"Files:     {stats['files']}")
        print(f"Classes:   {stats['classes']}")
        print(f"Functions: {stats['functions']}")
        print(f"Tests:     {stats['tests']}")
        print(f"Commits:   {stats['commits']}")
        print(f"Packages:  {stats['packages']}")
        print(f"Docs:      {stats['docs']}")
        
        if all(v == 0 for v in stats.values()):
            print("\n⚠ No data found. Has this repository been analyzed?")
        
    except Exception as e:
        print(f"Error querying Neo4j: {e}")
        sys.exit(1)


def clear_command(args):
    """Clear all data for a repository from Neo4j"""
    repo_name = args.repo_name
    
    if not args.force:
        response = input(f"Are you sure you want to delete all data for '{repo_name}'? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            return
    
    try:
        graph_ingestion_service.clear_repository_data(repo_name)
        print(f"✓ Cleared all data for '{repo_name}'")
    except Exception as e:
        print(f"Error clearing data: {e}")
        sys.exit(1)


def languages_command(args):
    """List supported languages"""
    analyzer = RepositoryAnalyzer()
    languages = analyzer.get_supported_languages()
    
    print("Supported Languages:")
    print("=" * 60)
    
    for lang in sorted(languages):
        # Get file extensions for this language
        from packages.parser.utils.file_utils import LANGUAGE_EXTENSIONS
        extensions = LANGUAGE_EXTENSIONS.get(lang, [])
        ext_str = ", ".join(extensions) if extensions else "N/A"
        print(f"  {lang:<15} {ext_str}")
    
    print(f"\nTotal: {len(languages)} languages supported")


def main():
    parser = argparse.ArgumentParser(
        description="Code Repository Parser - Analyze repositories and extract graph data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a local repository
  python cli.py analyze /path/to/repo
  
  # Analyze a GitHub repository
  python cli.py analyze https://github.com/user/repo
  
  # Analyze without ingesting into Neo4j
  python cli.py analyze /path/to/repo --skip-ingest
  
  # Keep cloned repository after analysis
  python cli.py analyze https://github.com/user/repo --keep-clone
  
  # Get statistics for a repository
  python cli.py stats my-repo
  
  # Clear repository data
  python cli.py clear my-repo --force
  
  # List supported languages
  python cli.py languages
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a repository")
    analyze_parser.add_argument(
        "repo_path", 
        help="Path to the repository or Git URL (e.g., https://github.com/user/repo)"
    )
    analyze_parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip Neo4j ingestion (only analyze)"
    )
    analyze_parser.add_argument(
        "--keep-clone",
        action="store_true",
        help="Keep cloned repository after analysis (for Git URLs)"
    )
    analyze_parser.set_defaults(func=analyze_command)
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Get repository statistics from Neo4j")
    stats_parser.add_argument("repo_name", help="Name of the repository")
    stats_parser.set_defaults(func=stats_command)
    
    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear repository data from Neo4j")
    clear_parser.add_argument("repo_name", help="Name of the repository")
    clear_parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )
    clear_parser.set_defaults(func=clear_command)
    
    # Languages command
    languages_parser = subparsers.add_parser("languages", help="List supported languages")
    languages_parser.set_defaults(func=languages_command)
    
    # Parse and execute
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
