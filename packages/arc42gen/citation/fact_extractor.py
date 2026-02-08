"""
Fact extraction engine - extracts provable facts from code analysis with file:line references.
"""

import logging
import os
import re
from pathlib import Path
from typing import List, Optional

from ..models.analysis import AnalysisResult, Module, ModuleTree
from ..models.citation import Citation, Fact, FactType

logger = logging.getLogger(__name__)


class FactExtractor:
    """Extracts provable facts from codebase analysis with exact source citations."""

    def __init__(self, repo_path: str = ""):
        self.repo_path = repo_path
        self._fact_counter = 0

    def extract_all_facts(self, analysis: AnalysisResult) -> List[Fact]:
        """
        Extract all provable facts from an analysis result.

        Returns facts with Citations pointing to exact file:line locations.
        No LLM involved - purely deterministic extraction.
        """
        facts = []

        facts.extend(self._extract_structure_facts(analysis))
        facts.extend(self._extract_dependency_facts(analysis))
        facts.extend(self._extract_interface_facts(analysis))
        facts.extend(self._extract_config_facts(analysis))
        facts.extend(self._extract_technology_facts(analysis))

        logger.info(f"Extracted {len(facts)} facts from {analysis.repo_name}")
        return facts

    def _next_id(self) -> str:
        self._fact_counter += 1
        return f"FACT-{self._fact_counter:04d}"

    def _extract_structure_facts(self, analysis: AnalysisResult) -> List[Fact]:
        """Extract facts about code structure (modules, classes, functions)."""
        facts = []
        all_modules = analysis.module_tree.get_all_modules()

        for module in all_modules:
            if module.type == "file" and module.size_loc > 0:
                # Fact: file exists with N lines
                facts.append(Fact(
                    id=self._next_id(),
                    text=f"File `{module.path}` contains {module.size_loc} lines of code",
                    citation=Citation(
                        source_file=module.path,
                        line_start=1,
                        line_end=module.size_loc,
                    ),
                    fact_type=FactType.STRUCTURE,
                ))

            # Facts about classes in the module
            for cls in module.classes:
                facts.append(Fact(
                    id=self._next_id(),
                    text=f"Class `{cls.name}` is defined in `{module.path}`"
                         + (f" extending {', '.join(cls.bases)}" if cls.bases else ""),
                    citation=Citation(
                        source_file=module.path,
                        line_start=cls.line_number,
                        line_end=cls.end_line or cls.line_number,
                        snippet=f"class {cls.name}",
                    ),
                    fact_type=FactType.STRUCTURE,
                ))

                # Methods
                for method in cls.methods:
                    facts.append(Fact(
                        id=self._next_id(),
                        text=f"Class `{cls.name}` has method `{method}`",
                        citation=Citation(
                            source_file=module.path,
                            line_start=cls.line_number,
                            line_end=cls.end_line or cls.line_number,
                        ),
                        fact_type=FactType.INTERFACE,
                    ))

            # Facts about functions
            for func in module.functions:
                params = ", ".join(func.parameters) if func.parameters else ""
                facts.append(Fact(
                    id=self._next_id(),
                    text=f"Function `{func.name}({params})` is defined in `{module.path}`",
                    citation=Citation(
                        source_file=module.path,
                        line_start=func.line_number,
                        line_end=func.end_line or func.line_number,
                        snippet=f"def {func.name}",
                    ),
                    fact_type=FactType.STRUCTURE,
                ))

        return facts

    def _extract_dependency_facts(self, analysis: AnalysisResult) -> List[Fact]:
        """Extract facts about dependencies between modules."""
        facts = []

        for edge in analysis.dependency_graph.edges:
            facts.append(Fact(
                id=self._next_id(),
                text=f"Module `{edge.from_module}` depends on `{edge.to_module}` via {edge.type}",
                citation=Citation(
                    source_file=edge.from_module,
                    line_start=1,
                ),
                fact_type=FactType.DEPENDENCY,
            ))

        return facts

    def _extract_interface_facts(self, analysis: AnalysisResult) -> List[Fact]:
        """Extract facts about public interfaces."""
        facts = []
        all_modules = analysis.module_tree.get_all_modules()

        for module in all_modules:
            interfaces = module.get_public_interfaces()
            if interfaces:
                facts.append(Fact(
                    id=self._next_id(),
                    text=f"Module `{module.name}` exposes: {', '.join(interfaces[:5])}",
                    citation=Citation(
                        source_file=module.path,
                        line_start=1,
                    ),
                    fact_type=FactType.INTERFACE,
                ))

        return facts

    def _extract_config_facts(self, analysis: AnalysisResult) -> List[Fact]:
        """Extract facts from configuration files in the repo."""
        facts = []
        repo_path = Path(self.repo_path or analysis.repo_path)

        if not repo_path.exists():
            return facts

        config_files = [
            ("package.json", self._parse_package_json),
            ("pyproject.toml", self._parse_pyproject_toml),
            ("requirements.txt", self._parse_requirements_txt),
            (".env.example", self._parse_env_file),
        ]

        for filename, parser in config_files:
            filepath = repo_path / filename
            if filepath.exists():
                try:
                    extracted = parser(filepath)
                    facts.extend(extracted)
                except Exception as e:
                    logger.warning(f"Failed to parse {filename}: {e}")

        return facts

    def _extract_technology_facts(self, analysis: AnalysisResult) -> List[Fact]:
        """Extract technology stack facts from imports and dependencies."""
        facts = []
        all_modules = analysis.module_tree.get_all_modules()

        # Collect all unique imports
        imports_seen = set()
        for module in all_modules:
            for imp in module.imports:
                top_level = imp.module.split('.')[0]
                if top_level not in imports_seen:
                    imports_seen.add(top_level)
                    facts.append(Fact(
                        id=self._next_id(),
                        text=f"Project uses library `{top_level}` (imported in `{module.path}`)",
                        citation=Citation(
                            source_file=module.path,
                            line_start=imp.line_number,
                            snippet=f"import {imp.module}",
                        ),
                        fact_type=FactType.TECHNOLOGY,
                    ))

        return facts

    def _parse_package_json(self, filepath: Path) -> List[Fact]:
        """Extract facts from package.json."""
        import json
        facts = []
        content = filepath.read_text()
        data = json.loads(content)

        if "dependencies" in data:
            for i, (dep, version) in enumerate(data["dependencies"].items()):
                facts.append(Fact(
                    id=self._next_id(),
                    text=f"Project depends on npm package `{dep}` version `{version}`",
                    citation=Citation(
                        source_file=str(filepath),
                        line_start=1,  # JSON doesn't have reliable line numbers
                        snippet=f'"{dep}": "{version}"',
                    ),
                    fact_type=FactType.DEPENDENCY,
                ))

        return facts

    def _parse_pyproject_toml(self, filepath: Path) -> List[Fact]:
        """Extract facts from pyproject.toml."""
        facts = []
        content = filepath.read_text()
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Match dependency lines like: package = "^1.0"
            match = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*"([^"]+)"', line.strip())
            if match:
                dep, version = match.groups()
                facts.append(Fact(
                    id=self._next_id(),
                    text=f"Project depends on Python package `{dep}` version `{version}`",
                    citation=Citation(
                        source_file=str(filepath),
                        line_start=line_num,
                        snippet=line.strip(),
                    ),
                    fact_type=FactType.DEPENDENCY,
                ))

        return facts

    def _parse_requirements_txt(self, filepath: Path) -> List[Fact]:
        """Extract facts from requirements.txt."""
        facts = []
        content = filepath.read_text()
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                facts.append(Fact(
                    id=self._next_id(),
                    text=f"Project requires Python package `{line}`",
                    citation=Citation(
                        source_file=str(filepath),
                        line_start=line_num,
                        snippet=line,
                    ),
                    fact_type=FactType.DEPENDENCY,
                ))

        return facts

    def _parse_env_file(self, filepath: Path) -> List[Fact]:
        """Extract facts from .env.example (environment variable names only)."""
        facts = []
        content = filepath.read_text()
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                var_name = line.split('=')[0].strip()
                facts.append(Fact(
                    id=self._next_id(),
                    text=f"System uses environment variable `{var_name}`",
                    citation=Citation(
                        source_file=str(filepath),
                        line_start=line_num,
                        snippet=var_name,
                    ),
                    fact_type=FactType.CONFIG,
                ))

        return facts
