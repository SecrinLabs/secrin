"""
Example script demonstrating vector search capabilities in the knowledge graph.
"""

from typing import Literal
from packages.memory.graph import graph_service
from pprint import pprint


def example_semantic_search():
    """Example: Semantic search for functions"""
    print("=" * 70)
    print("Example 1: Semantic Search for Functions")
    print("=" * 70)
    
    # Search for functions related to authentication
    results = graph_service.vector_search(
        query_text="authenticate user login credentials",
        node_type="Function",
        limit=5,
    )
    
    print("\n🔍 Query: 'authenticate user login credentials'\n")
    
    for i, result in enumerate(results, 1):
        node = result.node
        score = result.score
        print(f"{i}. Function: {node.get('name', 'Unknown')}")
        print(f"   Similarity Score: {score:.4f}")
        print(f"   Signature: {node.get('signature', 'N/A')}")
        print(f"   File: {node.get('source_path', 'N/A')}")
        print()


def example_hybrid_search():
    """Example: Hybrid search combining vector and keyword matching"""
    print("=" * 70)
    print("Example 2: Hybrid Search (Vector + Keyword)")
    print("=" * 70)
    
    # Hybrid search for classes
    results = graph_service.hybrid_search(
        query_text="data validation and schema",
        node_type="Class",
        limit=5,
        vector_weight=0.7,  # 70% vector, 30% keyword
    )
    
    print("\n🔍 Query: 'data validation and schema'\n")
    
    for i, result in enumerate(results, 1):
        node = result.node
        combined_score = (result.metadata or {}).get("score", 0.0)
        
        print(f"{i}. Class: {node.get('name', 'Unknown')}")
        print(f"   Combined Score: {combined_score:.4f}")
        # Simplified output: only combined score shown
        print(f"   File: {node.get('source_path', 'N/A')}")
        print()


def example_find_similar_code():
    """Example: Find similar code to a given function"""
    print("=" * 70)
    print("Example 3: Find Similar Functions")
    print("=" * 70)
    
    # First, get a specific function (you'll need to replace with an actual ID)
    search_results = graph_service.search("run_query", node_type="Function", search_type="vector", limit=5)
    
    if not search_results:
        print("\n⚠️  No function found. Please ingest some code first.")
        return
    
    target_node = search_results[0].node
    node_id = target_node.get("id")
    
    print(f"\n📍 Finding functions similar to: {target_node.get('name', 'Unknown')}\n")
    
    # Find similar functions
    similar_results = graph_service.find_similar_nodes(node_id=node_id, node_type="Function", limit=5)
    
    for i, result in enumerate(similar_results, 1):
        node = result.node
        score = result.score
        print(f"{i}. Function: {node.get('name', 'Unknown')}")
        print(f"   Similarity Score: {score:.4f}")
        print(f"   Signature: {node.get('signature', 'N/A')}")
        print(f"   File: {node.get('source_path', 'N/A')}")
        print()


def example_search_documentation():
    """Example: Search through documentation"""
    print("=" * 70)
    print("Example 4: Search Documentation")
    print("=" * 70)
    
    # Search for documentation about specific topics
    results = graph_service.vector_search(
        query_text="how to setup and configure the database connection",
        node_type="Doc",
        limit=3,
    )
    
    print("\n🔍 Query: 'how to setup and configure the database connection'\n")
    
    for i, result in enumerate(results, 1):
        node = result.node
        score = result.score
        doc_text = node.get('text', '')
        
        print(f"{i}. Document Type: {node.get('type', 'Unknown')}")
        print(f"   Similarity Score: {score:.4f}")
        print(f"   File: {node.get('source_path', 'N/A')}")
        print(f"   Preview: {doc_text[:200]}...")
        print()


def example_search_commits():
    """Example: Search commit history semantically"""
    print("=" * 70)
    print("Example 5: Search Commit History")
    print("=" * 70)
    
    # Search for commits about specific features
    results = graph_service.vector_search(
        query_text="added authentication and security features",
        node_type="Commit",
        limit=5,
    )
    
    print("\n🔍 Query: 'added authentication and security features'\n")
    
    for i, result in enumerate(results, 1):
        node = result.node
        score = result.score
        print(f"{i}. Commit: {node.get('hash', 'Unknown')[:8]}")
        print(f"   Similarity Score: {score:.4f}")
        print(f"   Author: {node.get('author', 'Unknown')}")
        print(f"   Message: {node.get('message', 'N/A')}")
        print()


def example_multi_type_search():
    """Example: Search across multiple node types"""
    print("=" * 70)
    print("Example 6: Multi-Type Search")
    print("=" * 70)
    
    query = "graph database operations and queries"
    
    print(f"\n🔍 Query: '{query}'\n")
    
    node_types: list[Literal["Function", "Class", "File"]] = ["Function", "Class", "File"]
    
    for node_type in node_types:
        print(f"\n--- {node_type}s ---")
        results = graph_service.vector_search(
            query_text=query,
            node_type=node_type,
            limit=2,
        )
        
        for result in results:
            node = result.node
            score = result.score
            print(f"  • {node.get('name', node.get('path', 'Unknown'))} (score: {score:.4f})")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Vector Search Examples" + " " * 31 + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")
    
    examples = [
        ("Semantic Search", example_semantic_search),
        ("Hybrid Search", example_hybrid_search),
        ("Find Similar Code", example_find_similar_code),
        ("Search Documentation", example_search_documentation),
        ("Search Commits", example_search_commits),
        ("Multi-Type Search", example_multi_type_search),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n{'=' * 70}")
        print(f"Running Example {i}/{len(examples)}: {name}")
        print(f"{'=' * 70}\n")
        
        try:
            func()
        except Exception as e:
            print(f"\n⚠️  Error running example: {e}")
            print("Make sure you have:")
            print("  1. Run the vector index migration")
            print("  2. Ingested some code")
            print("  3. Added embeddings using add_embeddings.py")
            print("  4. Ollama is running (or set EMBEDDING_PROVIDER to openai/sentence_transformer)")
        
        if i < len(examples):
            print("\n" + "─" * 70 + "\n")
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
