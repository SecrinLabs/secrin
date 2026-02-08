"""
Documentation publisher with provenance tracking.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..models.citation import Provenance, Fact
from ..models.config import LLMConfig

logger = logging.getLogger(__name__)

GENERATOR_VERSION = "0.2.0"


@dataclass
class PublishResult:
    """Result of a documentation publish operation."""
    success: bool
    files_published: int = 0
    provenance: Optional[Provenance] = None
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "files_published": self.files_published,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "errors": self.errors,
        }


class DocumentationPublisher:
    """Publishes documentation with provenance metadata."""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        self.llm_config = llm_config

    def publish_with_provenance(
        self,
        files: Dict[str, str],
        facts: Optional[List[Fact]] = None,
        source_commit: str = "",
        citation_coverage: float = 0.0,
    ) -> PublishResult:
        """
        Add provenance metadata to documentation files.

        Returns updated files dict with provenance.json and footers added.
        """
        provenance = self._create_provenance(
            files=files,
            facts=facts,
            source_commit=source_commit,
            citation_coverage=citation_coverage,
        )

        # Add provenance.json to files
        files["provenance.json"] = json.dumps(provenance.to_dict(), indent=2)

        # Add provenance footer to MDX files
        mdx_count = 0
        for filename in list(files.keys()):
            if filename.endswith('.mdx'):
                files[filename] = files[filename] + provenance.to_footer()
                mdx_count += 1

        return PublishResult(
            success=True,
            files_published=mdx_count,
            provenance=provenance,
        )

    def create_citation_index(
        self,
        facts: List[Fact],
    ) -> str:
        """Generate a citation index page listing all facts and their sources."""
        lines = [
            "---",
            "title: Citation Index",
            "description: Source code references for all documented claims",
            "---",
            "",
            "# Citation Index",
            "",
            "This page lists all source code references used in the documentation.",
            "",
        ]

        # Group facts by type
        facts_by_type: Dict[str, List[Fact]] = {}
        for fact in facts:
            type_name = fact.fact_type.value.title()
            if type_name not in facts_by_type:
                facts_by_type[type_name] = []
            facts_by_type[type_name].append(fact)

        for type_name, type_facts in sorted(facts_by_type.items()):
            lines.append(f"## {type_name} Facts")
            lines.append("")
            lines.append("| ID | Fact | Source |")
            lines.append("|-----|------|--------|")
            for fact in type_facts:
                source = fact.citation.to_reference()
                lines.append(f"| {fact.id} | {fact.text[:80]} | {source} |")
            lines.append("")

        lines.append(f"\n*Total: {len(facts)} facts across {len(facts_by_type)} categories*")

        return "\n".join(lines)

    def _create_provenance(
        self,
        files: Dict[str, str],
        facts: Optional[List[Fact]] = None,
        source_commit: str = "",
        citation_coverage: float = 0.0,
    ) -> Provenance:
        """Create provenance metadata for a documentation generation."""
        # Calculate content hash
        all_content = "".join(sorted(files.values()))
        content_hash = hashlib.sha256(all_content.encode()).hexdigest()[:16]

        return Provenance(
            generated_at=datetime.now(timezone.utc).isoformat(),
            generator_version=GENERATOR_VERSION,
            source_commit=source_commit,
            llm_provider=self.llm_config.provider if self.llm_config else "",
            llm_model=self.llm_config.model if self.llm_config else "",
            citations_count=len(facts) if facts else 0,
            content_hash=content_hash,
            facts_count=len(facts) if facts else 0,
            citation_coverage=citation_coverage,
        )
