"""
Diátaxis documentation generator using LLM.
"""

import logging
import re
from typing import List, Optional

from ..models.analysis import AnalysisResult
from ..models.citation import Fact, GroundedDocument
from ..models.config import LLMConfig
from ..providers.base import BaseLLMProvider
from ..providers.factory import create_llm_provider
from ..templates import load_prompt
from ..utils.sanitizer import sanitize_llm_content, sanitize_list_item, is_placeholder_content
from .models import (
    Tutorial,
    TutorialStep,
    HowToGuide,
    TroubleshootingItem,
    Reference,
    APIEndpoint,
    Explanation,
    DiátaxisDocument,
)


logger = logging.getLogger(__name__)


class DiátaxisGenerator:
    """Generates Diátaxis framework documentation using LLM."""

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

        logger.info(f"DiátaxisGenerator initialized with {self.provider.provider_name}")

    def generate_all(self, analysis: AnalysisResult) -> DiátaxisDocument:
        """Generate complete Diátaxis documentation."""
        logger.info("Generating Diátaxis documentation")

        tutorials = [self.generate_getting_started_tutorial(analysis)]
        how_to_guides = [
            self.generate_setup_howto(analysis),
            self.generate_troubleshooting_howto(analysis),
        ]
        references = [self.generate_api_reference(analysis)]
        explanations = [self.generate_architecture_explanation(analysis)]

        return DiátaxisDocument(
            tutorials=tutorials,
            how_to_guides=how_to_guides,
            references=references,
            explanations=explanations,
        )

    # =========================================================================
    # Tutorials
    # =========================================================================

    def generate_getting_started_tutorial(self, analysis: AnalysisResult) -> Tutorial:
        """Generate a Getting Started tutorial."""
        logger.info("Generating Getting Started tutorial")
        prompt = self._build_tutorial_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=3000)
        return self._parse_tutorial_response(response, "Getting Started")

    def _build_tutorial_prompt(self, analysis: AnalysisResult) -> str:
        modules = [m.name for m in analysis.module_tree.get_top_level_modules()[:10]]
        return load_prompt("diataxis/tutorial",
            repo_name=analysis.repo_name,
            language=analysis.language,
            modules=', '.join(modules),
            total_loc=analysis.statistics.total_loc,
        )

    def _parse_tutorial_response(self, response: str, default_title: str) -> Tutorial:
        goal = sanitize_llm_content(self._extract_section(response, "GOAL") or "Complete the tutorial")
        time = sanitize_llm_content(self._extract_section(response, "TIME") or "")

        prerequisites = []
        prereq_text = self._extract_section(response, "PREREQUISITES")
        if prereq_text:
            for line in prereq_text.split('\n'):
                line = sanitize_list_item(line.strip().lstrip('-').strip())
                if line and not is_placeholder_content(line):
                    prerequisites.append(line)

        steps = []
        for i in range(1, 10):
            step_text = self._extract_section(response, f"STEP_{i}")
            if step_text:
                title = ""
                instructions = ""
                code = ""
                checkpoint = ""

                title_match = re.search(r"TITLE:\s*(.+?)(?=\n|INSTRUCTIONS)", step_text)
                if title_match:
                    title = sanitize_llm_content(title_match.group(1).strip())

                instr_match = re.search(r"INSTRUCTIONS:\s*(.+?)(?=\nCODE|CHECKPOINT|$)", step_text, re.DOTALL)
                if instr_match:
                    instructions = sanitize_llm_content(instr_match.group(1).strip())

                code_match = re.search(r"CODE:\s*(.+?)(?=\nCHECKPOINT|$)", step_text, re.DOTALL)
                if code_match:
                    code = code_match.group(1).strip()  # Don't sanitize code

                check_match = re.search(r"CHECKPOINT:\s*(.+?)$", step_text, re.DOTALL)
                if check_match:
                    checkpoint = sanitize_llm_content(check_match.group(1).strip())

                if title and not is_placeholder_content(title):
                    steps.append(TutorialStep(
                        title=title,
                        instructions=instructions,
                        code=code,
                        checkpoint=checkpoint,
                    ))

        next_steps = []
        next_text = self._extract_section(response, "NEXT_STEPS")
        if next_text:
            for line in next_text.split('\n'):
                line = sanitize_list_item(line.strip().lstrip('-').strip())
                if line and not is_placeholder_content(line):
                    next_steps.append(line)

        return Tutorial(
            title=default_title,
            goal=goal,
            prerequisites=prerequisites,
            estimated_time=time,
            steps=steps,
            next_steps=next_steps,
        )

    # =========================================================================
    # How-To Guides
    # =========================================================================

    def generate_setup_howto(self, analysis: AnalysisResult) -> HowToGuide:
        """Generate a Local Setup how-to guide."""
        logger.info("Generating Local Setup how-to")
        prompt = self._build_howto_prompt(analysis, "Local Development Setup")
        response = self._call_llm(prompt, max_tokens=2000)
        return self._parse_howto_response(response, "Local Development Setup")

    def generate_troubleshooting_howto(self, analysis: AnalysisResult) -> HowToGuide:
        """Generate a Troubleshooting how-to guide."""
        logger.info("Generating Troubleshooting how-to")
        prompt = self._build_troubleshooting_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=2000)
        return self._parse_howto_response(response, "Troubleshooting Common Issues")

    def _build_howto_prompt(self, analysis: AnalysisResult, topic: str) -> str:
        return load_prompt("diataxis/howto",
            repo_name=analysis.repo_name,
            language=analysis.language,
            topic=topic,
        )

    def _build_troubleshooting_prompt(self, analysis: AnalysisResult) -> str:
        return load_prompt("diataxis/troubleshooting",
            repo_name=analysis.repo_name,
            language=analysis.language,
        )

    def _parse_howto_response(self, response: str, default_title: str) -> HowToGuide:
        problem = sanitize_llm_content(self._extract_section(response, "PROBLEM") or "")
        time = sanitize_llm_content(self._extract_section(response, "TIME") or "")

        prerequisites = []
        prereq_text = self._extract_section(response, "PREREQUISITES")
        if prereq_text:
            for line in prereq_text.split('\n'):
                line = sanitize_list_item(line.strip().lstrip('-').strip())
                if line and not is_placeholder_content(line):
                    prerequisites.append(line)

        steps = []
        steps_text = self._extract_section(response, "STEPS")
        if steps_text:
            for line in steps_text.split('\n'):
                line = sanitize_list_item(line.strip().lstrip('-').lstrip('0123456789.').strip())
                if line and not is_placeholder_content(line):
                    steps.append(line)

        troubleshooting = []
        # Parse new ISSUE/FIX format
        troubleshooting_text = self._extract_section(response, "TROUBLESHOOTING")
        if troubleshooting_text:
            issue_pattern = r'ISSUE:\s*(.+?)(?=\nFIX:|$)'
            fix_pattern = r'FIX:\s*(.+?)(?=\nISSUE:|$)'
            issues = re.findall(issue_pattern, troubleshooting_text, re.DOTALL)
            fixes = re.findall(fix_pattern, troubleshooting_text, re.DOTALL)
            for issue, fix in zip(issues, fixes):
                issue_clean = sanitize_llm_content(issue)
                fix_clean = sanitize_llm_content(fix)
                if issue_clean and fix_clean and not is_placeholder_content(issue_clean):
                    troubleshooting.append(TroubleshootingItem(
                        problem=issue_clean,
                        solution=fix_clean,
                    ))
        
        # Fallback: try old PROBLEM_N/SOLUTION_N format for backward compatibility
        if not troubleshooting:
            for i in range(1, 10):
                prob = self._extract_section(response, f"PROBLEM_{i}")
                sol = self._extract_section(response, f"SOLUTION_{i}")
                if prob and sol:
                    prob_clean = sanitize_llm_content(prob)
                    sol_clean = sanitize_llm_content(sol)
                    if prob_clean and sol_clean and not is_placeholder_content(prob_clean):
                        troubleshooting.append(TroubleshootingItem(
                            problem=prob_clean,
                            solution=sol_clean,
                        ))

        return HowToGuide(
            title=default_title,
            problem=problem,
            prerequisites=prerequisites,
            estimated_time=time,
            steps=steps,
            troubleshooting=troubleshooting,
        )

    # =========================================================================
    # Reference
    # =========================================================================

    def generate_api_reference(self, analysis: AnalysisResult) -> Reference:
        """Generate API reference documentation."""
        logger.info("Generating API reference")
        prompt = self._build_reference_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=3000)
        return self._parse_reference_response(response, analysis.repo_name)

    def _build_reference_prompt(self, analysis: AnalysisResult) -> str:
        modules = [m.name for m in analysis.module_tree.get_top_level_modules()[:10]]
        return load_prompt("diataxis/reference",
            repo_name=analysis.repo_name,
            language=analysis.language,
            modules=', '.join(modules),
        )

    def _parse_reference_response(self, response: str, repo_name: str) -> Reference:
        overview = self._extract_section(response, "OVERVIEW") or ""

        sections = {}
        section_pattern = r"SECTION_([^:]+):\s*\n(.*?)(?=SECTION_|CONFIGURATION|$)"
        matches = re.findall(section_pattern, response, re.DOTALL)
        for name, content in matches:
            sections[name.strip()] = content.strip()

        configuration = {}
        config_text = self._extract_section(response, "CONFIGURATION")
        if config_text:
            for line in config_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:
                        configuration[parts[0]] = parts[1]

        return Reference(
            title=f"{repo_name} Reference",
            overview=overview,
            sections=sections,
            configuration=configuration,
        )

    # =========================================================================
    # Explanation
    # =========================================================================

    def generate_architecture_explanation(self, analysis: AnalysisResult) -> Explanation:
        """Generate architecture explanation."""
        logger.info("Generating architecture explanation")
        prompt = self._build_explanation_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=2500)
        return self._parse_explanation_response(response)

    def _build_explanation_prompt(self, analysis: AnalysisResult) -> str:
        modules = [m.name for m in analysis.module_tree.get_top_level_modules()[:10]]
        return load_prompt("diataxis/explanation",
            repo_name=analysis.repo_name,
            language=analysis.language,
            modules=', '.join(modules),
            total_loc=analysis.statistics.total_loc,
        )

    def _parse_explanation_response(self, response: str) -> Explanation:
        title = self._extract_section(response, "TITLE") or "Architecture Overview"
        problem = self._extract_section(response, "PROBLEM") or ""
        solution = self._extract_section(response, "SOLUTION") or ""

        benefits = []
        ben_text = self._extract_section(response, "BENEFITS")
        if ben_text:
            for line in ben_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if line:
                    benefits.append(line)

        tradeoffs = []
        trade_text = self._extract_section(response, "TRADEOFFS")
        if trade_text:
            for line in trade_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if line:
                    tradeoffs.append(line)

        when_to_use = []
        when_text = self._extract_section(response, "WHEN_TO_USE")
        if when_text:
            for line in when_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if line:
                    when_to_use.append(line)

        when_not = []
        not_text = self._extract_section(response, "WHEN_NOT_TO_USE")
        if not_text:
            for line in not_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if line:
                    when_not.append(line)

        related = []
        rel_text = self._extract_section(response, "RELATED")
        if rel_text:
            for line in rel_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if line:
                    related.append(line)

        return Explanation(
            title=title,
            problem=problem,
            solution=solution,
            benefits=benefits,
            tradeoffs=tradeoffs,
            when_to_use=when_to_use,
            when_not_to_use=when_not,
            related_sections=related,
        )

    # =========================================================================
    # Citation-Aware Generation
    # =========================================================================

    def generate_all_with_citations(
        self,
        analysis: AnalysisResult,
        facts: List[Fact],
    ) -> tuple:
        """
        Generate Diataxis documentation with citation grounding.

        Returns (diataxis_doc, grounded_document) tuple.
        """
        self._current_facts = facts

        try:
            doc = self.generate_all(analysis)
        finally:
            self._current_facts = None

        # Build grounded document from all generated content
        all_content = []
        for tutorial in doc.tutorials:
            all_content.append(tutorial.to_markdown())
        for guide in doc.how_to_guides:
            all_content.append(guide.to_markdown())
        for ref in doc.references:
            all_content.append(ref.to_markdown())
        for exp in doc.explanations:
            all_content.append(exp.to_markdown())

        grounded = GroundedDocument(
            content="\n\n".join(all_content),
            citations_count=len(facts),
        )

        return doc, grounded

    def _build_facts_context(self, facts: List[Fact]) -> str:
        """Format facts as evidence context for LLM prompts."""
        if not facts:
            return ""

        lines = ["\nEVIDENCE FROM CODEBASE (reference these in your response):"]
        for fact in facts[:50]:
            lines.append(
                f"- [{fact.id}] {fact.text} "
                f"(source: {fact.citation.source_file}:{fact.citation.line_start})"
            )
        return "\n".join(lines)

    # =========================================================================
    # Helpers
    # =========================================================================

    def _extract_section(self, text: str, section_name: str) -> Optional[str]:
        """Extract a section from the response."""
        pattern = rf"{section_name}:\s*\n?(.*?)(?=\n[A-Z_]+:|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _call_llm(self, prompt: str, max_tokens: int = 3000) -> str:
        """Call the LLM provider. Injects fact evidence if available."""
        current_facts = getattr(self, '_current_facts', None)
        if current_facts:
            prompt = prompt + self._build_facts_context(current_facts)

        try:
            response = self.provider.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.content
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise
