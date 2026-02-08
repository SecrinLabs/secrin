"""
Multi-pass documentation validator - 5-pass validation per the book's framework.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from ..models.citation import GroundedDocument, ValidationError, Severity, CitedClaim
from ..research.user_research import PersonaNeeds

logger = logging.getLogger(__name__)


@dataclass
class ValidationPass:
    """Result of a single validation pass."""
    name: str
    passed: bool
    issues: List[ValidationError] = field(default_factory=list)
    score: float = 0.0  # 0.0 to 1.0

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "issues": [i.to_dict() for i in self.issues],
            "score": self.score,
        }


@dataclass
class EditingReport:
    """Complete multi-pass validation report."""
    passes: List[ValidationPass] = field(default_factory=list)
    overall_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "passes": [p.to_dict() for p in self.passes],
            "overall_score": self.overall_score,
            "recommendations": self.recommendations,
        }

    @property
    def all_passed(self) -> bool:
        return all(p.passed for p in self.passes)


class DocumentationValidator:
    """
    Multi-pass documentation validator.

    5 passes:
    1. Technical accuracy - verify citations exist and match
    2. Completeness - check all persona questions answered
    3. Structure - logical organization, headings hierarchy
    4. Clarity - readability (word count, sentence length, jargon)
    5. Brevity - detect redundancy, excessive verbosity
    """

    def validate_all(
        self,
        content: str,
        grounded_doc: Optional[GroundedDocument] = None,
        persona_needs: Optional[PersonaNeeds] = None,
    ) -> EditingReport:
        """Run all 5 validation passes."""
        report = EditingReport()

        report.passes.append(self.validate_technical_accuracy(content, grounded_doc))
        report.passes.append(self.validate_completeness(content, persona_needs))
        report.passes.append(self.validate_structure(content))
        report.passes.append(self.validate_clarity(content))
        report.passes.append(self.validate_brevity(content))

        # Calculate overall score
        if report.passes:
            report.overall_score = sum(p.score for p in report.passes) / len(report.passes)

        # Generate recommendations
        for p in report.passes:
            if not p.passed:
                for issue in p.issues[:3]:  # Top 3 issues per pass
                    if issue.fix_suggestion:
                        report.recommendations.append(f"[{p.name}] {issue.fix_suggestion}")

        return report

    def validate_technical_accuracy(
        self,
        content: str,
        grounded_doc: Optional[GroundedDocument] = None,
    ) -> ValidationPass:
        """Pass 1: Verify citations exist and match."""
        issues = []

        if grounded_doc:
            # Check citation coverage
            coverage = grounded_doc.get_citation_coverage()
            if coverage < 0.5:
                issues.append(ValidationError(
                    claim="Overall document",
                    error=f"Low citation coverage: {coverage:.0%}",
                    severity=Severity.WARNING,
                    fix_suggestion="Add more source citations to factual claims",
                ))

            # Check for ungrounded claims
            for claim_text in grounded_doc.ungrounded_claims[:5]:
                issues.append(ValidationError(
                    claim=claim_text[:100],
                    error="Factual claim without citation",
                    severity=Severity.WARNING,
                    fix_suggestion="Add [CITE:FACT-XXXX] or rephrase as observation",
                ))

        # Check for hedge words that might indicate uncertainty
        uncertain_patterns = [
            r'\bprobably\b', r'\bmight\b', r'\bperhaps\b',
            r'\bseems to\b', r'\bappears to\b',
        ]
        for pattern in uncertain_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                issues.append(ValidationError(
                    claim=f"Found uncertain language: '{matches[0]}'",
                    error="Documentation should be definitive, not speculative",
                    severity=Severity.INFO,
                    fix_suggestion="Replace with cited facts or remove uncertain claims",
                ))

        score = 1.0 - min(len(issues) * 0.1, 0.5)
        return ValidationPass(
            name="Technical Accuracy",
            passed=not any(i.severity == Severity.ERROR for i in issues),
            issues=issues,
            score=max(score, 0.0),
        )

    def validate_completeness(
        self,
        content: str,
        persona_needs: Optional[PersonaNeeds] = None,
    ) -> ValidationPass:
        """Pass 2: Check all persona questions are answered."""
        issues = []
        content_lower = content.lower()

        # Essential topics that should be covered
        essential_topics = {
            "purpose": ["purpose", "overview", "what is", "introduction"],
            "setup": ["install", "setup", "getting started", "prerequisites"],
            "architecture": ["architecture", "structure", "components", "modules"],
        }

        covered = 0
        total = len(essential_topics)

        for topic, keywords in essential_topics.items():
            if any(kw in content_lower for kw in keywords):
                covered += 1
            else:
                issues.append(ValidationError(
                    claim=f"Topic: {topic}",
                    error=f"Documentation does not cover '{topic}'",
                    severity=Severity.WARNING,
                    fix_suggestion=f"Add a section covering {topic}",
                ))

        # Check persona needs if provided
        if persona_needs:
            for need in persona_needs.fresher[:3]:  # Check top fresher needs
                need_lower = need.lower()
                if not any(word in content_lower for word in need_lower.split()[:3]):
                    issues.append(ValidationError(
                        claim=f"Fresher need: {need}",
                        error="Documentation may not address new developer need",
                        severity=Severity.INFO,
                    ))

        score = covered / total if total > 0 else 1.0
        return ValidationPass(
            name="Completeness",
            passed=score >= 0.6,
            issues=issues,
            score=score,
        )

    def validate_structure(self, content: str) -> ValidationPass:
        """Pass 3: Validate logical organization and headings hierarchy."""
        issues = []
        lines = content.split('\n')

        # Check heading hierarchy
        headings = []
        for i, line in enumerate(lines, 1):
            match = re.match(r'^(#{1,6})\s+(.+)', line)
            if match:
                level = len(match.group(1))
                headings.append((i, level, match.group(2)))

        # Check for heading level jumps (e.g., h1 -> h3 without h2)
        for i in range(1, len(headings)):
            prev_level = headings[i-1][1]
            curr_level = headings[i][1]
            if curr_level > prev_level + 1:
                issues.append(ValidationError(
                    claim=f"Line {headings[i][0]}: {headings[i][2]}",
                    error=f"Heading level jumps from h{prev_level} to h{curr_level}",
                    severity=Severity.WARNING,
                    fix_suggestion=f"Use h{prev_level + 1} instead of h{curr_level}",
                ))

        # Check for empty sections (heading followed immediately by another heading)
        for i in range(len(headings) - 1):
            line_gap = headings[i+1][0] - headings[i][0]
            if line_gap <= 1:
                issues.append(ValidationError(
                    claim=f"Section: {headings[i][2]}",
                    error="Empty section (no content between headings)",
                    severity=Severity.WARNING,
                    fix_suggestion="Add content or remove the empty section",
                ))

        # Check minimum content length
        content_length = len(content.strip())
        if content_length < 200:
            issues.append(ValidationError(
                claim="Overall document",
                error="Document is very short",
                severity=Severity.WARNING,
                fix_suggestion="Expand with more detail and examples",
            ))

        total_checks = max(len(headings), 1) + 1  # heading checks + length check
        issue_count = len(issues)
        score = max(1.0 - (issue_count / total_checks), 0.0)

        return ValidationPass(
            name="Structure",
            passed=not any(i.severity == Severity.ERROR for i in issues),
            issues=issues,
            score=score,
        )

    def validate_clarity(self, content: str) -> ValidationPass:
        """Pass 4: Check readability (word count, sentence length, jargon)."""
        issues = []

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', content)
        sentences = [s for s in sentences if len(s.strip()) > 10]

        if not sentences:
            return ValidationPass(name="Clarity", passed=True, issues=[], score=1.0)

        # Check average sentence length
        word_counts = [len(s.split()) for s in sentences]
        avg_words = sum(word_counts) / len(word_counts) if word_counts else 0

        if avg_words > 30:
            issues.append(ValidationError(
                claim="Readability",
                error=f"Average sentence length is {avg_words:.0f} words (target: <25)",
                severity=Severity.WARNING,
                fix_suggestion="Break long sentences into shorter ones",
            ))

        # Check for very long sentences
        long_sentences = [s for s, wc in zip(sentences, word_counts) if wc > 40]
        for s in long_sentences[:3]:
            issues.append(ValidationError(
                claim=s[:80] + "...",
                error="Sentence exceeds 40 words",
                severity=Severity.INFO,
                fix_suggestion="Split into multiple sentences",
            ))

        # Check for jargon density (rough heuristic)
        jargon_terms = [
            "instantiate", "leverage", "utilize", "paradigm",
            "synergy", "holistic", "scalable", "robust",
        ]
        jargon_count = sum(
            1 for term in jargon_terms
            if term in content.lower()
        )
        if jargon_count > 3:
            issues.append(ValidationError(
                claim="Language",
                error=f"High jargon density ({jargon_count} jargon terms)",
                severity=Severity.INFO,
                fix_suggestion="Replace jargon with simpler alternatives",
            ))

        # Score: penalize for clarity issues
        score = max(1.0 - (len(issues) * 0.15), 0.0)
        return ValidationPass(
            name="Clarity",
            passed=score >= 0.5,
            issues=issues,
            score=score,
        )

    def validate_brevity(self, content: str) -> ValidationPass:
        """Pass 5: Detect redundancy and excessive verbosity."""
        issues = []
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        # Check for repeated phrases (simple n-gram check)
        words = content.lower().split()
        if len(words) > 50:
            # Check for repeated 3-grams
            trigrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
            trigram_counts = {}
            for tg in trigrams:
                trigram_counts[tg] = trigram_counts.get(tg, 0) + 1

            repeated = [(tg, count) for tg, count in trigram_counts.items() if count > 3]
            for phrase, count in repeated[:3]:
                issues.append(ValidationError(
                    claim=f"Repeated: '{phrase}'",
                    error=f"Phrase repeated {count} times",
                    severity=Severity.INFO,
                    fix_suggestion="Reduce repetition by consolidating information",
                ))

        # Check for verbose patterns
        verbose_patterns = [
            (r'\bin order to\b', "Use 'to' instead of 'in order to'"),
            (r'\bdue to the fact that\b', "Use 'because' instead"),
            (r'\bat this point in time\b', "Use 'now' instead"),
            (r'\bin the event that\b', "Use 'if' instead"),
            (r'\bhas the ability to\b', "Use 'can' instead"),
        ]

        for pattern, suggestion in verbose_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(ValidationError(
                    claim=f"Verbose: {pattern}",
                    error="Verbose phrasing detected",
                    severity=Severity.INFO,
                    fix_suggestion=suggestion,
                ))

        # Check overall word count vs content density
        word_count = len(words)
        heading_count = len(re.findall(r'^#+\s', content, re.MULTILINE))
        if heading_count > 0 and word_count / heading_count > 500:
            issues.append(ValidationError(
                claim="Section length",
                error=f"Average section is {word_count // heading_count} words (target: <300)",
                severity=Severity.WARNING,
                fix_suggestion="Break into smaller, focused sections",
            ))

        score = max(1.0 - (len(issues) * 0.1), 0.0)
        return ValidationPass(
            name="Brevity",
            passed=score >= 0.5,
            issues=issues,
            score=score,
        )
