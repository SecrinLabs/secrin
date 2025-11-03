"""Utilities for extracting git commit information"""
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict


def get_file_commits(repo_path: Path, file_path: Path, limit: int = 10) -> List[Dict]:
    """
    Get commit history for a specific file
    
    Args:
        repo_path: Path to the repository root
        file_path: Path to the file (can be relative or absolute)
        limit: Maximum number of commits to return
    
    Returns:
        List of commit dictionaries with hash, author, email, date, message
    """
    try:
        # Make file_path relative to repo_path
        if file_path.is_absolute():
            try:
                rel_path = file_path.relative_to(repo_path)
            except ValueError:
                rel_path = file_path
        else:
            rel_path = file_path
        
        # Git log format: hash|author|email|date|message
        cmd = [
            'git', 'log',
            f'-{limit}',
            '--format=%H|%an|%ae|%aI|%s',
            '--follow',  # Follow file renames
            '--',
            str(rel_path)
        ]
        
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return []
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            
            parts = line.split('|', 4)
            if len(parts) == 5:
                commits.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'email': parts[2],
                    'date': parts[3],
                    'message': parts[4],
                })
        
        return commits
        
    except Exception as e:
        print(f"Warning: Could not get commits for {file_path}: {e}")
        return []


def get_last_commit_for_file(repo_path: Path, file_path: Path) -> Optional[Dict]:
    """
    Get the last commit that modified a file
    
    Args:
        repo_path: Path to the repository root
        file_path: Path to the file
    
    Returns:
        Commit dictionary or None
    """
    commits = get_file_commits(repo_path, file_path, limit=1)
    return commits[0] if commits else None


def get_file_blame(repo_path: Path, file_path: Path) -> Dict[int, Dict]:
    """
    Get git blame information for a file (which commit/author modified each line)
    
    Args:
        repo_path: Path to the repository root
        file_path: Path to the file
    
    Returns:
        Dictionary mapping line numbers to commit info
    """
    try:
        if file_path.is_absolute():
            try:
                rel_path = file_path.relative_to(repo_path)
            except ValueError:
                rel_path = file_path
        else:
            rel_path = file_path
        
        cmd = ['git', 'blame', '--line-porcelain', str(rel_path)]
        
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return {}
        
        blame_data = {}
        current_commit = None
        current_line = None
        author = None
        
        for line in result.stdout.split('\n'):
            if line.startswith('author '):
                author = line[7:]
            elif line.startswith('author-time '):
                timestamp = int(line[12:])
                date = datetime.fromtimestamp(timestamp)
            elif line and line[0].isalnum() and len(line.split()) >= 3:
                # Commit hash line
                parts = line.split()
                current_commit = parts[0]
                current_line = int(parts[2])
            elif line.startswith('\t') and current_line:
                # Actual code line
                if current_commit and author:
                    blame_data[current_line] = {
                        'commit': current_commit,
                        'author': author,
                    }
        
        return blame_data
        
    except Exception as e:
        print(f"Warning: Could not get blame for {file_path}: {e}")
        return {}


def count_file_changes(repo_path: Path, file_path: Path) -> int:
    """
    Count how many times a file has been modified
    
    Args:
        repo_path: Path to the repository root
        file_path: Path to the file
    
    Returns:
        Number of commits that modified the file
    """
    commits = get_file_commits(repo_path, file_path, limit=1000)
    return len(commits)


def is_file_in_git(repo_path: Path, file_path: Path) -> bool:
    """
    Check if a file is tracked by git
    
    Args:
        repo_path: Path to the repository root
        file_path: Path to the file
    
    Returns:
        True if file is tracked by git
    """
    try:
        if file_path.is_absolute():
            try:
                rel_path = file_path.relative_to(repo_path)
            except ValueError:
                return False
        else:
            rel_path = file_path
        
        cmd = ['git', 'ls-files', '--error-unmatch', str(rel_path)]
        
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            timeout=5
        )
        
        return result.returncode == 0
        
    except:
        return False
