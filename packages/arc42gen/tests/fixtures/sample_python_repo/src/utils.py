"""
Utility functions for the sample application.
"""

from typing import Any, List


def format_string(value: str) -> str:
    """Format a string value."""
    return value.strip().lower()


def calculate_total(items: List[float]) -> float:
    """Calculate total of numeric items."""
    return sum(items)


class Logger:
    """Simple logger class."""

    def __init__(self, name: str = "default"):
        self.name = name

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message."""
        print(f"[{level}] {self.name}: {message}")

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.log(message, "DEBUG")

    def error(self, message: str) -> None:
        """Log error message."""
        self.log(message, "ERROR")
