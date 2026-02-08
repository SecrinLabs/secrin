"""
Prompt template loader.

Loads .txt prompt templates from the templates/prompts/ directory
and formats them with provided variables.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


@lru_cache(maxsize=64)
def load_prompt_raw(name: str) -> str:
    """
    Load a raw prompt template by name (without .txt extension).

    Args:
        name: Template name, e.g. "arc42/section_01" or "c4/level_1"

    Returns:
        Raw template string with {placeholders}.

    Raises:
        FileNotFoundError: If the template file doesn't exist.
    """
    # Support both slash and dot notation
    template_path = PROMPTS_DIR / f"{name}.txt"

    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    return template_path.read_text()


def load_prompt(name: str, **kwargs: Any) -> str:
    """
    Load a prompt template and format it with provided variables.

    Args:
        name: Template name, e.g. "arc42/section_01"
        **kwargs: Variables to substitute into the template.

    Returns:
        Formatted prompt string.

    Example:
        prompt = load_prompt("arc42/section_01",
            repo_name="my-app",
            language="python",
            total_files=42,
        )
    """
    template = load_prompt_raw(name)

    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.warning(f"Missing template variable {e} in prompt '{name}'")
        # Fall back to partial formatting - fill what we can
        for key, value in kwargs.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template
