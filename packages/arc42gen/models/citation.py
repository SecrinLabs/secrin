"""
Citation and provenance data models for grounded documentation generation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class FactType(Enum):
    """Types of facts that can be extracted from code."""
    TECHNOLOGY = "technology"
    STRUCTURE = "structure"
    INTEGRATION = "integration"
    CONFIG = "config"
    DEPENDENCY = "dependency"
    INTERFACE = "interface"


class ClaimType(Enum):
    """Types of claims in documentation."""
    ARCHITECTURE = "architecture"
    TECHNOLOGY = "technology"
    BEHAVIOR = "behavior"
    INTEGRATION = "integration"
    CONFIGURATION = "configuration"


class Severity(Enum):
    """Severity levels for validation errors."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Citation:
    """A reference to a specific location in the source code."""
    source_file: str
    line_start: int
    line_end: int = 0
    snippet: str = ""
    confidence: float = 1.0
    commit_hash: str = ""

    def to_dict(self) -> Dict:
        return {
            "source_file": self.source_file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "snippet": self.snippet,
            "confidence": self.confidence,
            "commit_hash": self.commit_hash,
        }

    def to_reference(self) -> str:
        """Format as a human-readable reference."""
        ref = f"`{self.source_file}:{self.line_start}"
        if self.line_end:
            ref += f"-{self.line_end}"
        ref += "`"
        return ref


@dataclass
class Fact:
    """A provable fact extracted from code analysis."""
    id: str
    text: str
    citation: Citation
    fact_type: FactType

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "text": self.text,
            "citation": self.citation.to_dict(),
            "fact_type": self.fact_type.value,
        }


@dataclass
class CitedClaim:
    """A claim in documentation backed by citations."""
    text: str
    citations: List[Citation] = field(default_factory=list)
    claim_type: ClaimType = ClaimType.ARCHITECTURE

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "citations": [c.to_dict() for c in self.citations],
            "claim_type": self.claim_type.value,
        }

    def is_grounded(self) -> bool:
        """Check if this claim has at least one citation."""
        return len(self.citations) > 0


@dataclass
class GroundedDocument:
    """A document section with citation-grounded content."""
    content: str
    claims: List[CitedClaim] = field(default_factory=list)
    citations_count: int = 0
    ungrounded_claims: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "claims": [c.to_dict() for c in self.claims],
            "citations_count": self.citations_count,
            "ungrounded_claims": self.ungrounded_claims,
        }

    def get_citation_coverage(self) -> float:
        """Calculate percentage of claims with citations."""
        if not self.claims:
            return 1.0
        grounded = sum(1 for c in self.claims if c.is_grounded())
        return grounded / len(self.claims)


@dataclass
class ValidationError:
    """An error found during citation validation."""
    claim: str
    error: str
    severity: Severity
    fix_suggestion: str = ""

    def to_dict(self) -> Dict:
        return {
            "claim": self.claim,
            "error": self.error,
            "severity": self.severity.value,
            "fix_suggestion": self.fix_suggestion,
        }


@dataclass
class ValidationReport:
    """Report from citation validation."""
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    citation_coverage: float = 0.0
    total_claims: int = 0
    grounded_claims: int = 0

    def to_dict(self) -> Dict:
        return {
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "citation_coverage": self.citation_coverage,
            "total_claims": self.total_claims,
            "grounded_claims": self.grounded_claims,
        }

    @property
    def is_valid(self) -> bool:
        """Check if there are no errors."""
        return len(self.errors) == 0


@dataclass
class Provenance:
    """Provenance metadata for generated documentation."""
    generated_at: str
    generator_version: str
    source_commit: str = ""
    llm_provider: str = ""
    llm_model: str = ""
    citations_count: int = 0
    content_hash: str = ""
    facts_count: int = 0
    citation_coverage: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "generated_at": self.generated_at,
            "generator_version": self.generator_version,
            "source_commit": self.source_commit,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "citations_count": self.citations_count,
            "content_hash": self.content_hash,
            "facts_count": self.facts_count,
            "citation_coverage": self.citation_coverage,
        }

    def to_footer(self) -> str:
        """Generate a provenance footer for MDX files."""
        lines = [
            "",
            "---",
            "",
            "<details>",
            "<summary>Document Provenance</summary>",
            "",
            f"- **Generated**: {self.generated_at}",
            f"- **Generator**: arc42gen v{self.generator_version}",
            f"- **Source Commit**: `{self.source_commit[:8]}`" if self.source_commit else "",
            f"- **LLM**: {self.llm_provider}/{self.llm_model}",
            f"- **Citations**: {self.citations_count}",
            f"- **Citation Coverage**: {self.citation_coverage:.0%}",
            "",
            "</details>",
        ]
        return "\n".join(line for line in lines if line is not None)


@dataclass
class CodeSample:
    """A code sample extracted from the codebase."""
    code: str
    language: str
    file_path: str
    line_start: int
    line_end: int
    explanation: str = ""
    citation: Optional[Citation] = None

    def to_dict(self) -> Dict:
        return {
            "code": self.code,
            "language": self.language,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "explanation": self.explanation,
            "citation": self.citation.to_dict() if self.citation else None,
        }

    def to_markdown(self) -> str:
        """Format as markdown code block with citation."""
        md = f"```{self.language}\n{self.code}\n```\n"
        md += f"*Source: `{self.file_path}:{self.line_start}-{self.line_end}`*"
        return md
