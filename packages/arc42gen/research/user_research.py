"""
User research framework - analyzes a repository to identify developer friction points
and map persona needs to documentation sections.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional

from ..models.analysis import AnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class FrictionPoint:
    """A point of friction for developers onboarding to a codebase."""
    area: str  # e.g., "setup", "architecture", "testing"
    description: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    recommendation: str = ""

    def to_dict(self) -> Dict:
        return {
            "area": self.area,
            "description": self.description,
            "severity": self.severity,
            "recommendation": self.recommendation,
        }


@dataclass
class FrictionLog:
    """Complete friction analysis for a repository."""
    repo_name: str
    friction_points: List[FrictionPoint] = field(default_factory=list)
    has_readme: bool = False
    has_setup_instructions: bool = False
    has_contributing_guide: bool = False
    has_api_docs: bool = False
    dependency_count: int = 0
    file_count: int = 0
    setup_complexity: str = "unknown"  # simple, moderate, complex

    def to_dict(self) -> Dict:
        return {
            "repo_name": self.repo_name,
            "friction_points": [f.to_dict() for f in self.friction_points],
            "has_readme": self.has_readme,
            "has_setup_instructions": self.has_setup_instructions,
            "has_contributing_guide": self.has_contributing_guide,
            "has_api_docs": self.has_api_docs,
            "dependency_count": self.dependency_count,
            "file_count": self.file_count,
            "setup_complexity": self.setup_complexity,
        }

    @property
    def critical_points(self) -> List[FrictionPoint]:
        return [f for f in self.friction_points if f.severity == "CRITICAL"]

    @property
    def high_points(self) -> List[FrictionPoint]:
        return [f for f in self.friction_points if f.severity == "HIGH"]


@dataclass
class PersonaNeeds:
    """Documentation needs mapped to developer personas."""
    fresher: List[str] = field(default_factory=list)
    intermediate: List[str] = field(default_factory=list)
    senior: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "fresher": self.fresher,
            "intermediate": self.intermediate,
            "senior": self.senior,
        }


class UserResearch:
    """Analyzes a codebase to identify developer friction and documentation needs."""

    def create_friction_log(self, repo_path: str, analysis: Optional[AnalysisResult] = None) -> FrictionLog:
        """
        Analyze a repository for developer friction points.

        Checks for README, setup instructions, dependency documentation, etc.
        """
        path = Path(repo_path)
        log = FrictionLog(repo_name=path.name)

        if not path.exists():
            log.friction_points.append(FrictionPoint(
                area="access",
                description="Repository path does not exist",
                severity="CRITICAL",
            ))
            return log

        # Check for README
        readme_patterns = ["README.md", "README.rst", "README.txt", "README"]
        log.has_readme = any((path / p).exists() for p in readme_patterns)
        if not log.has_readme:
            log.friction_points.append(FrictionPoint(
                area="onboarding",
                description="No README file found",
                severity="CRITICAL",
                recommendation="Create a README.md with project overview and setup instructions",
            ))

        # Check README content if it exists
        if log.has_readme:
            readme_path = next((path / p for p in readme_patterns if (path / p).exists()), None)
            if readme_path:
                readme_content = readme_path.read_text().lower()
                log.has_setup_instructions = any(
                    term in readme_content
                    for term in ["install", "setup", "getting started", "quick start"]
                )
                if not log.has_setup_instructions:
                    log.friction_points.append(FrictionPoint(
                        area="setup",
                        description="README exists but lacks setup/install instructions",
                        severity="HIGH",
                        recommendation="Add a 'Getting Started' section to README",
                    ))

        # Check for contributing guide
        log.has_contributing_guide = any(
            (path / p).exists()
            for p in ["CONTRIBUTING.md", "CONTRIBUTING.rst", ".github/CONTRIBUTING.md"]
        )
        if not log.has_contributing_guide:
            log.friction_points.append(FrictionPoint(
                area="contribution",
                description="No CONTRIBUTING guide found",
                severity="MEDIUM",
                recommendation="Create CONTRIBUTING.md with development workflow",
            ))

        # Check for API documentation
        log.has_api_docs = any(
            (path / p).exists()
            for p in ["docs/", "doc/", "API.md", "api/"]
        )

        # Analyze dependency complexity
        self._check_dependencies(path, log)

        # Use analysis result if available
        if analysis:
            log.file_count = analysis.statistics.total_files
            self._analyze_complexity(analysis, log)

        # Determine setup complexity
        log.setup_complexity = self._assess_setup_complexity(log)

        return log

    def map_persona_needs(self, friction_log: FrictionLog) -> PersonaNeeds:
        """Map friction points to documentation needs per persona."""
        needs = PersonaNeeds()

        # Fresher needs: everything from scratch
        needs.fresher = [
            "Getting Started tutorial with step-by-step setup",
            "Architecture overview with visual diagrams",
            "Glossary of project-specific terms",
        ]

        # Add needs based on friction
        for point in friction_log.friction_points:
            if point.severity in ("CRITICAL", "HIGH"):
                if point.area == "setup":
                    needs.fresher.append("Detailed environment setup guide")
                    needs.intermediate.append("Quick setup reference")
                elif point.area == "architecture":
                    needs.fresher.append("Module-by-module walkthrough")
                    needs.intermediate.append("Architecture decision records")
                elif point.area == "onboarding":
                    needs.fresher.append("Project overview and purpose")

        # Intermediate needs
        needs.intermediate.extend([
            "How-to guides for common tasks",
            "API reference documentation",
            "Testing guide",
        ])

        # Senior needs
        needs.senior = [
            "Architecture decision records (ADRs)",
            "Cross-cutting concerns documentation",
            "Deployment and infrastructure guide",
            "Risk assessment and technical debt tracker",
        ]

        if friction_log.setup_complexity == "complex":
            needs.senior.append("Infrastructure dependency map")

        return needs

    def _check_dependencies(self, path: Path, log: FrictionLog) -> None:
        """Check dependency files and count."""
        dep_files = {
            "package.json": "npm",
            "requirements.txt": "pip",
            "pyproject.toml": "poetry/pip",
            "Pipfile": "pipenv",
            "go.mod": "go",
            "Cargo.toml": "cargo",
        }

        for filename, manager in dep_files.items():
            filepath = path / filename
            if filepath.exists():
                try:
                    content = filepath.read_text()
                    # Rough count of dependencies
                    if filename == "package.json":
                        import json
                        data = json.loads(content)
                        deps = len(data.get("dependencies", {}))
                        dev_deps = len(data.get("devDependencies", {}))
                        log.dependency_count = deps + dev_deps
                    elif filename == "requirements.txt":
                        log.dependency_count = len([
                            l for l in content.split('\n')
                            if l.strip() and not l.startswith('#')
                        ])
                except Exception:
                    pass

        if log.dependency_count > 50:
            log.friction_points.append(FrictionPoint(
                area="dependencies",
                description=f"High dependency count ({log.dependency_count})",
                severity="MEDIUM",
                recommendation="Document key dependencies and their purposes",
            ))

    def _analyze_complexity(self, analysis: AnalysisResult, log: FrictionLog) -> None:
        """Analyze codebase complexity from analysis result."""
        stats = analysis.statistics

        if stats.total_loc > 50000:
            log.friction_points.append(FrictionPoint(
                area="complexity",
                description=f"Large codebase ({stats.total_loc:,} LOC)",
                severity="MEDIUM",
                recommendation="Provide module-level architecture overview",
            ))

        if stats.total_modules > 20:
            log.friction_points.append(FrictionPoint(
                area="architecture",
                description=f"Many modules ({stats.total_modules}) - may be hard to navigate",
                severity="MEDIUM",
                recommendation="Create module dependency diagram",
            ))

    def _assess_setup_complexity(self, log: FrictionLog) -> str:
        """Assess overall setup complexity."""
        complexity_score = 0

        if log.dependency_count > 30:
            complexity_score += 2
        elif log.dependency_count > 10:
            complexity_score += 1

        if log.file_count > 100:
            complexity_score += 1

        if not log.has_setup_instructions:
            complexity_score += 2

        critical_count = len(log.critical_points)
        complexity_score += critical_count

        if complexity_score >= 4:
            return "complex"
        elif complexity_score >= 2:
            return "moderate"
        return "simple"
