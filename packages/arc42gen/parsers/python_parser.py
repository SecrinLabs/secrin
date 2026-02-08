"""
Python AST parser using tree-sitter.
"""

import logging
from typing import List, Optional

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Node

from .base import BaseLanguageParser
from ..models.analysis import ClassDef, FunctionDef, ImportDef


logger = logging.getLogger(__name__)


class PythonParser(BaseLanguageParser):
    """
    Python AST parser using tree-sitter.

    Extracts:
    - Class definitions with methods and bases
    - Function definitions with parameters
    - Import statements (import and from...import)
    - Module docstrings
    """

    def __init__(self):
        """Initialize the Python parser."""
        self.PY_LANGUAGE = Language(tspython.language())
        self.parser = Parser(self.PY_LANGUAGE)
        self.tree = None
        self.source_code = ""
        self._source_bytes = b""

    def parse(self, source_code: str) -> None:
        """
        Parse Python source code.

        Args:
            source_code: Python source code string
        """
        self.source_code = source_code
        self._source_bytes = source_code.encode('utf8')
        self.tree = self.parser.parse(self._source_bytes)

    def _get_node_text(self, node: Node) -> str:
        """Get text content of a node."""
        return self._source_bytes[node.start_byte:node.end_byte].decode('utf8')

    def extract_classes(self) -> List[ClassDef]:
        """Extract all class definitions."""
        if not self.tree:
            return []

        classes = []
        self._extract_classes_recursive(self.tree.root_node, classes)
        return classes

    def _extract_classes_recursive(self, node: Node, classes: List[ClassDef], depth: int = 0) -> None:
        """Recursively extract class definitions."""
        if node.type == 'class_definition':
            class_def = self._parse_class_node(node)
            if class_def:
                classes.append(class_def)
            return  # Don't recurse into nested classes for top-level extraction
        elif node.type == 'decorated_definition':
            # Handle decorated classes
            decorators = []
            for child in node.children:
                if child.type == 'decorator':
                    dec_text = self._get_node_text(child)
                    decorators.append(dec_text.lstrip('@'))
                elif child.type == 'class_definition':
                    class_def = self._parse_class_node(child)
                    if class_def:
                        class_def.decorators = decorators
                        classes.append(class_def)
            return

        for child in node.children:
            self._extract_classes_recursive(child, classes, depth)

    def _parse_class_node(self, node: Node) -> Optional[ClassDef]:
        """Parse a class_definition node."""
        name = None
        bases = []
        methods = []
        decorators = []
        docstring = None

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child)
            elif child.type == 'argument_list':
                # Class bases/inheritance
                for arg in child.children:
                    if arg.type == 'identifier':
                        bases.append(self._get_node_text(arg))
                    elif arg.type == 'attribute':
                        bases.append(self._get_node_text(arg))
            elif child.type == 'block':
                # Extract methods and docstring from class body
                methods, docstring = self._extract_class_body(child)
            elif child.type == 'decorator':
                dec_text = self._get_node_text(child)
                decorators.append(dec_text.lstrip('@'))

        if name:
            return ClassDef(
                name=name,
                line_number=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                docstring=docstring,
                methods=methods,
                bases=bases,
                decorators=decorators,
            )
        return None

    def _extract_class_body(self, block_node: Node) -> tuple[List[str], Optional[str]]:
        """Extract methods and docstring from class body."""
        methods = []
        docstring = None
        first_statement = True

        for child in block_node.children:
            if child.type == 'function_definition':
                # Get method name
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        methods.append(self._get_node_text(subchild))
                        break
            elif child.type == 'expression_statement' and first_statement:
                # Check for docstring
                for subchild in child.children:
                    if subchild.type == 'string':
                        docstring = self._get_node_text(subchild).strip('"""\'\'\'')
                        break

            if child.type not in ['comment', 'newline']:
                first_statement = False

        return methods, docstring

    def extract_functions(self) -> List[FunctionDef]:
        """Extract module-level function definitions."""
        if not self.tree:
            return []

        functions = []
        for child in self.tree.root_node.children:
            if child.type == 'function_definition':
                func_def = self._parse_function_node(child)
                if func_def:
                    functions.append(func_def)
            elif child.type == 'decorated_definition':
                # Handle decorated functions
                for subchild in child.children:
                    if subchild.type == 'function_definition':
                        func_def = self._parse_function_node(subchild, child)
                        if func_def:
                            functions.append(func_def)

        return functions

    def _parse_function_node(self, node: Node, decorated_node: Optional[Node] = None) -> Optional[FunctionDef]:
        """Parse a function_definition node."""
        name = None
        parameters = []
        return_type = None
        docstring = None
        decorators = []
        is_async = False

        # Check for async
        if decorated_node:
            for child in decorated_node.children:
                if child.type == 'decorator':
                    dec_text = self._get_node_text(child)
                    decorators.append(dec_text.lstrip('@'))

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child)
            elif child.type == 'parameters':
                parameters = self._extract_parameters(child)
            elif child.type == 'type':
                return_type = self._get_node_text(child)
            elif child.type == 'block':
                docstring = self._extract_docstring_from_block(child)
            elif child.type == 'async':
                is_async = True

        if name:
            return FunctionDef(
                name=name,
                line_number=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                docstring=docstring,
                parameters=parameters,
                return_type=return_type,
                decorators=decorators,
                is_async=is_async,
            )
        return None

    def _extract_parameters(self, params_node: Node) -> List[str]:
        """Extract parameter names from parameters node."""
        params = []
        for child in params_node.children:
            if child.type == 'identifier':
                params.append(self._get_node_text(child))
            elif child.type in ['default_parameter', 'typed_parameter', 'typed_default_parameter']:
                # Get the identifier from compound parameter
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        params.append(self._get_node_text(subchild))
                        break
            elif child.type == 'list_splat_pattern':
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        params.append('*' + self._get_node_text(subchild))
                        break
            elif child.type == 'dictionary_splat_pattern':
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        params.append('**' + self._get_node_text(subchild))
                        break

        return params

    def _extract_docstring_from_block(self, block_node: Node) -> Optional[str]:
        """Extract docstring from function/class block."""
        for child in block_node.children:
            if child.type == 'expression_statement':
                for subchild in child.children:
                    if subchild.type == 'string':
                        text = self._get_node_text(subchild)
                        # Remove quotes
                        if text.startswith('"""') or text.startswith("'''"):
                            return text[3:-3].strip()
                        elif text.startswith('"') or text.startswith("'"):
                            return text[1:-1].strip()
                break  # Only check first statement
        return None

    def extract_imports(self) -> List[ImportDef]:
        """Extract all import statements."""
        if not self.tree:
            return []

        imports = []
        for child in self.tree.root_node.children:
            if child.type == 'import_statement':
                import_def = self._parse_import_statement(child)
                if import_def:
                    imports.extend(import_def)
            elif child.type == 'import_from_statement':
                import_def = self._parse_from_import_statement(child)
                if import_def:
                    imports.append(import_def)

        return imports

    def _parse_import_statement(self, node: Node) -> List[ImportDef]:
        """Parse 'import x, y as z' statement."""
        imports = []

        for child in node.children:
            if child.type == 'dotted_name':
                module = self._get_node_text(child)
                imports.append(ImportDef(
                    module=module,
                    line_number=node.start_point[0] + 1,
                    is_from_import=False,
                ))
            elif child.type == 'aliased_import':
                module = None
                alias = None
                for subchild in child.children:
                    if subchild.type == 'dotted_name':
                        module = self._get_node_text(subchild)
                    elif subchild.type == 'identifier':
                        alias = self._get_node_text(subchild)
                if module:
                    imports.append(ImportDef(
                        module=module,
                        alias=alias,
                        line_number=node.start_point[0] + 1,
                        is_from_import=False,
                    ))

        return imports

    def _parse_from_import_statement(self, node: Node) -> Optional[ImportDef]:
        """Parse 'from x import a, b' statement."""
        module = None
        names = []
        seen_import_keyword = False

        for child in node.children:
            if child.type == 'import':
                # This is the 'import' keyword
                seen_import_keyword = True
            elif child.type == 'dotted_name':
                if not seen_import_keyword:
                    # First dotted_name is the module
                    module = self._get_node_text(child)
                else:
                    # Subsequent dotted_names are imported names
                    names.append(self._get_node_text(child))
            elif child.type == 'relative_import':
                module = self._get_node_text(child)
            elif child.type == 'import_prefix':
                # Handle relative imports like "from . import x"
                module = self._get_node_text(child)
            elif child.type == 'identifier' and seen_import_keyword:
                names.append(self._get_node_text(child))
            elif child.type == 'aliased_import':
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        names.append(self._get_node_text(subchild))
                        break
                    elif subchild.type == 'dotted_name':
                        names.append(self._get_node_text(subchild))
                        break
            elif child.type == 'wildcard_import':
                names.append('*')

        if module is not None:
            return ImportDef(
                module=module,
                names=names,
                line_number=node.start_point[0] + 1,
                is_from_import=True,
            )
        return None

    def extract_docstring(self) -> Optional[str]:
        """Extract module-level docstring."""
        if not self.tree:
            return None

        for child in self.tree.root_node.children:
            if child.type == 'expression_statement':
                for subchild in child.children:
                    if subchild.type == 'string':
                        text = self._get_node_text(subchild)
                        if text.startswith('"""') or text.startswith("'''"):
                            return text[3:-3].strip()
                        elif text.startswith('"') or text.startswith("'"):
                            return text[1:-1].strip()
                break  # Only first statement can be docstring
            elif child.type not in ['comment', 'newline']:
                break  # Non-docstring statement found

        return None

    def count_lines(self) -> int:
        """Count lines of code (excluding blank lines and comments)."""
        if not self.source_code:
            return 0

        loc = 0
        for line in self.source_code.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                loc += 1

        return loc
