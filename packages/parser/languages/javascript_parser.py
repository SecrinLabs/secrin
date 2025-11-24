"""
Simplified JavaScript/TypeScript Parser - Manual AST traversal

Extracts code structure from JS/TS files using tree-sitter.
Returns simple dictionaries - no graph modeling.
"""

from tree_sitter import Node
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field, asdict
import hashlib

from packages.parser.core import BaseLanguageParser


@dataclass
class ParsedFile:
    """Container for parsed file data"""
    path: str
    language: str
    sha: str
    lines: int
    classes: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class JavaScriptParser(BaseLanguageParser):
    """Parser for JavaScript/TypeScript files"""
    
    @property
    def language_name(self) -> str:
        return "javascript"
    
    @property
    def file_extensions(self) -> list[str]:
        return [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]
    
    def parse_file(self, file_path: Path, content: str) -> ParsedFile:
        """Parse a JS/TS file and extract structure"""
        tree = self.parser.parse(bytes(content, "utf8"))
        root_node = tree.root_node
        
        result = ParsedFile(
            path=str(file_path),
            language=self.language_name,
            sha=hashlib.sha256(content.encode()).hexdigest(),
            lines=len(content.split('\n'))
        )
        
        # Traverse AST and extract elements
        self._traverse(root_node, content, result)
        
        return result
    
    def _traverse(self, node: Node, content: str, result: ParsedFile):
        """Traverse AST and extract code elements"""
        if node.type == "class_declaration":
            class_info = self._extract_class(node, content)
            if class_info:
                result.classes.append(class_info)
        
        elif node.type in ("function_declaration", "arrow_function", "function"):
            func_info = self._extract_function(node, content)
            if func_info:
                result.functions.append(func_info)
        
        elif node.type == "import_statement":
            import_text = content[node.start_byte:node.end_byte]
            result.imports.append(import_text)
        
        elif node.type == "export_statement":
            export_text = content[node.start_byte:node.end_byte]
            result.exports.append(export_text)
        
        # Recurse to children
        for child in node.children:
            self._traverse(child, content, result)
    
    def _extract_class(self, node: Node, content: str) -> Dict[str, Any]:
        """Extract class information"""
        name = "Unknown"
        methods = []
        extends = None
        
        for child in node.children:
            if child.type == "identifier" or child.type == "type_identifier":
                name = content[child.start_byte:child.end_byte]
            elif child.type == "class_heritage":
                for heritage_child in child.children:
                    if heritage_child.type == "identifier":
                        extends = content[heritage_child.start_byte:heritage_child.end_byte]
            elif child.type == "class_body":
                methods = self._extract_methods(child, content)
        
        return {
            "name": name,
            "start_line": node.start_point[0] + 1,
            "end_line": node.end_point[0] + 1,
            "extends": extends,
            "methods": [m["name"] for m in methods],
            "method_details": methods
        }
    
    def _extract_methods(self, class_body: Node, content: str) -> List[Dict[str, Any]]:
        """Extract methods from class body"""
        methods = []
        for child in class_body.children:
            if child.type == "method_definition":
                method_info = self._extract_function(child, content)
                if method_info:
                    methods.append(method_info)
        return methods
    
    def _extract_function(self, node: Node, content: str) -> Dict[str, Any]:
        """Extract function information"""
        name = "anonymous"
        params = []
        calls = []
        
        for child in node.children:
            if child.type == "identifier":
                name = content[child.start_byte:child.end_byte]
            elif child.type == "formal_parameters":
                params = self._extract_params(child, content)
            elif child.type in ("statement_block", "expression"):
                calls = self._extract_calls(child, content)
        
        return {
            "name": name,
            "start_line": node.start_point[0] + 1,
            "end_line": node.end_point[0] + 1,
            "parameters": params,
            "calls": calls
        }
    
    def _extract_params(self, params_node: Node, content: str) -> List[str]:
        """Extract parameter names"""
        params = []
        for child in params_node.children:
            if child.type == "identifier":
                params.append(content[child.start_byte:child.end_byte])
            elif child.type == "required_parameter":
                for subchild in child.children:
                    if subchild.type == "identifier":
                        params.append(content[subchild.start_byte:subchild.end_byte])
                        break
        return params
    
    def _extract_calls(self, node: Node, content: str) -> List[str]:
        """Extract function calls"""
        calls = []
        self._find_calls(node, content, calls)
        return list(set(calls))  # Dedupe
    
    def _find_calls(self, node: Node, content: str, calls: List[str]):
        """Recursively find call expressions"""
        if node.type == "call_expression":
            for child in node.children:
                if child.type in ("identifier", "member_expression"):
                    call_name = content[child.start_byte:child.end_byte]
                    calls.append(call_name)
                    break
        
        for child in node.children:
            self._find_calls(child, content, calls)
