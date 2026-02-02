"""
JavaScript AST parser using tree-sitter.
"""

import logging
from typing import List, Optional

import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser, Node

from .base import BaseLanguageParser
from ..models.analysis import ClassDef, FunctionDef, ImportDef


logger = logging.getLogger(__name__)


class JavaScriptParser(BaseLanguageParser):
    """
    JavaScript AST parser using tree-sitter.

    Extracts:
    - Class definitions with methods
    - Function definitions (regular, arrow, async)
    - Import statements (ES6 imports, require)
    - Export statements
    """

    def __init__(self):
        """Initialize the JavaScript parser."""
        self.JS_LANGUAGE = Language(tsjavascript.language())
        self.parser = Parser(self.JS_LANGUAGE)
        self.tree = None
        self.source_code = ""
        self._source_bytes = b""

    def parse(self, source_code: str) -> None:
        """
        Parse JavaScript source code.

        Args:
            source_code: JavaScript source code string
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

    def _extract_classes_recursive(self, node: Node, classes: List[ClassDef]) -> None:
        """Recursively extract class definitions."""
        if node.type == 'class_declaration' or node.type == 'class':
            class_def = self._parse_class_node(node)
            if class_def:
                classes.append(class_def)
            return

        for child in node.children:
            self._extract_classes_recursive(child, classes)

    def _parse_class_node(self, node: Node) -> Optional[ClassDef]:
        """Parse a class declaration node."""
        name = None
        bases = []
        methods = []
        decorators = []

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child)
            elif child.type == 'class_heritage':
                # Extract extends clause
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        bases.append(self._get_node_text(subchild))
                    elif subchild.type == 'member_expression':
                        bases.append(self._get_node_text(subchild))
            elif child.type == 'class_body':
                methods = self._extract_class_methods(child)
            elif child.type == 'decorator':
                decorators.append(self._get_node_text(child).lstrip('@'))

        if name:
            return ClassDef(
                name=name,
                line_number=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                methods=methods,
                bases=bases,
                decorators=decorators,
            )
        return None

    def _extract_class_methods(self, class_body: Node) -> List[str]:
        """Extract method names from class body."""
        methods = []

        for child in class_body.children:
            if child.type == 'method_definition':
                for subchild in child.children:
                    if subchild.type == 'property_identifier':
                        methods.append(self._get_node_text(subchild))
                        break
            elif child.type == 'field_definition':
                # Handle class fields that are arrow functions
                for subchild in child.children:
                    if subchild.type == 'property_identifier':
                        methods.append(self._get_node_text(subchild))
                        break

        return methods

    def extract_functions(self) -> List[FunctionDef]:
        """Extract module-level function definitions."""
        if not self.tree:
            return []

        functions = []
        self._extract_functions_from_node(self.tree.root_node, functions)
        return functions

    def _extract_functions_from_node(self, node: Node, functions: List[FunctionDef]) -> None:
        """Extract functions from a node."""
        # Function declaration: function foo() {}
        if node.type == 'function_declaration':
            func_def = self._parse_function_node(node)
            if func_def:
                functions.append(func_def)
            return

        # Variable declaration with function: const foo = function() {} or const foo = () => {}
        if node.type == 'lexical_declaration' or node.type == 'variable_declaration':
            for child in node.children:
                if child.type == 'variable_declarator':
                    func_def = self._parse_variable_function(child)
                    if func_def:
                        functions.append(func_def)
            return

        # Export default function
        if node.type == 'export_statement':
            for child in node.children:
                if child.type == 'function_declaration':
                    func_def = self._parse_function_node(child)
                    if func_def:
                        functions.append(func_def)

        # Recurse into children (but not into class bodies or function bodies)
        if node.type not in ['class_body', 'function_body', 'statement_block']:
            for child in node.children:
                self._extract_functions_from_node(child, functions)

    def _parse_function_node(self, node: Node) -> Optional[FunctionDef]:
        """Parse a function declaration node."""
        name = None
        parameters = []
        is_async = False

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child)
            elif child.type == 'formal_parameters':
                parameters = self._extract_parameters(child)
            elif child.type == 'async':
                is_async = True

        if name:
            return FunctionDef(
                name=name,
                line_number=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                parameters=parameters,
                is_async=is_async,
            )
        return None

    def _parse_variable_function(self, node: Node) -> Optional[FunctionDef]:
        """Parse a variable declaration that contains a function."""
        name = None
        parameters = []
        is_async = False

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child)
            elif child.type in ['function', 'arrow_function']:
                for subchild in child.children:
                    if subchild.type == 'formal_parameters':
                        parameters = self._extract_parameters(subchild)
                    elif subchild.type == 'identifier':
                        # Single parameter arrow function: x => x
                        parameters = [self._get_node_text(subchild)]
                    elif subchild.type == 'async':
                        is_async = True

        if name:
            return FunctionDef(
                name=name,
                line_number=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                parameters=parameters,
                is_async=is_async,
            )
        return None

    def _extract_parameters(self, params_node: Node) -> List[str]:
        """Extract parameter names from formal_parameters node."""
        params = []

        for child in params_node.children:
            if child.type == 'identifier':
                params.append(self._get_node_text(child))
            elif child.type == 'assignment_pattern':
                # Default parameter: x = 10
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        params.append(self._get_node_text(subchild))
                        break
            elif child.type == 'rest_pattern':
                # Rest parameter: ...args
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        params.append('...' + self._get_node_text(subchild))
                        break
            elif child.type == 'object_pattern':
                # Destructuring: { a, b }
                params.append('{...}')
            elif child.type == 'array_pattern':
                # Destructuring: [a, b]
                params.append('[...]')

        return params

    def extract_imports(self) -> List[ImportDef]:
        """Extract all import statements."""
        if not self.tree:
            return []

        imports = []
        self._extract_imports_recursive(self.tree.root_node, imports)
        return imports

    def _extract_imports_recursive(self, node: Node, imports: List[ImportDef]) -> None:
        """Recursively extract import statements."""
        # ES6 import: import x from 'module'
        if node.type == 'import_statement':
            import_def = self._parse_import_statement(node)
            if import_def:
                imports.append(import_def)
            return

        # CommonJS require: const x = require('module')
        if node.type == 'lexical_declaration' or node.type == 'variable_declaration':
            for child in node.children:
                if child.type == 'variable_declarator':
                    import_def = self._parse_require_statement(child, node)
                    if import_def:
                        imports.append(import_def)
            return

        for child in node.children:
            self._extract_imports_recursive(child, imports)

    def _parse_import_statement(self, node: Node) -> Optional[ImportDef]:
        """Parse ES6 import statement."""
        module = None
        names = []

        for child in node.children:
            if child.type == 'string':
                # Module path
                module = self._get_node_text(child).strip('"\'')
            elif child.type == 'import_clause':
                names = self._extract_import_names(child)

        if module:
            return ImportDef(
                module=module,
                names=names,
                line_number=node.start_point[0] + 1,
                is_from_import=True,
            )
        return None

    def _extract_import_names(self, clause_node: Node) -> List[str]:
        """Extract imported names from import clause."""
        names = []

        for child in clause_node.children:
            if child.type == 'identifier':
                # Default import
                names.append(self._get_node_text(child))
            elif child.type == 'namespace_import':
                # import * as name
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        names.append('* as ' + self._get_node_text(subchild))
            elif child.type == 'named_imports':
                # import { a, b }
                for subchild in child.children:
                    if subchild.type == 'import_specifier':
                        for spec_child in subchild.children:
                            if spec_child.type == 'identifier':
                                names.append(self._get_node_text(spec_child))
                                break

        return names

    def _parse_require_statement(self, node: Node, parent: Node) -> Optional[ImportDef]:
        """Parse CommonJS require statement."""
        name = None
        module = None

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child)
            elif child.type == 'call_expression':
                # Check if it's a require() call
                func_name = None
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        func_name = self._get_node_text(subchild)
                    elif subchild.type == 'arguments':
                        for arg in subchild.children:
                            if arg.type == 'string':
                                module = self._get_node_text(arg).strip('"\'')

                if func_name != 'require':
                    return None

        if module:
            return ImportDef(
                module=module,
                names=[name] if name else [],
                line_number=parent.start_point[0] + 1,
                is_from_import=False,
            )
        return None

    def extract_docstring(self) -> Optional[str]:
        """Extract module-level JSDoc comment."""
        if not self.tree:
            return None

        # Look for leading comment
        for child in self.tree.root_node.children:
            if child.type == 'comment':
                text = self._get_node_text(child)
                if text.startswith('/**'):
                    # JSDoc comment
                    return text[3:-2].strip()
                elif text.startswith('/*'):
                    return text[2:-2].strip()
            elif child.type not in ['comment']:
                break

        return None

    def count_lines(self) -> int:
        """Count lines of code (excluding blank lines and comments)."""
        if not self.source_code:
            return 0

        loc = 0
        in_multiline_comment = False

        for line in self.source_code.split('\n'):
            stripped = line.strip()

            # Handle multiline comments
            if '/*' in stripped and '*/' not in stripped:
                in_multiline_comment = True
                continue
            if '*/' in stripped:
                in_multiline_comment = False
                continue
            if in_multiline_comment:
                continue

            # Skip empty lines and single-line comments
            if stripped and not stripped.startswith('//'):
                loc += 1

        return loc
