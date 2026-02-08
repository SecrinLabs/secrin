"""
Quality metrics analyzer for generated documentation.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..models.citation import GroundedDocument

logger = logging.getLogger(__name__)


@dataclass
class QualityDimension:
    """A single quality measurement dimension."""
    name: str
    score: float  # 0.0 to 1.0
    details: str = ""

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "score": self.score,
            "details": self.details,
        }


@dataclass
class QualityScore:
    """Complete quality score for a document."""
    dimensions: List[QualityDimension] = field(default_factory=list)
    overall: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "dimensions": [d.to_dict() for d in self.dimensions],
            "overall": self.overall,
        }


@dataclass
class QualityReport:
    """Full quality report for all generated documentation."""
    documents: Dict[str, QualityScore] = field(default_factory=dict)
    aggregate_score: float = 0.0
    citation_coverage: float = 0.0
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "documents": {k: v.to_dict() for k, v in self.documents.items()},
            "aggregate_score": self.aggregate_score,
            "citation_coverage": self.citation_coverage,
            "recommendations": self.recommendations,
        }


class QualityAnalyzer:
    """Measures functional quality of generated documentation."""

    def measure_functional_quality(self, content: str, title: str = "") -> QualityScore:
        """
        Measure functional quality across 5 dimensions:
        - Accessibility (readability grade)
        - Purposefulness (clear purpose in each section)
        - Findability (headings, table of contents potential)
        - Accuracy (based on citation density)
        - Completeness (coverage of expected topics)
        """
        dimensions = [
            self._measure_accessibility(content),
            self._measure_purposefulness(content),
            self._measure_findability(content),
            self._measure_accuracy(content),
            self._measure_completeness(content),
        ]

        overall = sum(d.score for d in dimensions) / len(dimensions) if dimensions else 0.0

        return QualityScore(dimensions=dimensions, overall=overall)

    def calculate_citation_coverage(self, grounded_doc: GroundedDocument) -> float:
        """Calculate percentage of claims with valid citations."""
        return grounded_doc.get_citation_coverage()

    def generate_report(
        self,
        documents: Dict[str, str],
        grounded_docs: Optional[Dict[str, GroundedDocument]] = None,
    ) -> QualityReport:
        """Generate a quality report for all documents."""
        report = QualityReport()

        for name, content in documents.items():
            report.documents[name] = self.measure_functional_quality(content, name)

        if report.documents:
            report.aggregate_score = sum(
                s.overall for s in report.documents.values()
            ) / len(report.documents)

        # Calculate citation coverage
        if grounded_docs:
            coverages = [
                self.calculate_citation_coverage(doc)
                for doc in grounded_docs.values()
            ]
            report.citation_coverage = sum(coverages) / len(coverages) if coverages else 0.0

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)

        return report

    def _measure_accessibility(self, content: str) -> QualityDimension:
        """Measure readability (simplified Flesch-Kincaid approximation)."""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        sentences = [s for s in sentences if s.strip()]

        if not words or not sentences:
            return QualityDimension(name="Accessibility", score=0.5, details="No content to analyze")

        avg_sentence_length = len(words) / len(sentences)
        # Approximate syllables (rough: count vowel groups)
        syllable_count = sum(
            len(re.findall(r'[aeiouy]+', word, re.IGNORECASE))
            for word in words
        )
        avg_syllables = syllable_count / len(words) if words else 0

        # Simplified Flesch Reading Ease (normalized to 0-1)
        # Original: 206.835 - 1.015 * ASL - 84.6 * ASW
        reading_ease = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables
        score = max(min(reading_ease / 100.0, 1.0), 0.0)

        if score > 0.7:
            details = f"Good readability (avg {avg_sentence_length:.0f} words/sentence)"
        elif score > 0.4:
            details = f"Moderate readability (avg {avg_sentence_length:.0f} words/sentence)"
        else:
            details = f"Difficult readability (avg {avg_sentence_length:.0f} words/sentence)"

        return QualityDimension(name="Accessibility", score=score, details=details)

    def _measure_purposefulness(self, content: str) -> QualityDimension:
        """Measure whether each section has a clear purpose."""
        headings = re.findall(r'^#+\s+(.+)', content, re.MULTILINE)

        if not headings:
            return QualityDimension(name="Purposefulness", score=0.3, details="No headings found")

        # Check if headings are descriptive (not just numbers or generic terms)
        descriptive_count = 0
        for heading in headings:
            # Descriptive headings have >2 words or specific terms
            words = heading.split()
            if len(words) >= 2 or any(c.isdigit() for c in heading):
                descriptive_count += 1

        score = descriptive_count / len(headings) if headings else 0.0

        return QualityDimension(
            name="Purposefulness",
            score=score,
            details=f"{descriptive_count}/{len(headings)} headings are descriptive",
        )

    def _measure_findability(self, content: str) -> QualityDimension:
        """Measure how easy it is to find information."""
        headings = re.findall(r'^#+\s+', content, re.MULTILINE)
        code_blocks = re.findall(r'```', content)
        tables = re.findall(r'\|.*\|', content)
        links = re.findall(r'\[.*?\]\(.*?\)', content)

        # Score based on structural elements
        structure_score = 0.0

        # Headings: at least 1 per 500 words
        word_count = len(content.split())
        expected_headings = max(word_count // 500, 1)
        heading_ratio = min(len(headings) / expected_headings, 1.0) if expected_headings > 0 else 0.0
        structure_score += heading_ratio * 0.4

        # Code blocks presence
        if code_blocks:
            structure_score += 0.2

        # Tables for structured data
        if tables:
            structure_score += 0.2

        # Cross-references / links
        if links:
            structure_score += 0.2

        return QualityDimension(
            name="Findability",
            score=min(structure_score, 1.0),
            details=f"{len(headings)} headings, {len(code_blocks)//2} code blocks, {len(tables)} table rows",
        )

    def _measure_accuracy(self, content: str) -> QualityDimension:
        """Measure accuracy signals (citations, source references)."""
        # Look for citation markers or source references
        citations = re.findall(r'\[(?:CITE:|source:|Source:).*?\]', content, re.IGNORECASE)
        file_refs = re.findall(r'`[^`]+\.\w+(?::\d+)?`', content)  # file.ext or file.ext:line

        total_refs = len(citations) + len(file_refs)
        word_count = len(content.split())

        # Score: at least 1 reference per 200 words
        expected_refs = max(word_count // 200, 1)
        score = min(total_refs / expected_refs, 1.0) if expected_refs > 0 else 0.0

        return QualityDimension(
            name="Accuracy",
            score=score,
            details=f"{total_refs} source references found ({len(citations)} citations, {len(file_refs)} file refs)",
        )

    def _measure_completeness(self, content: str) -> QualityDimension:
        """Measure content completeness."""
        content_lower = content.lower()

        # Check for key documentation elements
        elements = {
            "overview": any(w in content_lower for w in ["overview", "introduction", "about"]),
            "details": len(content.split()) > 200,
            "examples": "example" in content_lower or "```" in content,
            "structure": bool(re.findall(r'^#+\s+', content, re.MULTILINE)),
        }

        score = sum(1 for v in elements.values() if v) / len(elements)

        missing = [k for k, v in elements.items() if not v]
        details = f"Missing: {', '.join(missing)}" if missing else "All key elements present"

        return QualityDimension(name="Completeness", score=score, details=details)

    def _generate_recommendations(self, report: QualityReport) -> List[str]:
        """Generate actionable recommendations from quality report."""
        recommendations = []

        for name, score in report.documents.items():
            for dim in score.dimensions:
                if dim.score < 0.5:
                    if dim.name == "Accessibility":
                        recommendations.append(f"[{name}] Simplify language - shorten sentences")
                    elif dim.name == "Purposefulness":
                        recommendations.append(f"[{name}] Add descriptive headings")
                    elif dim.name == "Findability":
                        recommendations.append(f"[{name}] Add more structure (headings, tables)")
                    elif dim.name == "Accuracy":
                        recommendations.append(f"[{name}] Add source code references")
                    elif dim.name == "Completeness":
                        recommendations.append(f"[{name}] {dim.details}")

        if report.citation_coverage < 0.5:
            recommendations.append("Overall citation coverage is low - re-run with grounding engine")

        return recommendations
