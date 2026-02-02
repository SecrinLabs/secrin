"""
Input validation utilities.
"""

import logging
from pathlib import Path
from typing import List, Optional

import yaml


logger = logging.getLogger(__name__)


def validate_repo_path(path: str) -> List[str]:
    """
    Validate repository path.

    Args:
        path: Repository path

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    repo_path = Path(path)

    if not repo_path.exists():
        errors.append(f"Path does not exist: {path}")
        return errors

    if not repo_path.is_dir():
        errors.append(f"Path is not a directory: {path}")
        return errors

    # Check for common repo indicators
    has_git = (repo_path / ".git").exists()
    has_python = any(repo_path.glob("**/*.py"))
    has_package = (repo_path / "pyproject.toml").exists() or (repo_path / "setup.py").exists()

    if not has_python:
        errors.append("No Python files found in repository")

    # Warnings (not errors)
    if not has_git:
        logger.warning("Directory is not a Git repository")

    return errors


def validate_config_file(path: str) -> tuple[bool, Optional[str]]:
    """
    Validate configuration file.

    Args:
        path: Config file path

    Returns:
        Tuple of (is_valid, error_message)
    """
    config_path = Path(path)

    if not config_path.exists():
        return False, f"Config file not found: {path}"

    if not config_path.is_file():
        return False, f"Config path is not a file: {path}"

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}"
    except Exception as e:
        return False, f"Could not read config file: {e}"

    # Validate required sections
    required_sections = ['llm', 'repository', 'arc42']
    for section in required_sections:
        if section not in data:
            return False, f"Missing required section: {section}"

    # Validate LLM config
    llm = data.get('llm', {})
    if not llm.get('api_key') and not llm.get('api_key', '').startswith('${'):
        logger.warning("API key not set in config (may be set via environment)")

    return True, None


def validate_output_path(path: str) -> List[str]:
    """
    Validate output path.

    Args:
        path: Output directory path

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    output_path = Path(path)

    # Check if parent exists or can be created
    parent = output_path.parent
    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            errors.append(f"Cannot create output directory: {path}")
        except Exception as e:
            errors.append(f"Error creating output directory: {e}")

    # Check write permissions
    if output_path.exists() and not output_path.is_dir():
        errors.append(f"Output path exists but is not a directory: {path}")

    return errors
