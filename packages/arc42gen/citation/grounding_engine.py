"""
Grounded content generation - generates LLM content constrained to extracted facts.
"""

import logging
import re
from typing import List, Optional, Dict

from ..models.analysis import AnalysisResult
from ..models.citation import (
    Citation, Fact, CitedClaim, GroundedDocument, ClaimType,
)
from ..models.config import LLMConfig
from ..providers.base import BaseLLMProvider
from ..providers.factory import create_llm_provider
from ..templates import load_prompt

logger = logging.getLogger(__name__)


class GroundingEngine:
    """Generates documentation content grounded in extracted facts."""

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        provider: Optional[BaseLLMProvider] = None,
    ):
        if provider:
            self.provider = provider
        elif config:
            self.provider = create_llm_provider(config)
        else:
            raise ValueError("Must provide either config or provider")

    def generate_grounded_content(
        self,
        section_name: str,
        analysis: AnalysisResult,
        facts: List[Fact],
        additional_context: str = "",
    ) -> GroundedDocument:
        """
        Generate content for a documentation section, grounded in facts.

        The LLM is given facts as evidence and must cite them using [CITE:fact_id].
        """
        prompt = self._build_grounded_prompt(section_name, analysis, facts, additional_context)

        response = self._call_llm(prompt)

        return self._parse_grounded_response(response, facts)

    def _build_grounded_prompt(
        self,
        section_name: str,
        analysis: AnalysisResult,
        facts: List[Fact],
        additional_context: str,
    ) -> str:
        """Build a prompt that requires citation of facts."""
        facts_text = self._format_facts_for_prompt(facts)
        ctx = f"ADDITIONAL CONTEXT: {additional_context}" if additional_context else ""

        return load_prompt("citation/grounded",
            section_name=section_name,
            repo_name=analysis.repo_name,
            language=analysis.language,
            facts=facts_text,
            additional_context=ctx,
        )

    def _format_facts_for_prompt(self, facts: List[Fact]) -> str:
        """Format facts as numbered evidence for the LLM prompt."""
        lines = []
        for fact in facts[:50]:  # Limit to 50 facts to fit context
            lines.append(f"[{fact.id}] {fact.text} (source: {fact.citation.source_file}:{fact.citation.line_start})")
        return "\n".join(lines)

    def _parse_grounded_response(self, response: str, facts: List[Fact]) -> GroundedDocument:
        """Parse LLM response, extracting citations and building grounded document."""
        facts_by_id = {f.id: f for f in facts}
        claims = []
        ungrounded = []

        # Split response into sentences/claims
        sentences = re.split(r'(?<=[.!?])\s+', response)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Find all [CITE:FACT-XXXX] references
            cite_matches = re.findall(r'\[CITE:(FACT-\d+)\]', sentence)

            if cite_matches:
                citations = []
                for fact_id in cite_matches:
                    if fact_id in facts_by_id:
                        citations.append(facts_by_id[fact_id].citation)

                # Clean citation markers from the text for display
                clean_text = re.sub(r'\s*\[CITE:FACT-\d+\]', '', sentence).strip()

                claims.append(CitedClaim(
                    text=clean_text,
                    citations=citations,
                    claim_type=self._infer_claim_type(clean_text),
                ))
            elif self._is_factual_claim(sentence):
                ungrounded.append(sentence)

        # Build clean content (with inline citations converted to footnotes)
        content = self._format_content_with_citations(response, facts_by_id)

        return GroundedDocument(
            content=content,
            claims=claims,
            citations_count=sum(len(c.citations) for c in claims),
            ungrounded_claims=ungrounded,
        )

    def _infer_claim_type(self, text: str) -> ClaimType:
        """Infer the type of a claim from its text."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["architecture", "pattern", "design", "structure"]):
            return ClaimType.ARCHITECTURE
        if any(w in text_lower for w in ["uses", "library", "framework", "technology"]):
            return ClaimType.TECHNOLOGY
        if any(w in text_lower for w in ["api", "endpoint", "interface", "protocol"]):
            return ClaimType.INTEGRATION
        if any(w in text_lower for w in ["config", "environment", "setting"]):
            return ClaimType.CONFIGURATION
        return ClaimType.BEHAVIOR

    def _is_factual_claim(self, sentence: str) -> bool:
        """Check if a sentence makes a factual claim (vs. being a heading or transition)."""
        if len(sentence) < 20:
            return False
        if sentence.startswith('#'):
            return False
        if sentence.startswith('Based on'):
            return False
        # Has technical terms suggesting a factual claim
        return any(w in sentence.lower() for w in [
            "uses", "depends", "contains", "implements", "provides",
            "connects", "handles", "processes", "stores", "manages",
        ])

    def _format_content_with_citations(self, response: str, facts_by_id: Dict[str, Fact]) -> str:
        """Convert [CITE:FACT-XXXX] markers to readable source references."""
        def replace_cite(match):
            fact_id = match.group(1)
            if fact_id in facts_by_id:
                fact = facts_by_id[fact_id]
                return f" [{fact.citation.source_file}:{fact.citation.line_start}]"
            return ""

        content = re.sub(r'\[CITE:(FACT-\d+)\]', replace_cite, response)
        return content

    def _call_llm(self, prompt: str, max_tokens: int = 4000) -> str:
        """Call the LLM provider."""
        try:
            response = self.provider.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.3,  # Lower temperature for more factual output
            )
            return response.content
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise
