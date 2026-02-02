"""
CLI utility functions.
"""

from pathlib import Path
from typing import Dict, Any

from ..models.config import DEFAULT_CONFIG_YAML


def create_default_config(output_path: str, force: bool = False) -> None:
    """
    Create default configuration file.

    Args:
        output_path: Path to write config file
        force: Overwrite existing file if True

    Raises:
        FileExistsError: If file exists and force is False
    """
    path = Path(output_path)

    if path.exists() and not force:
        raise FileExistsError(f"Config file already exists: {output_path}")

    path.write_text(DEFAULT_CONFIG_YAML)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"
