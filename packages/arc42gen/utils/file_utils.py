"""
File I/O utilities.
"""

import logging
from pathlib import Path
from typing import Optional

from ..constants import get_language_for_extension, is_supported_extension


logger = logging.getLogger(__name__)


def get_file_extension(file_path: str) -> str:
    """
    Get file extension without the dot.

    Args:
        file_path: Path to file

    Returns:
        File extension (e.g., 'py', 'js')
    """
    return Path(file_path).suffix.lstrip('.')


def get_file_language(file_path: str) -> str:
    """
    Get the programming language for a file.

    Args:
        file_path: Path to file

    Returns:
        Language name (e.g., 'python', 'typescript')
    """
    ext = get_file_extension(file_path)
    return get_language_for_extension(ext)


def is_python_file(file_path: str) -> bool:
    """
    Check if file is a Python file.

    Args:
        file_path: Path to file

    Returns:
        True if Python file
    """
    return get_file_extension(file_path) == 'py'


def is_supported_file(file_path: str) -> bool:
    """
    Check if file is a supported source file.

    Args:
        file_path: Path to file

    Returns:
        True if the file extension is supported
    """
    return is_supported_extension(get_file_extension(file_path))


def read_file_safe(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Safely read file contents.

    Args:
        file_path: Path to file
        encoding: File encoding

    Returns:
        File contents or None if error
    """
    try:
        return Path(file_path).read_text(encoding=encoding)
    except UnicodeDecodeError:
        # Try with latin-1 as fallback
        try:
            return Path(file_path).read_text(encoding='latin-1')
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return None
    except Exception as e:
        logger.warning(f"Could not read file {file_path}: {e}")
        return None


def ensure_directory(path: str) -> Path:
    """
    Ensure directory exists, create if not.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def count_lines_of_code(source: str, exclude_blanks: bool = True, exclude_comments: bool = True) -> int:
    """
    Count lines of code in source string.

    Args:
        source: Source code string
        exclude_blanks: Exclude blank lines
        exclude_comments: Exclude comment lines

    Returns:
        Line count
    """
    count = 0
    for line in source.split('\n'):
        stripped = line.strip()

        if exclude_blanks and not stripped:
            continue

        if exclude_comments and stripped.startswith('#'):
            continue

        count += 1

    return count
