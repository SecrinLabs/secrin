"""
Base Parser - Simplified

Parser only extracts AST data, doesn't build graphs.
Graph construction is handled in the memory package.
"""

from abc import ABC, abstractmethod
from tree_sitter import Language, Parser
from pathlib import Path
from typing import Any, Union


class BaseLanguageParser(ABC):
    """Abstract base class for language-specific parsers"""
    
    def __init__(self, language: Union[Language, Any]):
        # Handle both Language objects and PyCapsule objects from tree-sitter-languages
        if not isinstance(language, Language):
            language = Language(language)
        
        self.parser = Parser(language)
        self.language = language
    
    @property
    @abstractmethod
    def language_name(self) -> str:
        """Return the name of the language (e.g., 'python', 'javascript')"""
        pass
    
    @property
    @abstractmethod
    def file_extensions(self) -> list[str]:
        """Return list of file extensions this parser handles (e.g., ['.py'])"""
        pass
    
    @abstractmethod
    def parse_file(self, file_path: Path, content: str) -> Any:
        """
        Parse a file and extract AST information.
        
        Returns structured data (dict, dataclass, etc) - NOT a graph.
        Graph construction should be done elsewhere.
        """
        pass
