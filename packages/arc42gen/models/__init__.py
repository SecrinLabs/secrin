"""
Data models for arc42gen.
"""

from .config import Config, LLMConfig, RepositoryConfig
from .analysis import (
    Module,
    Dependency,
    CodeStatistics,
    ModuleTree,
    DependencyGraph,
    AnalysisResult,
)
from .documentation import (
    ComponentDescription,
    Level1Whitebox,
    Level2Whitebox,
    Section5,
)

__all__ = [
    "Config",
    "LLMConfig",
    "RepositoryConfig",
    "Module",
    "Dependency",
    "CodeStatistics",
    "ModuleTree",
    "DependencyGraph",
    "AnalysisResult",
    "ComponentDescription",
    "Level1Whitebox",
    "Level2Whitebox",
    "Section5",
]
