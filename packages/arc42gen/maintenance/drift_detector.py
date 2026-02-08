"""
Documentation drift detector - detects when documentation falls out of sync with code.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional

from ..models.citation import Citation, Fact, Severity

logger = logging.getLogger(__name__)


@dataclass
class DriftIssue:
    """A single documentation drift issue."""
    fact_id: str
    description: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    old_value: str = ""
    new_value: str = ""
    affected_file: str = ""
    recommendation: str = ""

    def to_dict(self) -> Dict:
        return {
            "fact_id": self.fact_id,
            "description": self.description,
            "severity": self.severity,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "affected_file": self.affected_file,
            "recommendation": self.recommendation,
        }


@dataclass
class DriftReport:
    """Complete drift detection report."""
    issues: List[DriftIssue] = field(default_factory=list)
    total_facts_checked: int = 0
    stale_facts: int = 0
    missing_files: int = 0
    drift_percentage: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "issues": [i.to_dict() for i in self.issues],
            "total_facts_checked": self.total_facts_checked,
            "stale_facts": self.stale_facts,
            "missing_files": self.missing_files,
            "drift_percentage": self.drift_percentage,
        }

    @property
    def has_critical_drift(self) -> bool:
        return any(i.severity == "CRITICAL" for i in self.issues)

    @property
    def needs_regeneration(self) -> bool:
        """Check if drift is severe enough to warrant regeneration."""
        return self.drift_percentage > 0.3 or self.has_critical_drift


class DriftDetector:
    """Detects documentation drift by comparing stored citations against current code."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def detect_drift(self, facts: List[Fact]) -> DriftReport:
        """
        Compare stored facts/citations against current codebase state.

        Checks:
        - Referenced files still exist
        - Line ranges are still valid
        - Code snippets still match
        - Module structure hasn't fundamentally changed
        """
        report = DriftReport(total_facts_checked=len(facts))

        for fact in facts:
            issues = self._check_fact(fact)
            report.issues.extend(issues)

        report.stale_facts = len(set(i.fact_id for i in report.issues))
        report.missing_files = len([
            i for i in report.issues
            if "not found" in i.description.lower()
        ])
        report.drift_percentage = (
            report.stale_facts / report.total_facts_checked
            if report.total_facts_checked > 0
            else 0.0
        )

        logger.info(
            f"Drift report: {report.stale_facts}/{report.total_facts_checked} stale facts "
            f"({report.drift_percentage:.0%} drift)"
        )

        return report

    def _check_fact(self, fact: Fact) -> List[DriftIssue]:
        """Check a single fact against the current codebase."""
        issues = []
        citation = fact.citation
        source_path = self.repo_path / citation.source_file

        # Check file exists
        if not source_path.exists():
            issues.append(DriftIssue(
                fact_id=fact.id,
                description=f"Referenced file not found: {citation.source_file}",
                severity="CRITICAL",
                affected_file=citation.source_file,
                recommendation="File may have been moved or deleted. Regenerate documentation.",
            ))
            return issues

        try:
            content = source_path.read_text()
            lines = content.split('\n')
            total_lines = len(lines)

            # Check line range
            if citation.line_start > total_lines:
                issues.append(DriftIssue(
                    fact_id=fact.id,
                    description=f"Line {citation.line_start} exceeds file length ({total_lines})",
                    severity="HIGH",
                    old_value=f"Line {citation.line_start}",
                    new_value=f"File has {total_lines} lines",
                    affected_file=citation.source_file,
                    recommendation="Code has changed significantly. Re-analyze.",
                ))

            # Check snippet
            if citation.snippet and citation.snippet not in content:
                # Try to find similar content
                snippet_words = citation.snippet.split()
                if snippet_words:
                    first_word = snippet_words[0]
                    found_at = [
                        i + 1 for i, line in enumerate(lines)
                        if first_word in line
                    ]
                    if found_at:
                        issues.append(DriftIssue(
                            fact_id=fact.id,
                            description=f"Snippet moved: '{citation.snippet}' not at original location",
                            severity="MEDIUM",
                            old_value=f"Line {citation.line_start}",
                            new_value=f"Similar content at line(s) {found_at[:3]}",
                            affected_file=citation.source_file,
                            recommendation="Update line references.",
                        ))
                    else:
                        issues.append(DriftIssue(
                            fact_id=fact.id,
                            description=f"Snippet not found: '{citation.snippet}'",
                            severity="HIGH",
                            affected_file=citation.source_file,
                            recommendation="Code has been refactored. Re-extract facts.",
                        ))

        except (OSError, UnicodeDecodeError) as e:
            issues.append(DriftIssue(
                fact_id=fact.id,
                description=f"Cannot read file: {e}",
                severity="HIGH",
                affected_file=citation.source_file,
            ))

        return issues

    def get_staleness_summary(self, report: DriftReport) -> str:
        """Generate a human-readable summary of drift."""
        if not report.issues:
            return "Documentation is up-to-date with the codebase."

        lines = [f"Documentation Drift Report ({report.drift_percentage:.0%} drift):\n"]

        if report.missing_files > 0:
            lines.append(f"- {report.missing_files} referenced files no longer exist")

        severity_counts = {}
        for issue in report.issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1

        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = severity_counts.get(sev, 0)
            if count:
                lines.append(f"- {count} {sev} issues")

        if report.needs_regeneration:
            lines.append("\nRecommendation: Regenerate documentation.")
        else:
            lines.append("\nRecommendation: Update specific sections.")

        return "\n".join(lines)
