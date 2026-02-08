"""
Citation validator - validates citations against the current codebase.
"""

import logging
from pathlib import Path
from typing import List, Optional

from ..models.citation import (
    Citation,
    CitedClaim,
    GroundedDocument,
    ValidationError,
    ValidationReport,
    Severity,
)

logger = logging.getLogger(__name__)


class CitationValidator:
    """Validates that citations in documentation still match the current codebase."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def validate(self, document: GroundedDocument) -> ValidationReport:
        """
        Validate all citations in a grounded document.

        Checks:
        - Referenced files exist
        - Line ranges are valid
        - Content snippets still match
        """
        errors = []
        warnings = []
        total_claims = len(document.claims)
        grounded_claims = 0

        for claim in document.claims:
            if not claim.citations:
                warnings.append(ValidationError(
                    claim=claim.text,
                    error="Claim has no citations",
                    severity=Severity.WARNING,
                    fix_suggestion="Add source code reference to support this claim",
                ))
                continue

            claim_valid = True
            for citation in claim.citations:
                result = self._validate_citation(citation)
                if result:
                    if result.severity == Severity.ERROR:
                        errors.append(result)
                        claim_valid = False
                    else:
                        warnings.append(result)

            if claim_valid:
                grounded_claims += 1

        # Check for ungrounded claims
        for ungrounded in document.ungrounded_claims:
            warnings.append(ValidationError(
                claim=ungrounded,
                error="Claim made without citation",
                severity=Severity.WARNING,
                fix_suggestion="Add [CITE:FACT-XXXX] reference or rephrase as opinion",
            ))

        coverage = grounded_claims / total_claims if total_claims > 0 else 1.0

        return ValidationReport(
            errors=errors,
            warnings=warnings,
            citation_coverage=coverage,
            total_claims=total_claims,
            grounded_claims=grounded_claims,
        )

    def validate_citation(self, citation: Citation) -> Optional[ValidationError]:
        """Validate a single citation. Public interface."""
        return self._validate_citation(citation)

    def _validate_citation(self, citation: Citation) -> Optional[ValidationError]:
        """Validate a single citation against the codebase."""
        source_path = self.repo_path / citation.source_file

        # Check file exists
        if not source_path.exists():
            return ValidationError(
                claim=f"Reference to {citation.source_file}",
                error=f"File not found: {citation.source_file}",
                severity=Severity.ERROR,
                fix_suggestion=f"File may have been moved or deleted. Check current codebase.",
            )

        # Check line range validity
        try:
            content = source_path.read_text()
            lines = content.split('\n')
            total_lines = len(lines)

            if citation.line_start > total_lines:
                return ValidationError(
                    claim=f"Reference to {citation.source_file}:{citation.line_start}",
                    error=f"Line {citation.line_start} exceeds file length ({total_lines} lines)",
                    severity=Severity.ERROR,
                    fix_suggestion="Line numbers may have shifted. Re-analyze the codebase.",
                )

            if citation.line_end and citation.line_end > total_lines:
                return ValidationError(
                    claim=f"Reference to {citation.source_file}:{citation.line_start}-{citation.line_end}",
                    error=f"End line {citation.line_end} exceeds file length ({total_lines} lines)",
                    severity=Severity.WARNING,
                    fix_suggestion="End line may need updating.",
                )

            # Check snippet still matches (if provided)
            if citation.snippet:
                file_content = content
                if citation.snippet not in file_content:
                    return ValidationError(
                        claim=f"Reference to {citation.source_file}",
                        error=f"Snippet '{citation.snippet}' not found in file",
                        severity=Severity.WARNING,
                        fix_suggestion="Code may have been refactored. Re-extract facts.",
                    )

        except (OSError, UnicodeDecodeError) as e:
            return ValidationError(
                claim=f"Reference to {citation.source_file}",
                error=f"Cannot read file: {e}",
                severity=Severity.ERROR,
            )

        return None

    def check_freshness(self, citations: List[Citation], current_commit: str = "") -> List[ValidationError]:
        """Check if citations are still fresh against current codebase state."""
        stale = []

        for citation in citations:
            if citation.commit_hash and current_commit and citation.commit_hash != current_commit:
                result = self._validate_citation(citation)
                if result:
                    stale.append(result)

        return stale
