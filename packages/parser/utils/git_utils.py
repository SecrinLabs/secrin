"""Git and GitHub repository utilities"""
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse


def is_github_url(path: str) -> bool:
    """
    Check if a string is a GitHub URL
    
    Args:
        path: String that might be a URL or local path
    
    Returns:
        True if it's a GitHub URL
    """
    try:
        parsed = urlparse(path)
        return parsed.netloc in ['github.com', 'www.github.com'] or path.startswith('git@github.com')
    except:
        return False


def is_git_url(path: str) -> bool:
    """
    Check if a string is any Git URL
    
    Args:
        path: String that might be a URL or local path
    
    Returns:
        True if it's a Git URL
    """
    git_indicators = [
        'github.com',
        'gitlab.com',
        'bitbucket.org',
        '.git',
        'git@',
        'https://',
        'http://',
    ]
    return any(indicator in path for indicator in git_indicators)


def normalize_github_url(url: str) -> str:
    """
    Normalize GitHub URL to HTTPS format
    
    Args:
        url: GitHub URL in various formats
    
    Returns:
        Normalized HTTPS URL
    """
    # Handle git@ format
    if url.startswith('git@github.com:'):
        url = url.replace('git@github.com:', 'https://github.com/')
    
    # Remove .git suffix if present
    if url.endswith('.git'):
        url = url[:-4]
    
    # Ensure https://
    if not url.startswith('http'):
        if 'github.com' in url and not url.startswith('github.com'):
            pass  # Already has a protocol-like part
        elif 'github.com' in url:
            url = f'https://{url}'
    
    return url


def clone_repository(repo_url: str, target_dir: Optional[Path] = None, shallow: bool = True) -> Tuple[Path, bool]:
    """
    Clone a Git repository to a local directory
    
    Args:
        repo_url: URL of the repository
        target_dir: Target directory (creates temp dir if None)
        shallow: If True, do a shallow clone (faster, less disk space)
    
    Returns:
        Tuple of (path to cloned repo, is_temporary)
    """
    is_temporary = target_dir is None
    
    if is_temporary:
        target_dir = Path(tempfile.mkdtemp(prefix='repo_parser_'))
    else:
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
    
    # Normalize URL
    repo_url = normalize_github_url(repo_url)
    
    # Build clone command
    cmd = ['git', 'clone']
    
    if shallow:
        cmd.extend(['--depth', '1'])  # Shallow clone
    
    cmd.extend([repo_url, str(target_dir)])
    
    try:
        print(f"Cloning repository: {repo_url}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")
        
        print(f"✓ Repository cloned to: {target_dir}")
        return target_dir, is_temporary
        
    except subprocess.TimeoutExpired:
        if is_temporary:
            shutil.rmtree(target_dir, ignore_errors=True)
        raise RuntimeError("Git clone timed out after 5 minutes")
    except Exception as e:
        if is_temporary:
            shutil.rmtree(target_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to clone repository: {e}")


def cleanup_temp_repo(repo_path: Path):
    """
    Clean up a temporary repository directory
    
    Args:
        repo_path: Path to the repository to remove
    """
    if repo_path.exists():
        try:
            shutil.rmtree(repo_path)
            print(f"✓ Cleaned up temporary directory: {repo_path}")
        except Exception as e:
            print(f"Warning: Could not remove temporary directory {repo_path}: {e}")


def extract_repo_info(repo_url: str) -> dict:
    """
    Extract repository information from URL
    
    Args:
        repo_url: Repository URL
    
    Returns:
        Dictionary with owner, name, and url
    """
    # Normalize URL
    url = normalize_github_url(repo_url)
    
    # Parse URL
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    if len(path_parts) >= 2:
        owner = path_parts[0]
        repo_name = path_parts[1]
        
        return {
            'owner': owner,
            'name': repo_name,
            'url': url,
            'full_name': f"{owner}/{repo_name}"
        }
    
    return {
        'owner': 'unknown',
        'name': Path(repo_url).name,
        'url': repo_url,
        'full_name': 'unknown'
    }


def is_git_installed() -> bool:
    """
    Check if git is installed and available
    
    Returns:
        True if git is available
    """
    try:
        result = subprocess.run(
            ['git', '--version'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False
