"""
Code analysis result models.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ClassDef:
    """Represents a class definition."""
    name: str
    line_number: int
    end_line: int = 0
    docstring: Optional[str] = None
    methods: List[str] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)


@dataclass
class FunctionDef:
    """Represents a function definition."""
    name: str
    line_number: int
    end_line: int = 0
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False


@dataclass
class ImportDef:
    """Represents an import statement."""
    module: str
    names: List[str] = field(default_factory=list)  # For 'from x import a, b'
    alias: Optional[str] = None
    is_from_import: bool = False
    line_number: int = 0


@dataclass
class Module:
    """Represents a code module (package, directory, or file)."""
    name: str
    path: str
    type: str  # 'package', 'directory', 'file'
    children: List['Module'] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    size_loc: int = 0
    classes: List[ClassDef] = field(default_factory=list)
    functions: List[FunctionDef] = field(default_factory=list)
    imports: List[ImportDef] = field(default_factory=list)
    docstring: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "path": self.path,
            "type": self.type,
            "children": [c.to_dict() for c in self.children],
            "dependencies": self.dependencies,
            "interfaces": self.interfaces,
            "size_loc": self.size_loc,
            "classes": [
                {
                    "name": c.name,
                    "line": c.line_number,
                    "methods": c.methods,
                    "bases": c.bases,
                }
                for c in self.classes
            ],
            "functions": [
                {
                    "name": f.name,
                    "line": f.line_number,
                    "parameters": f.parameters,
                }
                for f in self.functions
            ],
            "imports": [
                {
                    "module": i.module,
                    "names": i.names,
                }
                for i in self.imports
            ],
        }

    def get_public_interfaces(self) -> List[str]:
        """Get list of public interfaces (classes and functions not starting with _)."""
        interfaces = []
        for cls in self.classes:
            if not cls.name.startswith('_'):
                interfaces.append(f"class {cls.name}")
        for func in self.functions:
            if not func.name.startswith('_'):
                interfaces.append(f"def {func.name}")
        return interfaces


@dataclass
class Dependency:
    """Represents a dependency relationship."""
    from_module: str
    to_module: str
    type: str  # 'import', 'call', 'inherit'

    def to_dict(self) -> Dict:
        return {
            "from": self.from_module,
            "to": self.to_module,
            "type": self.type,
        }


@dataclass
class CodeStatistics:
    """Code statistics."""
    total_loc: int = 0
    total_files: int = 0
    total_modules: int = 0
    total_classes: int = 0
    total_functions: int = 0

    def to_dict(self) -> Dict:
        return {
            "total_loc": self.total_loc,
            "total_files": self.total_files,
            "total_modules": self.total_modules,
            "total_classes": self.total_classes,
            "total_functions": self.total_functions,
        }


@dataclass
class ModuleTree:
    """Tree structure of modules."""
    root: Module

    def get_all_modules(self) -> List[Module]:
        """Flatten tree to list of all modules."""
        modules = []
        self._collect_modules(self.root, modules)
        return modules

    def _collect_modules(self, module: Module, result: List[Module]) -> None:
        result.append(module)
        for child in module.children:
            self._collect_modules(child, result)

    def get_top_level_modules(self) -> List[Module]:
        """Get direct children of root."""
        return self.root.children


@dataclass
class DependencyGraph:
    """Dependency graph."""
    nodes: List[str] = field(default_factory=list)
    edges: List[Dependency] = field(default_factory=list)

    def add_dependency(self, from_module: str, to_module: str, dep_type: str = "import") -> None:
        """Add a dependency edge."""
        if from_module not in self.nodes:
            self.nodes.append(from_module)
        if to_module not in self.nodes:
            self.nodes.append(to_module)

        # Avoid duplicates
        for edge in self.edges:
            if edge.from_module == from_module and edge.to_module == to_module:
                return

        self.edges.append(Dependency(from_module, to_module, dep_type))

    def get_dependencies_for(self, module: str) -> List[str]:
        """Get all modules that the given module depends on."""
        return [e.to_module for e in self.edges if e.from_module == module]

    def get_dependents_of(self, module: str) -> List[str]:
        """Get all modules that depend on the given module."""
        return [e.from_module for e in self.edges if e.to_module == module]

    def to_dict(self) -> Dict:
        return {
            "nodes": self.nodes,
            "edges": [e.to_dict() for e in self.edges],
        }


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    repo_name: str
    language: str
    module_tree: ModuleTree
    dependency_graph: DependencyGraph
    statistics: CodeStatistics
    repo_path: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "repo_name": self.repo_name,
            "repo_path": self.repo_path,
            "language": self.language,
            "module_tree": self.module_tree.root.to_dict(),
            "dependency_graph": self.dependency_graph.to_dict(),
            "statistics": self.statistics.to_dict(),
        }

    def get_summary(self) -> str:
        """Get human-readable summary of analysis."""
        stats = self.statistics
        return (
            f"Repository: {self.repo_name}\n"
            f"Language: {self.language}\n"
            f"Files: {stats.total_files}\n"
            f"Modules: {stats.total_modules}\n"
            f"Classes: {stats.total_classes}\n"
            f"Functions: {stats.total_functions}\n"
            f"Total LOC: {stats.total_loc}"
        )
