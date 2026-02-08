"""
Code sample extractor - finds representative code snippets from the codebase.
"""

import logging
from pathlib import Path
from typing import List, Optional

from ..models.analysis import AnalysisResult, Module
from ..models.citation import Citation, CodeSample
from ..constants import get_fence_language

logger = logging.getLogger(__name__)


class CodeSampleExtractor:
    """Extracts representative code samples from a codebase for documentation."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def extract_samples(self, analysis: AnalysisResult, max_samples: int = 20) -> List[CodeSample]:
        """
        Extract representative code samples from the codebase.

        Prioritizes:
        1. Entry points (main files, API endpoints)
        2. Public class definitions
        3. Key function signatures
        """
        samples = []

        all_modules = analysis.module_tree.get_all_modules()
        file_modules = [m for m in all_modules if m.type == "file" and m.size_loc > 0]

        # Sort by importance (more interfaces = more important)
        file_modules.sort(key=lambda m: len(m.get_public_interfaces()), reverse=True)

        for module in file_modules:
            if len(samples) >= max_samples:
                break

            # Extract class samples
            for cls in module.classes:
                if not cls.name.startswith('_'):
                    sample = self._extract_class_sample(module, cls)
                    if sample:
                        samples.append(sample)

            # Extract function samples
            for func in module.functions:
                if not func.name.startswith('_') and len(samples) < max_samples:
                    sample = self._extract_function_sample(module, func)
                    if sample:
                        samples.append(sample)

        logger.info(f"Extracted {len(samples)} code samples")
        return samples

    def _extract_class_sample(self, module: Module, cls) -> Optional[CodeSample]:
        """Extract a code sample for a class definition."""
        file_path = self.repo_path / module.path
        if not file_path.exists():
            return None

        try:
            lines = file_path.read_text().split('\n')
            start = cls.line_number - 1
            # Get class definition + first few lines (up to 15 lines or first method)
            end = min(start + 15, cls.end_line if cls.end_line else start + 15, len(lines))
            snippet = '\n'.join(lines[start:end])

            if end < (cls.end_line or len(lines)):
                snippet += "\n    ..."

            language = self._detect_language(module.path)

            return CodeSample(
                code=snippet,
                language=language,
                file_path=module.path,
                line_start=cls.line_number,
                line_end=cls.end_line or end + 1,
                explanation=f"Class `{cls.name}`"
                           + (f" extends {', '.join(cls.bases)}" if cls.bases else "")
                           + (f" - {cls.docstring[:100]}" if cls.docstring else ""),
                citation=Citation(
                    source_file=module.path,
                    line_start=cls.line_number,
                    line_end=cls.end_line or end + 1,
                    snippet=f"class {cls.name}",
                ),
            )
        except (OSError, UnicodeDecodeError):
            return None

    def _extract_function_sample(self, module: Module, func) -> Optional[CodeSample]:
        """Extract a code sample for a function definition."""
        file_path = self.repo_path / module.path
        if not file_path.exists():
            return None

        try:
            lines = file_path.read_text().split('\n')
            start = func.line_number - 1
            # Get function signature + docstring (up to 10 lines)
            end = min(start + 10, func.end_line if func.end_line else start + 10, len(lines))
            snippet = '\n'.join(lines[start:end])

            if end < (func.end_line or len(lines)):
                snippet += "\n    ..."

            language = self._detect_language(module.path)

            params = ", ".join(func.parameters) if func.parameters else ""
            return_info = f" -> {func.return_type}" if func.return_type else ""

            return CodeSample(
                code=snippet,
                language=language,
                file_path=module.path,
                line_start=func.line_number,
                line_end=func.end_line or end + 1,
                explanation=f"Function `{func.name}({params}){return_info}`"
                           + (f" - {func.docstring[:100]}" if func.docstring else ""),
                citation=Citation(
                    source_file=module.path,
                    line_start=func.line_number,
                    line_end=func.end_line or end + 1,
                    snippet=f"def {func.name}" if language == "python" else f"function {func.name}",
                ),
            )
        except (OSError, UnicodeDecodeError):
            return None

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lstrip('.')
        return get_fence_language(ext)
