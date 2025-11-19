"""
Script to add embeddings to existing nodes in the knowledge graph.
Run this after you've ingested your code to add vector embeddings.
"""

import argparse
from typing import List, Optional
from packages.database.graph.graph import neo4j_client
from packages.memory.embeddings import (
    get_embedding_service, 
    EmbeddingProvider, 
    create_embedding_for_node
)
from packages.config.settings import Settings

settings = Settings()


def get_nodes_without_embeddings(node_label: str, batch_size: int = 100) -> List[dict]:
    """Get nodes that don't have embeddings yet."""
    query = f"""
    MATCH (n:{node_label})
    WHERE n.embedding IS NULL
    RETURN n
    LIMIT $batch_size
    """
    results = neo4j_client.run_query(query, {"batch_size": batch_size})
    return [record["n"] for record in results]


def update_node_embedding(node_id: str, embedding: List[float]):
    """Update a node with its embedding."""
    query = """
    MATCH (n {id: $node_id})
    SET n.embedding = $embedding
    """
    neo4j_client.run_query(query, {
        "node_id": node_id,
        "embedding": embedding
    })


def process_nodes_batch(
    node_label: str,
    batch_size: int = 50,
    provider: EmbeddingProvider = EmbeddingProvider.OPENAI
):
    """Process a batch of nodes and add embeddings."""
    nodes = get_nodes_without_embeddings(node_label, batch_size)
    
    if not nodes:
        print(f"No more {node_label} nodes to process.")
        return 0
    
    print(f"Processing {len(nodes)} {node_label} nodes...")
    
    # Get embedding service
    embedding_service = get_embedding_service(provider)
    
    # Create text representations for all nodes
    texts = []
    node_ids = []
    
    for node in nodes:
        node_dict = dict(node)
        text = create_embedding_for_node(node_label, node_dict)
        if text and text.strip():
            texts.append(text)
            node_ids.append(node_dict["id"])
    
    if not texts:
        print(f"No valid texts found for {node_label} nodes.")
        return 0
    
    # Generate embeddings in batch
    try:
        embeddings = embedding_service.embed_texts(texts)
        
        # Update nodes with embeddings
        for node_id, embedding in zip(node_ids, embeddings):
            update_node_embedding(node_id, embedding)
        
        print(f"✓ Successfully added embeddings to {len(node_ids)} {node_label} nodes")
        return len(node_ids)
    
    except Exception as e:
        print(f"✗ Error processing {node_label} nodes: {e}")
        return 0


def add_embeddings_to_all_nodes(
    node_types: Optional[List[str]] = None,
    batch_size: int = 50,
    provider: EmbeddingProvider = EmbeddingProvider.OPENAI
):
    """
    Add embeddings to all specified node types.
    
    Args:
        node_types: List of node types to process. If None, processes all supported types.
        batch_size: Number of nodes to process at once
        provider: Embedding provider to use
    """
    if node_types is None:
        node_types = ["Function", "Class", "File", "Doc", "Module", "Commit"]
    
    print(f"Using {provider.value} embeddings")
    print(f"Embedding dimension: {settings.EMBEDDING_DIMENSION}")
    print("-" * 50)
    
    total_processed = 0
    
    for node_type in node_types:
        print(f"\n📦 Processing {node_type} nodes...")
        
        # Process all batches for this node type
        while True:
            processed = process_nodes_batch(node_type, batch_size, provider)
            total_processed += processed
            
            if processed < batch_size:
                # No more nodes to process for this type
                break
    
    print("\n" + "=" * 50)
    print(f"✓ Completed! Total nodes processed: {total_processed}")
    print("=" * 50)


def count_nodes_with_embeddings():
    """Print statistics about nodes with embeddings."""
    node_types = ["Function", "Class", "File", "Doc", "Module", "Commit"]
    
    print("\n📊 Embedding Statistics:")
    print("-" * 50)
    
    for node_type in node_types:
        total_query = f"MATCH (n:{node_type}) RETURN count(n) as total"
        with_embedding_query = f"MATCH (n:{node_type}) WHERE n.embedding IS NOT NULL RETURN count(n) as count"
        
        total_result = neo4j_client.run_query(total_query)
        with_embedding_result = neo4j_client.run_query(with_embedding_query)
        
        total = total_result[0]["total"] if total_result else 0
        with_embedding = with_embedding_result[0]["count"] if with_embedding_result else 0
        
        if total > 0:
            percentage = (with_embedding / total) * 100
            print(f"{node_type:12} : {with_embedding:5} / {total:5} ({percentage:5.1f}%)")
    
    print("-" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Add vector embeddings to nodes in the knowledge graph"
    )
    parser.add_argument(
        "--node-types",
        nargs="+",
        choices=["Function", "Class", "File", "Doc", "Module", "Commit"],
        help="Node types to process (default: all)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of nodes to process at once (default: 50)"
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "ollama", "sentence_transformer"],
        default=settings.EMBEDDING_PROVIDER,
        help="Embedding provider to use"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show embedding statistics and exit"
    )
    
    args = parser.parse_args()
    
    if args.stats:
        count_nodes_with_embeddings()
        return
    
    provider = EmbeddingProvider(args.provider)
    
    add_embeddings_to_all_nodes(
        node_types=args.node_types,
        batch_size=args.batch_size,
        provider=provider
    )
    
    # Show final statistics
    count_nodes_with_embeddings()


if __name__ == "__main__":
    main()
