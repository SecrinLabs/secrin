"""
Centralised language and file extension constants for arc42gen.

All language-related mappings live here so they can be maintained in one place.
"""

from typing import Dict, List


# ============================================================================
# File Extension → Language Mapping
# ============================================================================

# Canonical mapping: file extension (with dot) → language name
EXTENSION_TO_LANGUAGE: Dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
}

# Reverse mapping: extension without dot → language (for utilities)
EXT_TO_LANGUAGE: Dict[str, str] = {
    ext.lstrip("."): lang
    for ext, lang in EXTENSION_TO_LANGUAGE.items()
}

# ============================================================================
# Language → Markdown Code Fence Language
# ============================================================================

# Maps language name to the string used in ```<lang> code fences
LANGUAGE_TO_FENCE: Dict[str, str] = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
}

# Extension (without dot) → fence language (for code samples)
EXT_TO_FENCE: Dict[str, str] = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "jsx": "jsx",
    "tsx": "tsx",
    "mjs": "javascript",
    "cjs": "javascript",
    "mts": "typescript",
    "cts": "typescript",
}

# ============================================================================
# Supported Languages
# ============================================================================

SUPPORTED_LANGUAGES: List[str] = ["python", "javascript", "typescript"]

# Valid values for the repository.language config field
VALID_LANGUAGE_CONFIG: List[str] = SUPPORTED_LANGUAGES + ["auto"]

# Default language when auto-detection finds nothing
DEFAULT_LANGUAGE: str = "python"

# ============================================================================
# Default Glob Patterns
# ============================================================================

# Default file include patterns for repository analysis
DEFAULT_INCLUDE_PATTERNS: List[str] = [
    f"**/*{ext}" for ext in EXTENSION_TO_LANGUAGE
]

# Default exclude patterns
DEFAULT_EXCLUDE_PATTERNS: List[str] = [
    "**/test/**",
    "**/tests/**",
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/dist/**",
    "**/build/**",
]


# ============================================================================
# Helpers
# ============================================================================

def get_language_for_extension(ext: str) -> str:
    """
    Get language name for a file extension.

    Args:
        ext: Extension with or without leading dot (e.g., ".py" or "py")

    Returns:
        Language name, or the extension itself if unrecognised.
    """
    if ext.startswith("."):
        return EXTENSION_TO_LANGUAGE.get(ext, ext.lstrip("."))
    return EXT_TO_LANGUAGE.get(ext, ext)


def get_fence_language(ext: str) -> str:
    """
    Get the markdown code-fence language for a file extension.

    Args:
        ext: Extension without dot (e.g., "py", "tsx")

    Returns:
        Fence language string.
    """
    return EXT_TO_FENCE.get(ext, ext)


def is_supported_extension(ext: str) -> bool:
    """Check if a file extension is supported (with or without dot)."""
    if ext.startswith("."):
        return ext in EXTENSION_TO_LANGUAGE
    return ext in EXT_TO_LANGUAGE
