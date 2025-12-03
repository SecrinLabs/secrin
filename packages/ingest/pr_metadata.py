from datetime import datetime
from typing import Dict, Any, Optional
from packages.memory.memory import Memory
from packages.ingest.edges import Edge
from packages.parser.utils import extract_repo_info

def ingest_pull_request_metadata(
    pr_payload: Dict[str, Any],
    repo_payload: Dict[str, Any],
    memory: Optional[Memory] = None
) -> Dict[str, Any]:
    """
    Ingest pull request metadata into the knowledge graph.
    
    Args:
        pr_payload: The pull_request object from GitHub webhook
        repo_payload: The repository object from GitHub webhook
        memory: Optional Memory instance (creates new if not provided)
    
    Returns:
        Dictionary with created node IDs and stats
    """
    if memory is None:
        memory = Memory()
    
    # Extract repository info
    repo_url = repo_payload.get("clone_url") or repo_payload.get("html_url") or ""
    if not repo_url:
        raise ValueError("Repository URL not found in payload")
    
    repo_info = extract_repo_info(repo_url)
    repo_name = repo_info.get("name", "unknown")
    
    # Extract PR metadata
    pr_number = pr_payload.get("number")
    pr_title = pr_payload.get("title", "")
    pr_body = pr_payload.get("body", "")
    pr_state = pr_payload.get("state", "open")
    pr_merged = pr_payload.get("merged", False)
    pr_merged_at = pr_payload.get("merged_at")
    
    # Extract author info
    pr_author_data = pr_payload.get("user", {})
    pr_author = pr_author_data.get("login", "unknown")
    pr_author_email = pr_author_data.get("email", f"{pr_author}@github.com")
    
    # Extract branch info
    base_branch = pr_payload.get("base", {}).get("ref")
    head_branch = pr_payload.get("head", {}).get("ref")
    
    # Create stable PR ID
    pr_id = f"{repo_name}:pr:{pr_number}"
    
    # Build PR content for embedding
    pr_content = f"""Pull Request #{pr_number}: {pr_title}

      {pr_body}

      Author: {pr_author}
      State: {pr_state}
      Merged: {pr_merged}
      Base Branch: {base_branch}
      Head Branch: {head_branch}
      """
    
    # Upsert PR node
    pr_node_id = memory.upsert_node(
        "PullRequest",
        match_props={"pr_number": pr_number, "repo_url": repo_url},
        set_props={
            "id": pr_id,
            "pr_number": pr_number,
            "title": pr_title,
            "body": pr_body,
            "content": pr_content,
            "author": pr_author,
            "repo_url": repo_url,
            "state": pr_state,
            "merged": pr_merged,
            "merged_at": pr_merged_at,
            "base_branch": base_branch,
            "head_branch": head_branch,
        }
    )
    
    # Upsert repository node
    repo_node_id = f"repo:{repo_name}"
    memory.upsert_node(
        "Repository",
        match_props={"url": repo_url},
        set_props={
            "id": repo_node_id,
            "url": repo_url,
            "name": repo_name,
            "owner": repo_info.get("owner", "unknown"),
            "full_name": repo_info.get("full_name", "unknown"),
            "content": repo_info.get("full_name", "unknown"),
        }
    )
    
    # Upsert author as Person node
    author_id = f"person:{pr_author}"
    memory.upsert_node(
        "Person",
        match_props={"email": pr_author_email},
        set_props={
            "id": author_id,
            "name": pr_author,
            "email": pr_author_email,
            "content": f"{pr_author} ({pr_author_email})",
        }
    )
    
    # Create relationships
    memory.link(pr_node_id, Edge.BELONGS_TO, repo_node_id)
    memory.link(pr_node_id, Edge.CREATED_BY, author_id)
    
    # If PR is merged and includes commits, link to commits
    # This would require additional commit SHAs from the payload
    # For now, we'll just store the PR metadata
    
    return {
        "pr_node_id": pr_node_id,
        "pr_number": pr_number,
        "title": pr_title,
        "author": pr_author,
        "state": pr_state,
        "merged": pr_merged,
    }


__all__ = ["ingest_pull_request_metadata"]
