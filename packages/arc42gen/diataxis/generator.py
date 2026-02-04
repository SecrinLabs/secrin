"""
Diátaxis documentation generator using LLM.
"""

import logging
import re
from typing import List, Optional

from ..models.analysis import AnalysisResult
from ..models.config import LLMConfig
from ..providers.base import BaseLLMProvider
from ..providers.factory import create_llm_provider
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
        return f"""You are a technical writer creating developer documentation.

Create a "Getting Started" tutorial for this codebase:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
MODULES: {', '.join(modules)}
LOC: {analysis.statistics.total_loc}

Generate a tutorial with EXACTLY this format:

GOAL:
[What the developer will accomplish after completing this tutorial]

PREREQUISITES:
- [Prerequisite 1]
- [Prerequisite 2]

TIME:
[Estimated time, e.g., "15 minutes"]

STEP_1:
TITLE: [Step title]
INSTRUCTIONS: [What to do in this step]
CODE: [Shell commands if any]
CHECKPOINT: [How to verify this step worked]

STEP_2:
TITLE: [Step title]
INSTRUCTIONS: [What to do]
CODE: [Commands]
CHECKPOINT: [Verification]

STEP_3:
TITLE: [Step title]
INSTRUCTIONS: [What to do]
CODE: [Commands]
CHECKPOINT: [Verification]

NEXT_STEPS:
- [What to explore next]
- [Related documentation]

Create 3-5 clear steps for getting the project running locally."""

    def _parse_tutorial_response(self, response: str, default_title: str) -> Tutorial:
        goal = self._extract_section(response, "GOAL") or "Complete the tutorial"
        time = self._extract_section(response, "TIME") or ""

        prerequisites = []
        prereq_text = self._extract_section(response, "PREREQUISITES")
        if prereq_text:
            for line in prereq_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if line:
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
                    title = title_match.group(1).strip()

                instr_match = re.search(r"INSTRUCTIONS:\s*(.+?)(?=\nCODE|CHECKPOINT|$)", step_text, re.DOTALL)
                if instr_match:
                    instructions = instr_match.group(1).strip()

                code_match = re.search(r"CODE:\s*(.+?)(?=\nCHECKPOINT|$)", step_text, re.DOTALL)
                if code_match:
                    code = code_match.group(1).strip()

                check_match = re.search(r"CHECKPOINT:\s*(.+?)$", step_text, re.DOTALL)
                if check_match:
                    checkpoint = check_match.group(1).strip()

                if title:
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
                line = line.strip().lstrip('-').strip()
                if line:
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
        return f"""You are a technical writer creating developer documentation.

Create a How-To guide for "{topic}" for this codebase:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}

Generate a how-to guide with EXACTLY this format:

PROBLEM:
[What problem does this guide solve]

PREREQUISITES:
- [Prerequisite 1]
- [Prerequisite 2]

TIME:
[Estimated time]

STEPS:
- [Step 1]
- [Step 2]
- [Step 3]

TROUBLESHOOTING:
PROBLEM_1: [Common problem]
SOLUTION_1: [How to fix it]

PROBLEM_2: [Another common problem]
SOLUTION_2: [How to fix it]"""

    def _build_troubleshooting_prompt(self, analysis: AnalysisResult) -> str:
        return f"""You are a technical writer creating developer documentation.

Create a Troubleshooting guide for this codebase:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}

Generate a troubleshooting guide with EXACTLY this format:

PROBLEM:
Help developers fix common issues when working with this project

PREREQUISITES:
- Basic knowledge of {analysis.language}
- Project set up locally

STEPS:
- Identify the error message
- Check the troubleshooting section below
- Follow the solution steps

TROUBLESHOOTING:
PROBLEM_1: [Common issue like "Dependencies fail to install"]
SOLUTION_1: [How to fix it]

PROBLEM_2: [Common issue like "Tests fail"]
SOLUTION_2: [How to fix it]

PROBLEM_3: [Common issue]
SOLUTION_3: [How to fix it]

List 3-5 common problems developers might face."""

    def _parse_howto_response(self, response: str, default_title: str) -> HowToGuide:
        problem = self._extract_section(response, "PROBLEM") or ""
        time = self._extract_section(response, "TIME") or ""

        prerequisites = []
        prereq_text = self._extract_section(response, "PREREQUISITES")
        if prereq_text:
            for line in prereq_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if line:
                    prerequisites.append(line)

        steps = []
        steps_text = self._extract_section(response, "STEPS")
        if steps_text:
            for line in steps_text.split('\n'):
                line = line.strip().lstrip('-').lstrip('0123456789.').strip()
                if line:
                    steps.append(line)

        troubleshooting = []
        for i in range(1, 10):
            prob = self._extract_section(response, f"PROBLEM_{i}")
            sol = self._extract_section(response, f"SOLUTION_{i}")
            if prob and sol:
                troubleshooting.append(TroubleshootingItem(
                    problem=prob,
                    solution=sol,
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
        return f"""You are a technical writer creating developer documentation.

Create a Reference guide for this codebase:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
MODULES: {', '.join(modules)}

Generate a reference with EXACTLY this format:

OVERVIEW:
[Brief overview of the system and its main components]

SECTION_Architecture:
[Description of the architecture and main components]

SECTION_Modules:
[Description of main modules and their purpose]

CONFIGURATION:
- [Option Name]|[Description]
- [Option Name]|[Description]

Create factual, information-focused content."""

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
        return f"""You are a technical writer creating developer documentation.

Create an Architecture Explanation for this codebase:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
MODULES: {', '.join(modules)}
LOC: {analysis.statistics.total_loc}

Generate an explanation with EXACTLY this format:

TITLE:
Architecture Overview

PROBLEM:
[What architectural challenges does this system solve]

SOLUTION:
[How the architecture addresses these challenges]

BENEFITS:
- [Benefit 1]
- [Benefit 2]

TRADEOFFS:
- [Trade-off 1]
- [Trade-off 2]

WHEN_TO_USE:
- [When this approach is appropriate]

WHEN_NOT_TO_USE:
- [When this approach may not be ideal]

RELATED:
- [Related documentation or concepts]"""

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
        """Call the LLM provider."""
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
