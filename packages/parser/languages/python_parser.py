from tree_sitter import Language, Node, Query, QueryCursor
from pathlib import Path
import hashlib

from packages.parser.core import BaseLanguageParser
from packages.parser.models import (
    FileNode,
    ClassNode,
    FunctionNode,
    VariableNode,
    DocNode,
    PackageNode,
    TestNode,
    CommitNode,
    GraphData,
    Relationship,
    RelationshipType,
)
from packages.parser.models.nodes import DocType


class PythonParser(BaseLanguageParser):
    """Parser for Python files using tree-sitter"""
    
    @property
    def language_name(self) -> str:
        return "python"
    
    @property
    def file_extensions(self) -> list[str]:
        return [".py", ".pyi"]
    
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
    
    def _extract_classes(self, root_node: Node, content: str, file_node: FileNode, graph_data: GraphData, repo_context: dict):
        """Extract Python class definitions"""
        query = Query(self.language, """
            (class_definition
                name: (identifier) @class.name
                body: (block) @class.body) @class.def
        """)
        
        cursor = QueryCursor(query)
        captures_dict = cursor.captures(root_node)
        # Convert dict format to list of tuples for compatibility
        captures = [(node, name) for name, nodes in captures_dict.items() for node in nodes]
        classes = {}
        
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
                    classes[class_name] = class_node
                    
                    # Create relationship: File CONTAINS_CLASS Class
                    graph_data.add_relationship(Relationship(
                        source_id=file_node.id,
                        target_id=class_id,
                        type=RelationshipType.CONTAINS_CLASS
                    ))
                    
                    # Extract methods within the class
                    self._extract_methods(node, content, file_node, class_node, graph_data, repo_context)
    
    def _extract_methods(self, class_node: Node, content: str, file_node: FileNode, 
                        class_obj: ClassNode, graph_data: GraphData, repo_context: dict):
        """Extract methods from a class"""
        query = Query(self.language, """
            (function_definition
                name: (identifier) @method.name
                parameters: (parameters) @method.params) @method.def
        """)
        
        cursor = QueryCursor(query)
        captures_dict = cursor.captures(class_node)
        captures = [(node, name) for name, nodes in captures_dict.items() for node in nodes]
        
        for node, capture_name in captures:
            if capture_name == "method.def":
                method_name_node = node.child_by_field_name("name")
                params_node = node.child_by_field_name("parameters")
                
                if method_name_node and params_node:
                    method_name = self._get_node_text(method_name_node, content)
                    params = self._get_node_text(params_node, content)
                    signature = f"{method_name}{params}"
                    
                    start_line = self._get_line_number(node)
                    end_line = node.end_point[0] + 1
                    
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
                    
                    # Relationships
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
        """Extract top-level Python functions"""
        # Get only top-level functions (not methods inside classes)
        for child in root_node.children:
            if child.type == "function_definition":
                name_node = child.child_by_field_name("name")
                params_node = child.child_by_field_name("parameters")
                
                if name_node and params_node:
                    func_name = self._get_node_text(name_node, content)
                    params = self._get_node_text(params_node, content)
                    signature = f"{func_name}{params}"
                    
                    start_line = self._get_line_number(child)
                    end_line = child.end_point[0] + 1
                    
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
                    
                    # Relationships
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
        """Extract Python import statements"""
        query = Query(self.language, """
            [
                (import_statement
                    name: (dotted_name) @import.module)
                (import_from_statement
                    module_name: (dotted_name) @import.from)
            ]
        """)
        
        cursor = QueryCursor(query)
        captures_dict = cursor.captures(root_node)
        captures = [(node, name) for name, nodes in captures_dict.items() for node in nodes]
        
        for node, capture_name in captures:
            module_name = self._get_node_text(node, content)
            
            # Create PackageNode for external imports
            package_id = self._generate_id("package", module_name.split('.')[0])
            
            # Check if package already exists
            existing = [n for n in graph_data.nodes if getattr(n, 'id', None) == package_id]
            
            if not existing:
                package_node = PackageNode(
                    id=package_id,
                    name=module_name.split('.')[0],
                    version="unknown",
                )
                graph_data.add_node(package_node)
            
            # Create IMPORTS relationship
            graph_data.add_relationship(Relationship(
                source_id=file_node.id,
                target_id=package_id,
                type=RelationshipType.IMPORTS
            ))
    
    def _extract_variables(self, root_node: Node, content: str, file_node: FileNode, 
                          graph_data: GraphData, repo_context: dict):
        """Extract top-level variable assignments"""
        for child in root_node.children:
            if child.type == "expression_statement":
                # Look for assignments
                assignment = child.child(0)
                if assignment and assignment.type == "assignment":
                    left = assignment.child_by_field_name("left")
                    if left and left.type == "identifier":
                        var_name = self._get_node_text(left, content)
                        start_line = self._get_line_number(child)
                        
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
    
    def _extract_docs(self, root_node: Node, content: str, file_node: FileNode, 
                     graph_data: GraphData, repo_context: dict):
        """Extract Python docstrings and comments"""
        query = Query(self.language, """
            [
                (expression_statement (string) @docstring)
                (comment) @comment
            ]
        """)
        
        cursor = QueryCursor(query)
        captures_dict = cursor.captures(root_node)
        captures = [(node, name) for name, nodes in captures_dict.items() for node in nodes]
        
        for node, capture_name in captures:
            doc_text = self._get_node_text(node, content)
            start_line = self._get_line_number(node)
            
            doc_type = DocType.DOCSTRING if capture_name == "docstring" else DocType.COMMENT
            
            doc_id = self._generate_id(
                repo_context["name"],
                str(file_node.path),
                "doc",
                str(start_line)
            )
            
            doc_node = DocNode(
                id=doc_id,
                type=doc_type,
                text=doc_text.strip(),
                start_line=start_line,
                source_path=file_node.path,
                repo_sha=repo_context.get("sha"),
                commit_hash=repo_context.get("commit_hash"),
            )
            
            graph_data.add_node(doc_node)
            
            graph_data.add_relationship(Relationship(
                source_id=file_node.id,
                target_id=doc_id,
                type=RelationshipType.HAS_DOC
            ))
    
    def _extract_tests(self, root_node: Node, content: str, file_node: FileNode, 
                      graph_data: GraphData, repo_context: dict):
        """Extract Python test functions (pytest, unittest)"""
        from packages.parser.utils.file_utils import is_test_file
        from pathlib import Path
        
        # Only extract tests if this is a test file
        if not is_test_file(Path(file_node.path)):
            return
        
        # Look for test functions (test_*, Test* classes)
        query = Query(self.language, """
            [
                (function_definition
                    name: (identifier) @test.name) @test.func
                (class_definition
                    name: (identifier) @test.class) @test.cls
            ]
        """)
        
        cursor = QueryCursor(query)
        captures_dict = cursor.captures(root_node)
        captures = [(node, name) for name, nodes in captures_dict.items() for node in nodes]
        
        for node, capture_name in captures:
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue
            
            name = self._get_node_text(name_node, content)
            
            # Check if it's a test (starts with 'test' or 'Test')
            if not (name.startswith('test_') or name.startswith('Test')):
                continue
            
            start_line = self._get_line_number(node)
            
            # Determine test kind
            if capture_name in ["test.func", "test.name"]:
                kind = "unit"  # Function-based test
            else:
                kind = "class"  # Class-based test
            
            test_id = self._generate_id(
                repo_context["name"],
                str(file_node.path),
                "test",
                name
            )
            
            test_node = TestNode(
                id=test_id,
                name=name,
                kind=kind,
                source_path=file_node.path,
                repo_sha=repo_context.get("sha"),
                commit_hash=repo_context.get("commit_hash"),
            )
            
            graph_data.add_node(test_node)
            
            # Create relationship: File HAS_TEST Test
            graph_data.add_relationship(Relationship(
                source_id=file_node.id,
                target_id=test_id,
                type=RelationshipType.HAS_TEST
            ))
    
    def _extract_commits(self, file_path: Path, file_node: FileNode, 
                        graph_data: GraphData, repo_context: dict):
        """Extract commit information for the file"""
        from packages.parser.utils.git_commit_utils import get_last_commit_for_file
        from datetime import datetime
        
        # Get repo path from context
        repo_path_str = repo_context.get("path")
        if not repo_path_str:
            return
        
        repo_path = Path(repo_path_str)
        
        # Get last commit
        commit_info = get_last_commit_for_file(repo_path, file_path)
        
        if not commit_info:
            return
        
        # Create CommitNode
        commit_id = self._generate_id(
            repo_context["name"],
            "commit",
            commit_info['hash']
        )
        
        # Parse date
        try:
            commit_date = datetime.fromisoformat(commit_info['date'].replace('Z', '+00:00'))
        except:
            commit_date = datetime.utcnow()
        
        commit_node = CommitNode(
            id=commit_id,
            hash=commit_info['hash'],
            author=commit_info['author'],
            email=commit_info['email'],
            date=commit_date,
            message=commit_info['message'],
            repo_sha=repo_context.get("sha"),
        )
        
        # Check if commit already exists
        existing = [n for n in graph_data.nodes if getattr(n, 'id', None) == commit_id]
        
        if not existing:
            graph_data.add_node(commit_node)
        
        # Create relationship: Commit TOUCHED File
        graph_data.add_relationship(Relationship(
            source_id=commit_id,
            target_id=file_node.id,
            type=RelationshipType.TOUCHED
        ))
