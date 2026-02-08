"""
Command-line interface for arc42gen.
"""

from .commands import cli
from .utils import create_default_config

__all__ = ["cli", "create_default_config"]
