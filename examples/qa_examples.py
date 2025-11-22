#!/usr/bin/env python3
"""
Example usage of the Question-Answering (QA) service.
Demonstrates how to ask questions and get natural language answers about code.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from packages.memory.qa_service import QAService
from packages.memory.services.graph_service import GraphService
from packages.database.graph.graph import neo4j_client
from packages.memory.factories.llm_factory import create_llm_provider


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80 + "\n")


def print_answer(result: dict):
    """Print a formatted answer."""
    print(f"❓ Question: {result['question']}")
    print(f"\n💡 Answer:\n{result['answer']}\n")
    print(f"📊 Context Used: {result['context_count']} items")
    print(f"🔍 Search Type: {result['search_type']}")
    print(f"🤖 Model: {result['model']} ({result['provider']})")
    
    if result['context']:
        print(f"\n📝 Context Sources:")
        for idx, ctx in enumerate(result['context'], 1):
            print(f"  {idx}. {ctx['type']}: {ctx['name']}")
            if ctx.get('score'):
                print(f"     Relevance: {ctx['score']:.3f}")


def main():
    """Run QA examples."""
    print_header("Question-Answering Service Examples")
    
    # Initialize services
    print("Initializing services...")
    graph_service = GraphService(neo4j_client)
    llm_provider = create_llm_provider()  # Uses config defaults
    qa_service = QAService(graph_service, llm_provider)
    print(f"✅ Services initialized (LLM: {llm_provider.get_provider_name()}/{llm_provider.model})\n")
    
    # Example 1: Simple question about functions
    print_header("Example 1: Ask about a specific functionality")
    
    result = qa_service.ask(
        question="How does the embedding system work?",
        search_type="hybrid",
        node_type="Function",
        context_limit=5
    )
    
    print_answer(result)
    
    # Example 2: Ask about configuration
    print_header("Example 2: Ask about configuration")
    
    result = qa_service.ask(
        question="How do I configure the database connection?",
        search_type="vector",
        node_type="File",
        context_limit=3
    )
    
    print_answer(result)
    
    # Example 3: Multi-type search
    print_header("Example 3: Search across multiple types")
    
    result = qa_service.ask_multiple_types(
        question="What are the main components of the search system?",
        node_types=["Function", "Class", "File"],
        search_type="hybrid",
        context_per_type=2
    )
    
    print_answer(result)
    
    # Example 4: Ask about specific implementation
    print_header("Example 4: Ask about implementation details")
    
    result = qa_service.ask(
        question="Show me how vector search is implemented",
        search_type="hybrid",
        node_type="Function",
        context_limit=3
    )
    
    print_answer(result)
    
    print_header("Examples completed!")
    print("\n💡 Tips:")
    print("  • Use 'hybrid' search for better relevance (vector + keyword)")
    print("  • Use 'vector' search for semantic similarity")
    print("  • Adjust context_limit based on question complexity")
    print("  • Try different node_types: Function, Class, File, Commit, Doc")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
