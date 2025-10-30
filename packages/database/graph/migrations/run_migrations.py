from pathlib import Path
from neo4j import GraphDatabase
from typing import LiteralString, cast

from packages.config.settings import Settings

def get_applied_migrations(session):
    """Return a set of filenames that have already been applied."""
    result = session.run("MATCH (m:Migration) RETURN m.filename AS filename")
    return {record["filename"] for record in result}

def mark_migration_applied(session, filename):
    """Create a Migration node marking this file as applied."""
    session.run("""
        MERGE (m:Migration {filename: $filename})
        ON CREATE SET m.applied_at = timestamp()
    """, {"filename": filename})

def run_migrations():
    settings = Settings()
    driver = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASS)
    )

    migrations_dir = Path(__file__).parent
    cypher_files = sorted(migrations_dir.glob("*.cypher"))
    
    with driver.session() as session:
        applied = get_applied_migrations(session)

        for file_path in cypher_files:
            filename = file_path.name
            if filename in applied:
                print(f"⚪ Skipping {filename} (already applied)")
                continue

            print(f"🚀 Applying {filename}...")
            cypher = file_path.read_text()

            for statement in cypher.split(";"):
                stmt = statement.strip()
                if stmt:
                    session.run(cast(LiteralString, stmt))
            
            mark_migration_applied(session, filename)
            print(f"✅ Applied {filename}")

    driver.close()

if __name__ == "__main__":
    run_migrations()
    print("🎉 All pending Neo4j migrations applied successfully!")
