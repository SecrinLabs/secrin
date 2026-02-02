"""
Git utilities for repository operations.
"""

import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import git


logger = logging.getLogger(__name__)


def is_remote_url(path: str) -> bool:
    """
    Check if the path is a remote Git URL.

    Args:
        path: Repository path or URL

    Returns:
        True if remote URL, False if local path
    """
    if path.startswith(('http://', 'https://', 'git@', 'git://', 'ssh://')):
        return True

    # Check for GitHub shorthand (owner/repo)
    if '/' in path and not Path(path).exists():
        parts = path.split('/')
        if len(parts) == 2 and not path.startswith('.'):
            return True

    return False


def parse_repo_url(url: str) -> Tuple[str, str]:
    """
    Parse repository URL to extract owner and repo name.

    Args:
        url: Repository URL or shorthand

    Returns:
        Tuple of (full_url, repo_name)
    """
    # Handle GitHub shorthand (owner/repo)
    if not url.startswith(('http://', 'https://', 'git@', 'git://', 'ssh://')):
        if '/' in url:
            parts = url.split('/')
            if len(parts) == 2:
                owner, repo = parts
                url = f"https://github.com/{owner}/{repo}.git"
                return url, repo

    # Extract repo name from URL
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')

    if path.endswith('.git'):
        path = path[:-4]

    repo_name = path.split('/')[-1]

    return url, repo_name


def clone_repository(
    url: str,
    target_dir: Optional[str] = None,
    depth: int = 1,
    branch: Optional[str] = None
) -> Path:
    """
    Clone a remote Git repository.

    Args:
        url: Repository URL (HTTPS or SSH)
        target_dir: Target directory (uses temp dir if not specified)
        depth: Clone depth (1 for shallow clone)
        branch: Specific branch to clone

    Returns:
        Path to cloned repository

    Raises:
        git.GitCommandError: If clone fails
    """
    full_url, repo_name = parse_repo_url(url)

    # Determine target directory
    if target_dir:
        clone_path = Path(target_dir)
    else:
        # Use temp directory
        temp_dir = tempfile.mkdtemp(prefix="arc42gen_")
        clone_path = Path(temp_dir) / repo_name

    logger.info(f"Cloning {full_url} to {clone_path}")

    try:
        clone_kwargs = {
            'depth': depth,
        }

        if branch:
            clone_kwargs['branch'] = branch

        git.Repo.clone_from(full_url, clone_path, **clone_kwargs)

        logger.info(f"Successfully cloned to {clone_path}")
        return clone_path

    except git.GitCommandError as e:
        logger.error(f"Failed to clone repository: {e}")
        # Clean up on failure
        if clone_path.exists():
            shutil.rmtree(clone_path)
        raise


def cleanup_cloned_repo(repo_path: Path) -> None:
    """
    Clean up a cloned repository.

    Args:
        repo_path: Path to cloned repository
    """
    if repo_path.exists() and str(repo_path).startswith(tempfile.gettempdir()):
        logger.debug(f"Cleaning up temporary repo: {repo_path}")
        shutil.rmtree(repo_path)


def get_repo_info(repo_path: Path) -> dict:
    """
    Get information about a Git repository.

    Args:
        repo_path: Path to repository

    Returns:
        Dictionary with repo information
    """
    try:
        repo = git.Repo(repo_path)

        info = {
            'is_git_repo': True,
            'branch': repo.active_branch.name if not repo.head.is_detached else 'HEAD',
            'commit': repo.head.commit.hexsha[:8],
            'commit_message': repo.head.commit.message.split('\n')[0],
            'remote_url': None,
        }

        if repo.remotes:
            info['remote_url'] = repo.remotes.origin.url

        return info

    except (git.InvalidGitRepositoryError, git.GitCommandError):
        return {
            'is_git_repo': False,
            'branch': None,
            'commit': None,
            'commit_message': None,
            'remote_url': None,
        }
