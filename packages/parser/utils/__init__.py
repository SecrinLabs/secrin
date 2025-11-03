"""Utility modules for the parser"""
from .file_utils import (
    detect_language,
    is_code_file,
    should_ignore_path,
    get_file_hash,
    get_relative_path,
)
from .language_config import language_registry
from .git_utils import (
    is_github_url,
    is_git_url,
    clone_repository,
    cleanup_temp_repo,
    extract_repo_info,
    is_git_installed,
)

__all__ = [
    "detect_language",
    "is_code_file",
    "should_ignore_path",
    "get_file_hash",
    "get_relative_path",
    "language_registry",
    "is_github_url",
    "is_git_url",
    "clone_repository",
    "cleanup_temp_repo",
    "extract_repo_info",
    "is_git_installed",
]
