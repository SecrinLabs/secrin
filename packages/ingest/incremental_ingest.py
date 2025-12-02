import logging
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, List

from packages.parser.core.repository_analyzer import RepositoryAnalyzer
from packages.parser.core.graph_ingestion import graph_ingestion_service
from packages.ingest.commit_decisions import process_repository
from packages.ingest.add_embeddings import add_embeddings_to_all_nodes
from packages.memory.embeddings import EmbeddingProvider
from packages.config.settings import Settings
from packages.parser.utils import extract_repo_info
from packages.database.graph.graph import neo4j_client
from packages.ingest.full_ingest import full_ingest

settings = Settings()
logger = logging.getLogger(__name__)

def get_changed_files(repo_path: Path, base_sha: str, head_sha: str) -> Optional[List[str]]:
    """Get list of changed files between two commits. Returns None on error."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_sha, head_sha],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        return files
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting changed files: {e}")
        return None

def incremental_ingest(repo_url: str, branch: Optional[str] = None):
    """
    Run incremental ingestion pipeline.
    """    
    with TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        
        # Clone the repository
        try:
            subprocess.run(["git", "clone", repo_url, "."], cwd=repo_path, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e}")
            return

        if branch:
            try:
                subprocess.run(["git", "checkout", branch], cwd=repo_path, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to checkout branch {branch}: {e}")
                return
            
        # Get current HEAD SHA
        try:
            head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_path, text=True).strip()
        except subprocess.CalledProcessError:
            logger.error("Failed to get HEAD SHA")
            return
        
        # Get Repo Info
        repo_info = extract_repo_info(repo_url)
        repo_name = repo_info.get("name", "unknown")
        
        # Get last ingested SHA from Neo4j
        query = "MATCH (r:Repo {name: $name}) RETURN r.repo_sha as sha"
        result = neo4j_client.run_query(query, {"name": repo_name})
        
        last_sha = result[0]["sha"] if result and result[0]["sha"] else None
        
        if not last_sha:
            full_ingest(repo_url, branch=branch)
            return

        if last_sha == head_sha:
            return

        print(f"Found changes: {last_sha[:8]} -> {head_sha[:8]}")
        
        # 2. Identify Changed Files
        changed_files = get_changed_files(repo_path, last_sha, head_sha)
        
        if changed_files is None:
            full_ingest(repo_url, branch=branch)
            return
                    
        if not changed_files:
            logger.info("No files changed (maybe only merge commits or non-code files).")
        else:
            # 3. Parse Changed Files
            analyzer = RepositoryAnalyzer()
            
            # First, delete old data for these files
            for file_path in changed_files:
                graph_ingestion_service.delete_file_data(repo_name, file_path)
            
            # Then parse and ingest new data
            graph_data = analyzer.analyze_files(repo_path, changed_files)
            graph_ingestion_service.ingest_graph_data(graph_data)
            
        # 4. Ingest Git History (New Commits)
        print("Ingesting new commits...")
        # We limit to 50 commits to avoid re-ingesting too much history if the gap is large.
        # Ideally we'd stop at last_sha, but process_repository doesn't support that yet.
        process_repository(str(repo_path), branch=branch, max_commits=50)
        
        # 5. Update Embeddings
        print("Updating embeddings...")
        add_embeddings_to_all_nodes(
            node_types=["Function", "Class", "File", "Doc", "Module", "Commit"],
            provider=EmbeddingProvider(settings.EMBEDDING_PROVIDER)
        )
        
        # 6. Update Repo SHA
        print(f"Updating Repo SHA to {head_sha}...")
        update_query = "MATCH (r:Repo {name: $name}) SET r.repo_sha = $sha"
        neo4j_client.run_query(update_query, {"name": repo_name, "sha": head_sha})
        
        print("\n" + "="*50)
        print("✅ Incremental Ingestion Complete!")
        print("="*50)
