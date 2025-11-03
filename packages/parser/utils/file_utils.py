"""Utility functions for the parser"""
import mimetypes
from pathlib import Path
from typing import Optional


# Language to file extension mapping
LANGUAGE_EXTENSIONS = {
    "python": [".py", ".pyi"],
    "javascript": [".js", ".jsx", ".mjs", ".cjs"],
    "typescript": [".ts", ".tsx"],
    "java": [".java"],
    "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".h"],
    "c": [".c", ".h"],
    "go": [".go"],
    "rust": [".rs"],
    "ruby": [".rb"],
    "php": [".php"],
    "swift": [".swift"],
    "kotlin": [".kt", ".kts"],
}

# Extension to language mapping (reverse)
EXTENSION_TO_LANGUAGE = {}
for lang, exts in LANGUAGE_EXTENSIONS.items():
    for ext in exts:
        EXTENSION_TO_LANGUAGE[ext] = lang


def detect_language(file_path: Path) -> Optional[str]:
    """
    Detect the programming language of a file based on its extension
    
    Args:
        file_path: Path to the file
    
    Returns:
        Language name (e.g., 'python', 'javascript') or None if unknown
    """
    suffix = file_path.suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(suffix)


def is_code_file(file_path: Path) -> bool:
    """
    Check if a file is a code file that we can parse
    
    Args:
        file_path: Path to the file
    
    Returns:
        True if the file is a recognized code file
    """
    return detect_language(file_path) is not None


def is_test_file(file_path: Path) -> bool:
    """
    Check if a file appears to be a test file
    
    Args:
        file_path: Path to the file
    
    Returns:
        True if the file appears to be a test file
    """
    path_str = str(file_path).lower()
    name = file_path.name.lower()
    
    # Common test patterns
    test_indicators = [
        'test_',
        '_test.',
        'tests/',
        '/test/',
        'spec.',
        '_spec.',
        '__tests__/',
        '.test.',
        '.spec.',
        'test.py',
        'test.js',
        'test.ts',
    ]
    
    return any(indicator in path_str or indicator in name for indicator in test_indicators)


def is_readme_file(file_path: Path) -> bool:
    """
    Check if a file is a README file
    
    Args:
        file_path: Path to the file
    
    Returns:
        True if the file is a README
    """
    name = file_path.name.lower()
    return name.startswith('readme')


def should_ignore_path(path: Path) -> bool:
    """
    Check if a path should be ignored during parsing
    
    Args:
        path: Path to check
    
    Returns:
        True if the path should be ignored
    """
    ignore_patterns = {
        # Version control
        ".git",
        ".svn",
        ".hg",
        
        # Dependencies
        "node_modules",
        "vendor",
        "venv",
        ".venv",
        "env",
        ".env",
        "__pycache__",
        ".pytest_cache",
        
        # Build outputs
        "dist",
        "build",
        "target",
        "out",
        ".next",
        ".nuxt",
        
        # IDE
        ".vscode",
        ".idea",
        ".eclipse",
        
        # Other
        ".DS_Store",
        "coverage",
        ".coverage",
    }
    
    # Check if any part of the path matches ignore patterns
    parts = path.parts
    for part in parts:
        if part in ignore_patterns or part.startswith('.') and len(part) > 1:
            return True
    
    return False


def get_file_hash(content: str) -> str:
    """
    Generate a hash for file content
    
    Args:
        content: File content
    
    Returns:
        SHA256 hash of the content
    """
    import hashlib
    return hashlib.sha256(content.encode()).hexdigest()


def get_relative_path(file_path: Path, repo_root: Path) -> Path:
    """
    Get the relative path of a file from the repo root
    
    Args:
        file_path: Absolute path to the file
        repo_root: Absolute path to the repo root
    
    Returns:
        Relative path
    """
    try:
        return file_path.relative_to(repo_root)
    except ValueError:
        # If file_path is not relative to repo_root, return as-is
        return file_path
