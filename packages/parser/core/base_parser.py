from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING
from tree_sitter import Language, Parser, Node
from pathlib import Path

from packages.parser.models import GraphData

if TYPE_CHECKING:
    from packages.parser.models import FileNode


class BaseLanguageParser(ABC):
    """Abstract base class for language-specific parsers"""
    
    def __init__(self, language: Language):
        self.parser = Parser(language)  # Updated for tree-sitter 0.21+
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
    
    def parse_file(self, file_path: Path, content: str, repo_context: dict) -> GraphData:
        """
        Parse a file and extract all nodes and relationships
        
        Args:
            file_path: Path to the file being parsed
            content: Content of the file
            repo_context: Dictionary with repo metadata (name, sha, url, etc.)
        
        Returns:
            GraphData object containing all extracted nodes and relationships
        """
        tree = self.parser.parse(bytes(content, "utf8"))
        graph_data = GraphData()
        
        # Create File node
        file_node = self._create_file_node(file_path, content, repo_context)
        graph_data.add_node(file_node)
        
        # Extract code elements
        self._extract_classes(tree.root_node, content, file_node, graph_data, repo_context)
        self._extract_functions(tree.root_node, content, file_node, graph_data, repo_context)
        self._extract_imports(tree.root_node, content, file_node, graph_data, repo_context)
        self._extract_variables(tree.root_node, content, file_node, graph_data, repo_context)
        self._extract_docs(tree.root_node, content, file_node, graph_data, repo_context)
        
        # Extract additional metadata
        self._extract_tests(tree.root_node, content, file_node, graph_data, repo_context)
        self._extract_commits(file_path, file_node, graph_data, repo_context)
        
        return graph_data
    
    @abstractmethod
    def _create_file_node(self, file_path: Path, content: str, repo_context: dict) -> 'FileNode':
        """Create a FileNode for the given file"""
        pass
    
    @abstractmethod
    def _extract_classes(self, root_node: Node, content: str, file_node, graph_data: GraphData, repo_context: dict):
        """Extract class definitions from the AST"""
        pass
    
    @abstractmethod
    def _extract_functions(self, root_node: Node, content: str, file_node, graph_data: GraphData, repo_context: dict):
        """Extract function/method definitions from the AST"""
        pass
    
    @abstractmethod
    def _extract_imports(self, root_node: Node, content: str, file_node, graph_data: GraphData, repo_context: dict):
        """Extract import statements"""
        pass
    
    @abstractmethod
    def _extract_variables(self, root_node: Node, content: str, file_node, graph_data: GraphData, repo_context: dict):
        """Extract variable declarations"""
        pass
    
    def _extract_docs(self, root_node: Node, content: str, file_node, graph_data: GraphData, repo_context: dict):
        """Extract documentation (can be overridden by subclasses)"""
        pass
    
    def _extract_tests(self, root_node: Node, content: str, file_node, graph_data: GraphData, repo_context: dict):
        """Extract test cases (can be overridden by subclasses)"""
        pass
    
    def _extract_commits(self, file_path: Path, file_node, graph_data: GraphData, repo_context: dict):
        """Extract commit information for the file (can be overridden by subclasses)"""
        pass
    
    def _extract_function_calls(self, node: Node, content: str, function_node, graph_data: GraphData):
        """Extract function calls within a function (helper method)"""
        pass
    
    def _get_node_text(self, node: Node, content: str) -> str:
        """Extract text from a tree-sitter node"""
        return content[node.start_byte:node.end_byte]
    
    def _get_line_number(self, node: Node) -> int:
        """Get line number (1-indexed) from node"""
        return node.start_point[0] + 1
    
    def _generate_id(self, *parts: str) -> str:
        """Generate a canonical ID for a node"""
        return ":".join(str(p) for p in parts)
    
    def _get_snippet(self, content: str, start_line: int, end_line: int, max_lines: int = 5) -> str:
        """Extract a code snippet (limited to max_lines)"""
        lines = content.split('\n')
        start_idx = start_line - 1
        end_idx = min(start_line - 1 + max_lines, end_line)
        return '\n'.join(lines[start_idx:end_idx])
