"""
Utility functions for arc42gen.
"""

from .file_utils import (
    get_file_extension,
    is_python_file,
    read_file_safe,
    ensure_directory,
)
from .validation import (
    validate_repo_path,
    validate_config_file,
)
from .git_utils import (
    is_remote_url,
    clone_repository,
    cleanup_cloned_repo,
    get_repo_info,
)
from .progress import (
    ProgressTracker,
    ProgressBar,
)

__all__ = [
    "get_file_extension",
    "is_python_file",
    "read_file_safe",
    "ensure_directory",
    "validate_repo_path",
    "validate_config_file",
    "is_remote_url",
    "clone_repository",
    "cleanup_cloned_repo",
    "get_repo_info",
    "ProgressTracker",
    "ProgressBar",
]
