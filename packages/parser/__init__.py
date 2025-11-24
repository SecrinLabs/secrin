"""
Parser package - AST extraction only

Parses Python and JavaScript files using tree-sitter.
Returns simple structured data (no graph modeling).

Graph construction should be done in the memory package.
"""

from packages.parser.languages.python_parser import PythonParser, ParsedFile
from packages.parser.languages.javascript_parser import JavaScriptParser

__all__ = ["PythonParser", "JavaScriptParser", "ParsedFile"]

__version__ = "0.1.0"
