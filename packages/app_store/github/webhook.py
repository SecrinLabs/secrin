import logging
from typing import Dict, Any, Optional
from packages.ingest.incremental_ingest import incremental_ingest

logger = logging.getLogger(__name__)

def handle_github_event(event_type: str, payload: Dict[str, Any]):
    """
    Dispatch GitHub events to specific handlers.
    """
    logger.info(f"Received GitHub event: {event_type}")
    
    if event_type == "pull_request":
        return handle_pull_request(payload)
    
    if event_type == "push":
        return handle_push(payload)

    return {"status": "ignored", "reason": f"Event type {event_type} not handled"}

def handle_pull_request(payload: Dict[str, Any]):
    """
    Handle pull_request events.
    Specifically look for closed PRs that were merged.
    """
    action = payload.get("action")
    pull_request = payload.get("pull_request", {})
    merged = pull_request.get("merged", False)
    
    logger.info(f"Processing PR action: {action}, merged: {merged}")

    if action == "closed" and merged:
        # PR was merged
        repo_info = payload.get("repository", {})
        repo_url = repo_info.get("clone_url") or repo_info.get("html_url")
        
        # The branch where the PR was merged into (usually main/master)
        base_branch = pull_request.get("base", {}).get("ref")
        
        if repo_url and base_branch:
            logger.info(f"Triggering ingestion for merged PR in {repo_url} on branch {base_branch}")
            
            # Trigger ingestion via background task
            return {
                "status": "triggered",
                "task": "ingest",
                "repo_url": repo_url,
                "branch": base_branch
            }
            
    return {"status": "ignored", "reason": "Not a merged PR"}

def handle_push(payload: Dict[str, Any]):
    """
    Handle push events.
    """
    ref = payload.get("ref")
    repo_info = payload.get("repository", {})
    repo_url = repo_info.get("clone_url") or repo_info.get("html_url")
    
    # ref is usually "refs/heads/branch_name"
    branch = ref.replace("refs/heads/", "") if ref else None
    
    if repo_url and branch:
        logger.info(f"Triggering ingestion for push to {repo_url} on branch {branch}")
        return {
            "status": "triggered",
            "task": "ingest",
            "repo_url": repo_url,
            "branch": branch
        }
        
    return {"status": "ignored", "reason": "Invalid push payload"}

def run_ingestion(repo_url: str, branch: Optional[str]):
    """
    Wrapper to run incremental_ingest, suitable for BackgroundTasks.
    """
    try:
        logger.info(f"Starting background ingestion for {repo_url} branch {branch}")
        incremental_ingest(repo_url, branch=branch)
        logger.info(f"Finished background ingestion for {repo_url} branch {branch}")
    except Exception as e:
        logger.error(f"Error during background ingestion: {e}", exc_info=True)
