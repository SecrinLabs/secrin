from tree_sitter import Language, Node, Query, QueryCursor
from pathlib import Path
import hashlib

from packages.parser.core import BaseLanguageParser
from packages.parser.models import (
    FileNode,
    ClassNode,
    FunctionNode,
    VariableNode,
    PackageNode,
    GraphData,
    Relationship,
    RelationshipType,
)


class TypeScriptParser(BaseLanguageParser):
    """Parser for TypeScript files using tree-sitter"""
    
    @property
    def language_name(self) -> str:
        return "typescript"
    
    @property
    def file_extensions(self) -> list[str]:
        return [".ts", ".tsx"]
    
    def _create_file_node(self, file_path: Path, content: str, repo_context: dict) -> FileNode:
        lines = len(content.split('\n'))
        sha = hashlib.sha256(content.encode()).hexdigest()
        
        return FileNode(
            id=self._generate_id(repo_context["name"], str(file_path), "file"),
            path=str(file_path),
            language=self.language_name,
            sha=sha,
            lines=lines,
            source_path=str(file_path),
            repo_sha=repo_context.get("sha"),
            commit_hash=repo_context.get("commit_hash"),
        )
    
    def _extract_classes(self, root_node: Node, content: str, file_node: FileNode, 
                        graph_data: GraphData, repo_context: dict):
        """Extract TypeScript class definitions"""
        # TypeScript classes are similar to JS but can have decorators, implements, etc.
        query = Query(self.language, """
            (class_declaration
                name: (type_identifier) @class.name
                body: (class_body) @class.body) @class.def
        """)
        
        cursor = QueryCursor(query)
        captures_dict = cursor.captures(root_node)
        captures = [(node, name) for name, nodes in captures_dict.items() for node in nodes]
        
        for node, capture_name in captures:
            if capture_name == "class.def":
                class_name_node = node.child_by_field_name("name")
                if class_name_node:
                    class_name = self._get_node_text(class_name_node, content)
                    start_line = self._get_line_number(node)
                    end_line = node.end_point[0] + 1
                    
                    class_id = self._generate_id(
                        repo_context["name"],
                        str(file_node.path),
                        "class",
                        class_name
                    )
                    
                    class_node = ClassNode(
                        id=class_id,
                        name=class_name,
                        start_line=start_line,
                        end_line=end_line,
                        source_path=file_node.path,
                        repo_sha=repo_context.get("sha"),
                        commit_hash=repo_context.get("commit_hash"),
                        snippet=self._get_snippet(content, start_line, end_line),
                    )
                    
                    graph_data.add_node(class_node)
                    
                    graph_data.add_relationship(Relationship(
                        source_id=file_node.id,
                        target_id=class_id,
                        type=RelationshipType.CONTAINS_CLASS
                    ))
                    
                    # Extract methods
                    self._extract_methods(node, content, file_node, class_node, graph_data, repo_context)
    
    def _extract_methods(self, class_node: Node, content: str, file_node: FileNode,
                        class_obj: ClassNode, graph_data: GraphData, repo_context: dict):
        """Extract methods from a TypeScript class"""
        body = class_node.child_by_field_name("body")
        if not body:
            return
        
        for child in body.children:
            if child.type == "method_definition":
                name_node = child.child_by_field_name("name")
                params_node = child.child_by_field_name("parameters")
                
                if name_node and params_node:
                    method_name = self._get_node_text(name_node, content)
                    params = self._get_node_text(params_node, content)
                    signature = f"{method_name}{params}"
                    
                    start_line = self._get_line_number(child)
                    end_line = child.end_point[0] + 1
                    
                    method_id = self._generate_id(
                        repo_context["name"],
                        str(file_node.path),
                        "method",
                        class_obj.name,
                        method_name
                    )
                    
                    method_node = FunctionNode(
                        id=method_id,
                        name=method_name,
                        signature=signature,
                        start_line=start_line,
                        end_line=end_line,
                        is_method=True,
                        source_path=file_node.path,
                        repo_sha=repo_context.get("sha"),
                        commit_hash=repo_context.get("commit_hash"),
                        snippet=self._get_snippet(content, start_line, end_line),
                    )
                    
                    graph_data.add_node(method_node)
                    
                    graph_data.add_relationship(Relationship(
                        source_id=class_obj.id,
                        target_id=method_id,
                        type=RelationshipType.HAS_METHOD
                    ))
                    
                    graph_data.add_relationship(Relationship(
                        source_id=method_id,
                        target_id=file_node.id,
                        type=RelationshipType.DEFINED_IN
                    ))
    
    def _extract_functions(self, root_node: Node, content: str, file_node: FileNode,
                          graph_data: GraphData, repo_context: dict):
        """Extract top-level TypeScript functions"""
        query = Query(self.language, """
            [
                (function_declaration
                    name: (identifier) @func.name
                    parameters: (formal_parameters) @func.params) @func.def
                (variable_declarator
                    name: (identifier) @arrow.name
                    value: (arrow_function) @arrow.func)
            ]
        """)
        
        cursor = QueryCursor(query)
        captures_dict = cursor.captures(root_node)
        captures = [(node, name) for name, nodes in captures_dict.items() for node in nodes]
        processed_funcs = set()
        
        for node, capture_name in captures:
            if capture_name == "func.def":
                name_node = node.child_by_field_name("name")
                params_node = node.child_by_field_name("parameters")
                
                if name_node and params_node:
                    func_name = self._get_node_text(name_node, content)
                    
                    if func_name in processed_funcs:
                        continue
                    processed_funcs.add(func_name)
                    
                    params = self._get_node_text(params_node, content)
                    signature = f"{func_name}{params}"
                    
                    start_line = self._get_line_number(node)
                    end_line = node.end_point[0] + 1
                    
                    func_id = self._generate_id(
                        repo_context["name"],
                        str(file_node.path),
                        "function",
                        func_name
                    )
                    
                    func_node = FunctionNode(
                        id=func_id,
                        name=func_name,
                        signature=signature,
                        start_line=start_line,
                        end_line=end_line,
                        is_method=False,
                        source_path=file_node.path,
                        repo_sha=repo_context.get("sha"),
                        commit_hash=repo_context.get("commit_hash"),
                        snippet=self._get_snippet(content, start_line, end_line),
                    )
                    
                    graph_data.add_node(func_node)
                    
                    graph_data.add_relationship(Relationship(
                        source_id=file_node.id,
                        target_id=func_id,
                        type=RelationshipType.CONTAINS_FUNCTION
                    ))
                    
                    graph_data.add_relationship(Relationship(
                        source_id=func_id,
                        target_id=file_node.id,
                        type=RelationshipType.DEFINED_IN
                    ))
    
    def _extract_imports(self, root_node: Node, content: str, file_node: FileNode,
                        graph_data: GraphData, repo_context: dict):
        """Extract TypeScript import statements"""
        query = Query(self.language, """
            [
                (import_statement
                    source: (string) @import.source)
            ]
        """)
        
        cursor = QueryCursor(query)
        captures_dict = cursor.captures(root_node)
        captures = [(node, name) for name, nodes in captures_dict.items() for node in nodes]
        
        for node, capture_name in captures:
            if capture_name == "import.source":
                import_path = self._get_node_text(node, content).strip('"').strip("'")
                
                # Extract package name (handle @scoped packages)
                if import_path.startswith('@'):
                    parts = import_path.split('/')
                    package_name = '/'.join(parts[:2]) if len(parts) >= 2 else import_path
                elif import_path.startswith('.'):
                    # Relative import - skip for now or handle differently
                    continue
                else:
                    package_name = import_path.split('/')[0]
                
                package_id = self._generate_id("package", package_name)
                
                # Check if package already exists
                existing = [n for n in graph_data.nodes if getattr(n, 'id', None) == package_id]
                
                if not existing:
                    package_node = PackageNode(
                        id=package_id,
                        name=package_name,
                        version="unknown",
                    )
                    graph_data.add_node(package_node)
                
                graph_data.add_relationship(Relationship(
                    source_id=file_node.id,
                    target_id=package_id,
                    type=RelationshipType.IMPORTS
                ))
    
    def _extract_variables(self, root_node: Node, content: str, file_node: FileNode,
                          graph_data: GraphData, repo_context: dict):
        """Extract top-level variable declarations"""
        query = Query(self.language, """
            (variable_declaration
                (variable_declarator
                    name: (identifier) @var.name)) @var.decl
        """)
        
        cursor = QueryCursor(query)
        captures_dict = cursor.captures(root_node)
        captures = [(node, name) for name, nodes in captures_dict.items() for node in nodes]
        
        for node, capture_name in captures:
            if capture_name == "var.name":
                var_name = self._get_node_text(node, content)
                start_line = self._get_line_number(node)
                
                var_id = self._generate_id(
                    repo_context["name"],
                    str(file_node.path),
                    "variable",
                    var_name,
                    str(start_line)
                )
                
                var_node = VariableNode(
                    id=var_id,
                    name=var_name,
                    kind="global",
                    start_line=start_line,
                    source_path=file_node.path,
                    repo_sha=repo_context.get("sha"),
                    commit_hash=repo_context.get("commit_hash"),
                )
                
                graph_data.add_node(var_node)
