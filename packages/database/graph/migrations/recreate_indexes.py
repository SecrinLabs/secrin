"""
Drop and recreate vector indexes with correct dimensions.
"""

from packages.database.graph.graph import neo4j_client


def drop_vector_indexes():
    """Drop all existing vector indexes."""
    
    print("\n🗑️  Dropping existing vector indexes...")
    
    indexes = [
        "function_embedding_index",
        "class_embedding_index",
        "file_embedding_index",
        "doc_embedding_index",
        "module_embedding_index",
        "commit_embedding_index"
    ]
    
    for idx_name in indexes:
        try:
            neo4j_client.run_query(f"DROP INDEX {idx_name} IF EXISTS")
            print(f"✅ Dropped {idx_name}")
        except Exception as e:
            print(f"⚠️  Could not drop {idx_name}: {e}")
    
    print("\n✅ All indexes dropped\n")


def create_vector_indexes():
    """Create vector indexes with 1024 dimensions for mxbai-embed-large."""
    
    print("🚀 Creating vector indexes with 1024 dimensions...")
    
    statements = [
        """
        CREATE VECTOR INDEX function_embedding_index IF NOT EXISTS
        FOR (f:Function)
        ON f.embedding
        OPTIONS {indexConfig: {
          `vector.dimensions`: 1024,
          `vector.similarity_function`: 'cosine'
        }}
        """,
        """
        CREATE VECTOR INDEX class_embedding_index IF NOT EXISTS
        FOR (c:Class)
        ON c.embedding
        OPTIONS {indexConfig: {
          `vector.dimensions`: 1024,
          `vector.similarity_function`: 'cosine'
        }}
        """,
        """
        CREATE VECTOR INDEX file_embedding_index IF NOT EXISTS
        FOR (f:File)
        ON f.embedding
        OPTIONS {indexConfig: {
          `vector.dimensions`: 1024,
          `vector.similarity_function`: 'cosine'
        }}
        """,
        """
        CREATE VECTOR INDEX doc_embedding_index IF NOT EXISTS
        FOR (d:Doc)
        ON d.embedding
        OPTIONS {indexConfig: {
          `vector.dimensions`: 1024,
          `vector.similarity_function`: 'cosine'
        }}
        """,
        """
        CREATE VECTOR INDEX module_embedding_index IF NOT EXISTS
        FOR (m:Module)
        ON m.embedding
        OPTIONS {indexConfig: {
          `vector.dimensions`: 1024,
          `vector.similarity_function`: 'cosine'
        }}
        """,
        """
        CREATE VECTOR INDEX commit_embedding_index IF NOT EXISTS
        FOR (c:Commit)
        ON c.embedding
        OPTIONS {indexConfig: {
          `vector.dimensions`: 1024,
          `vector.similarity_function`: 'cosine'
        }}
        """
    ]
    
    for idx, statement in enumerate(statements, 1):
        try:
            neo4j_client.run_query(statement.strip())
            print(f"✅ Created index {idx}/6")
        except Exception as e:
            print(f"❌ Error creating index {idx}/6: {e}")
    
    print("\n✅ Vector indexes created with 1024 dimensions!\n")


if __name__ == "__main__":
    drop_vector_indexes()
    create_vector_indexes()
    
    # Verify
    print("📊 Verifying indexes...")
    try:
        results = neo4j_client.run_query("""
            SHOW INDEXES
            YIELD name, type, labelsOrTypes, properties, options
            WHERE type = 'VECTOR'
            RETURN name, options
        """)
        
        for record in results:
            name = record['name']
            options = record.get('options', {})
            if isinstance(options, dict):
                index_config = options.get('indexConfig', {})
                dimension = index_config.get('vector.dimensions', 'N/A')
                print(f"✅ {name}: {dimension} dimensions")
    except Exception as e:
        print(f"Error verifying: {e}")
