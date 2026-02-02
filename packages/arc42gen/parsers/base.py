"""
Abstract base class for language-specific parsers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..models.analysis import ClassDef, FunctionDef, ImportDef


class BaseLanguageParser(ABC):
    """
    Abstract base class for language-specific AST parsers.

    Each language parser must implement methods to extract:
    - Classes and their methods
    - Functions (module-level)
    - Import statements
    - Module docstrings
    """

    @abstractmethod
    def parse(self, source_code: str) -> None:
        """
        Parse source code and prepare for extraction.

        Args:
            source_code: The source code to parse
        """
        pass

    @abstractmethod
    def extract_classes(self) -> List[ClassDef]:
        """
        Extract all class definitions from parsed source.

        Returns:
            List of ClassDef objects
        """
        pass

    @abstractmethod
    def extract_functions(self) -> List[FunctionDef]:
        """
        Extract all module-level function definitions.

        Returns:
            List of FunctionDef objects
        """
        pass

    @abstractmethod
    def extract_imports(self) -> List[ImportDef]:
        """
        Extract all import statements.

        Returns:
            List of ImportDef objects
        """
        pass

    @abstractmethod
    def extract_docstring(self) -> Optional[str]:
        """
        Extract module-level docstring.

        Returns:
            Module docstring or None
        """
        pass

    @abstractmethod
    def count_lines(self) -> int:
        """
        Count lines of code (excluding blank lines and comments).

        Returns:
            Number of lines of code
        """
        pass

    def get_public_symbols(self) -> List[str]:
        """
        Get list of public symbols (not starting with _).

        Returns:
            List of public class and function names
        """
        symbols = []

        for cls in self.extract_classes():
            if not cls.name.startswith('_'):
                symbols.append(cls.name)

        for func in self.extract_functions():
            if not func.name.startswith('_'):
                symbols.append(func.name)

        return symbols
