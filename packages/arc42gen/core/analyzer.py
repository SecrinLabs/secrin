"""
Codebase analysis using tree-sitter.
"""

import logging
import fnmatch
from pathlib import Path
from typing import List, Optional, Set, Dict

from ..models.config import Config
from ..models.analysis import (
    AnalysisResult,
    Module,
    ModuleTree,
    DependencyGraph,
    CodeStatistics,
    Dependency,
)
from ..parsers.base import BaseLanguageParser
from ..parsers.python_parser import PythonParser
from ..parsers.javascript_parser import JavaScriptParser
from ..parsers.typescript_parser import TypeScriptParser
from ..utils.git_utils import is_remote_url, clone_repository, cleanup_cloned_repo
from ..constants import EXTENSION_TO_LANGUAGE, DEFAULT_LANGUAGE


logger = logging.getLogger(__name__)


class CodebaseAnalyzer:
    """
    Analyzes codebase structure using static analysis.

    Implements hierarchical decomposition:
    1. Directory-based clustering
    2. LOC-based decomposition for large modules
    3. Dependency graph construction

    Supports multiple languages:
    - Python (.py)
    - JavaScript (.js, .jsx, .mjs, .cjs)
    - TypeScript (.ts, .tsx, .mts, .cts)
    """

    def __init__(self, config: Config):
        """
        Initialize the analyzer.

        Args:
            config: Configuration object
        """
        self.config = config
        self._statistics = CodeStatistics()
        self._detected_language = None

        # Initialize parsers for each supported language
        self._parsers: Dict[str, BaseLanguageParser] = {
            "python": PythonParser(),
            "javascript": JavaScriptParser(),
            "typescript": TypeScriptParser(tsx=False),
            "typescript_tsx": TypeScriptParser(tsx=True),
        }

    def _get_parser_for_file(self, file_path: Path) -> Optional[BaseLanguageParser]:
        """
        Get the appropriate parser for a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            Parser instance or None if unsupported
        """
        ext = file_path.suffix.lower()
        language = EXTENSION_TO_LANGUAGE.get(ext)

        if not language:
            return None

        # Handle TSX files specially
        if ext == ".tsx":
            return self._parsers.get("typescript_tsx")

        return self._parsers.get(language)

    def _detect_primary_language(self, files: List[Path]) -> str:
        """
        Detect the primary language of a repository based on file counts.

        Args:
            files: List of file paths

        Returns:
            Primary language name
        """
        language_counts: Dict[str, int] = {}

        for file_path in files:
            ext = file_path.suffix.lower()
            language = EXTENSION_TO_LANGUAGE.get(ext)
            if language:
                language_counts[language] = language_counts.get(language, 0) + 1

        if not language_counts:
            return DEFAULT_LANGUAGE  # Default fallback

        # Return language with most files
        return max(language_counts, key=language_counts.get)

    def analyze(self, repo_path: str) -> AnalysisResult:
        """
        Main analysis entry point.

        Args:
            repo_path: Path to repository (local path or remote URL)

        Returns:
            AnalysisResult with module tree, dependencies, statistics
        """
        logger.info(f"Starting analysis of: {repo_path}")

        # Handle remote URLs
        cloned_path = None
        if is_remote_url(repo_path):
            logger.info(f"Detected remote URL, cloning repository...")
            cloned_path = clone_repository(repo_path)
            actual_path = cloned_path
        else:
            actual_path = Path(repo_path).resolve()
            if not actual_path.exists():
                raise FileNotFoundError(f"Repository path not found: {repo_path}")

        try:
            result = self._analyze_local(actual_path)
            return result
        finally:
            # Clean up cloned repo if it was temporary
            if cloned_path:
                cleanup_cloned_repo(cloned_path)

    def _analyze_local(self, repo_path: Path) -> AnalysisResult:
        """
        Analyze a local repository path.

        Args:
            repo_path: Local path to repository

        Returns:
            AnalysisResult
        """
        # Reset statistics
        self._statistics = CodeStatistics()

        # Get all matching files first for language detection
        matching_files = self._get_matching_files(repo_path)
        logger.debug(f"Found {len(matching_files)} matching files")

        # Determine language
        configured_language = self.config.repository.language
        if configured_language == "auto" or not configured_language:
            self._detected_language = self._detect_primary_language(matching_files)
            logger.info(f"Auto-detected primary language: {self._detected_language}")
        else:
            self._detected_language = configured_language

        # Build module tree with hierarchical decomposition
        root_module = self._decompose_repository(repo_path, matching_files)

        # Build dependency graph
        dependency_graph = self._build_dependency_graph(root_module)

        # Create module tree
        module_tree = ModuleTree(root=root_module)

        # Count modules
        self._statistics.total_modules = len(module_tree.get_all_modules())

        logger.info(
            f"Analysis complete: {self._statistics.total_files} files, "
            f"{self._statistics.total_loc} LOC, "
            f"{self._statistics.total_classes} classes, "
            f"{self._statistics.total_functions} functions"
        )

        return AnalysisResult(
            repo_name=repo_path.name,
            repo_path=str(repo_path),
            language=self._detected_language,
            module_tree=module_tree,
            dependency_graph=dependency_graph,
            statistics=self._statistics,
        )

    def _decompose_repository(
        self, root_path: Path, matching_files: Optional[List[Path]] = None
    ) -> Module:
        """
        Hierarchical decomposition of repository.

        Strategy:
        1. Start with directory structure as initial grouping
        2. For large directories, decompose into submodules
        3. Build dependency links between modules

        Args:
            root_path: Root path of the repository
            matching_files: Pre-computed list of matching files (optional)
        """
        root_module = Module(
            name=root_path.name,
            path=str(root_path),
            type="package",
            children=[],
            size_loc=0,
        )

        # Get all matching files if not provided
        if matching_files is None:
            matching_files = self._get_matching_files(root_path)
            logger.debug(f"Found {len(matching_files)} matching files")

        # Group files by top-level directory
        directory_groups = self._group_by_directory(root_path, matching_files)

        # Process each directory group
        for dir_name, files in sorted(directory_groups.items()):
            if dir_name == ".":
                # Root-level files
                for file_path in files:
                    file_module = self._analyze_file(file_path)
                    if file_module:
                        root_module.children.append(file_module)
                        root_module.size_loc += file_module.size_loc
            else:
                # Directory module
                dir_path = root_path / dir_name
                dir_module = self._analyze_directory(dir_path, files)
                if dir_module and (dir_module.children or dir_module.size_loc > 0):
                    root_module.children.append(dir_module)
                    root_module.size_loc += dir_module.size_loc

        return root_module

    def _get_matching_files(self, root_path: Path) -> List[Path]:
        """Get all files matching include/exclude patterns."""
        matching_files = []

        for pattern in self.config.repository.include:
            for file_path in root_path.glob(pattern):
                if file_path.is_file():
                    # Check exclusions
                    rel_path = str(file_path.relative_to(root_path))
                    if not self._is_excluded(rel_path):
                        matching_files.append(file_path)

        return list(set(matching_files))  # Remove duplicates

    def _is_excluded(self, rel_path: str) -> bool:
        """Check if path matches any exclusion pattern."""
        from pathlib import PurePath

        path = PurePath(rel_path)

        for pattern in self.config.repository.exclude:
            # Use PurePath.match for glob-style matching with ** support
            if path.match(pattern):
                return True
            # Also try matching individual path parts for patterns like "**/tests/**"
            # Split pattern on **
            if '**' in pattern:
                # Check if any part of the path matches
                pattern_part = pattern.replace('**/', '').replace('/**', '').replace('**', '')
                for part in path.parts:
                    if fnmatch.fnmatch(part, pattern_part.strip('/')):
                        return True
        return False

    def _group_by_directory(self, root_path: Path, files: List[Path]) -> dict:
        """Group files by their top-level directory."""
        groups = {}

        for file_path in files:
            rel_path = file_path.relative_to(root_path)
            parts = rel_path.parts

            if len(parts) == 1:
                # Root-level file
                key = "."
            else:
                # Use first directory
                key = parts[0]

            if key not in groups:
                groups[key] = []
            groups[key].append(file_path)

        return groups

    def _analyze_directory(self, dir_path: Path, files: List[Path]) -> Module:
        """
        Analyze a directory and create a Module.

        If the directory is too large (exceeds max_module_size),
        it will be decomposed further.
        """
        dir_module = Module(
            name=dir_path.name,
            path=str(dir_path),
            type="package" if (dir_path / "__init__.py").exists() else "directory",
            children=[],
            size_loc=0,
        )

        # Group files by subdirectory
        subdir_groups = {}
        root_files = []

        for file_path in files:
            try:
                rel_path = file_path.relative_to(dir_path)
                parts = rel_path.parts

                if len(parts) == 1:
                    root_files.append(file_path)
                else:
                    subdir = parts[0]
                    if subdir not in subdir_groups:
                        subdir_groups[subdir] = []
                    subdir_groups[subdir].append(file_path)
            except ValueError:
                # File not under this directory
                continue

        # Process root files
        for file_path in root_files:
            file_module = self._analyze_file(file_path)
            if file_module:
                dir_module.children.append(file_module)
                dir_module.size_loc += file_module.size_loc

        # Process subdirectories
        for subdir_name, subdir_files in sorted(subdir_groups.items()):
            subdir_path = dir_path / subdir_name
            subdir_module = self._analyze_directory(subdir_path, subdir_files)
            if subdir_module and (subdir_module.children or subdir_module.size_loc > 0):
                dir_module.children.append(subdir_module)
                dir_module.size_loc += subdir_module.size_loc

        # Check if module should be decomposed further
        max_size = self.config.decomposition.max_module_size
        if dir_module.size_loc > max_size and len(dir_module.children) <= 1:
            logger.debug(f"Module {dir_module.name} exceeds {max_size} LOC, decomposing...")
            # Decomposition already happens through recursion

        # Aggregate interfaces and dependencies
        dir_module.interfaces = self._aggregate_interfaces(dir_module)
        dir_module.dependencies = self._aggregate_dependencies(dir_module)

        return dir_module

    def _analyze_file(self, file_path: Path) -> Optional[Module]:
        """
        Analyze a single source file.

        Supports Python, JavaScript, and TypeScript files.
        """
        # Get the appropriate parser
        parser = self._get_parser_for_file(file_path)
        if not parser:
            logger.debug(f"No parser available for file: {file_path}")
            return None

        try:
            source_code = file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return None

        # Parse the file
        try:
            parser.parse(source_code)
        except Exception as e:
            logger.warning(f"Could not parse file {file_path}: {e}")
            return None

        # Extract information
        classes = parser.extract_classes()
        functions = parser.extract_functions()
        imports = parser.extract_imports()
        docstring = parser.extract_docstring()
        loc = parser.count_lines()

        # Update statistics
        self._statistics.total_files += 1
        self._statistics.total_loc += loc
        self._statistics.total_classes += len(classes)
        self._statistics.total_functions += len(functions)

        # Build module
        file_module = Module(
            name=file_path.stem,
            path=str(file_path),
            type="file",
            children=[],
            size_loc=loc,
            classes=classes,
            functions=functions,
            imports=imports,
            docstring=docstring,
        )

        # Extract interfaces (public classes and functions)
        file_module.interfaces = file_module.get_public_interfaces()

        # Extract dependencies from imports
        file_module.dependencies = [
            imp.module for imp in imports
            if not imp.module.startswith('.')  # Skip relative imports for now
        ]

        return file_module

    def _aggregate_interfaces(self, module: Module) -> List[str]:
        """Aggregate interfaces from all child modules."""
        interfaces = set(module.interfaces)

        for child in module.children:
            if child.type == "file":
                for interface in child.interfaces:
                    interfaces.add(f"{child.name}.{interface}")
            else:
                for interface in child.interfaces:
                    interfaces.add(f"{child.name}.{interface}")

        return list(interfaces)

    def _aggregate_dependencies(self, module: Module) -> List[str]:
        """Aggregate dependencies from all child modules."""
        dependencies = set(module.dependencies)

        for child in module.children:
            dependencies.update(child.dependencies)

        return list(dependencies)

    def _build_dependency_graph(self, root_module: Module) -> DependencyGraph:
        """Build dependency graph from module tree."""
        graph = DependencyGraph()

        # Collect all module names
        module_names = self._collect_module_names(root_module)

        # Process each file module
        self._add_dependencies_recursive(root_module, graph, module_names)

        return graph

    def _collect_module_names(self, module: Module, prefix: str = "") -> Set[str]:
        """Collect all module names from tree."""
        names = set()

        if prefix:
            full_name = f"{prefix}.{module.name}"
        else:
            full_name = module.name

        names.add(full_name)
        names.add(module.name)  # Also add short name

        for child in module.children:
            child_names = self._collect_module_names(child, full_name)
            names.update(child_names)

        return names

    def _add_dependencies_recursive(
        self,
        module: Module,
        graph: DependencyGraph,
        module_names: Set[str],
        prefix: str = ""
    ) -> None:
        """Recursively add dependencies to graph."""
        if prefix:
            full_name = f"{prefix}.{module.name}"
        else:
            full_name = module.name

        # Add node
        if full_name not in graph.nodes:
            graph.nodes.append(full_name)

        # Add dependencies
        for dep in module.dependencies:
            # Check if dependency is internal
            if dep in module_names or any(dep.startswith(m + '.') for m in module_names):
                graph.add_dependency(full_name, dep, "import")

        # Process children
        for child in module.children:
            self._add_dependencies_recursive(child, graph, module_names, full_name)
