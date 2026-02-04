"""
Arc42 documentation generation using LLM providers.

Supports multiple LLM providers (Anthropic Claude, Google Gemini).
"""

import logging
import re
from pathlib import Path
from typing import List, Optional, Union

from ..models.analysis import AnalysisResult, Module
from ..models.config import LLMConfig
from ..models.documentation import (
    Section5,
    Level1Whitebox,
    Level2Whitebox,
    ComponentDescription,
    Section01,
    Section02,
    Section03,
    Section04,
    Section06,
    Section07,
    Section08,
    Section09,
    Section10,
    Section11,
    Section12,
    Arc42Document,
    Stakeholder,
    QualityGoal,
    Constraint,
    ExternalSystem,
    TechnologyDecision,
    RuntimeScenario,
    ArchitectureDecision,
    Risk,
    TechnicalDebt,
    GlossaryTerm,
)
from ..providers.base import BaseLLMProvider
from ..providers.factory import create_llm_provider


logger = logging.getLogger(__name__)


class Arc42Generator:
    """
    Generates Arc42 Section 5 using LLM providers.

    Supports multiple LLM backends:
    - Anthropic (Claude)
    - Google (Gemini)

    Workflow:
    1. Generate Level 1 Whitebox (system overview)
    2. Generate Level 2 Whiteboxes for each major component
    3. Generate Mermaid C4 diagram
    4. Assemble complete Section 5
    """

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        provider: Optional[BaseLLMProvider] = None,
        # Legacy support for direct api_key/model args
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the generator.

        Args:
            config: LLM configuration (preferred)
            provider: Pre-configured LLM provider (for testing)
            api_key: Legacy - API key (will use anthropic)
            model: Legacy - Model name
        """
        if provider:
            # Use provided provider (for testing or custom setup)
            self.provider = provider
        elif config:
            # Create provider from config
            self.provider = create_llm_provider(config)
        elif api_key:
            # Legacy support: create Anthropic provider
            from ..providers.anthropic_provider import AnthropicProvider
            self.provider = AnthropicProvider(
                api_key=api_key,
                model=model or "claude-sonnet-4-5-20250929"
            )
        else:
            raise ValueError(
                "Must provide either config, provider, or api_key"
            )

        logger.info(f"Arc42Generator initialized with {self.provider.provider_name} provider")

    def generate_section_5(self, analysis: AnalysisResult) -> Section5:
        """
        Generate complete Arc42 Section 5.

        Args:
            analysis: Codebase analysis result

        Returns:
            Section5 with Level 1, Level 2, and diagrams
        """
        logger.info("Generating Arc42 Section 5")

        # Generate Level 1 Whitebox
        logger.info("Generating Level 1 Whitebox...")
        level_1 = self._generate_level_1(analysis)

        # Generate Level 2 Whiteboxes for major components
        logger.info("Generating Level 2 Whiteboxes...")
        level_2_list = self._generate_level_2_list(analysis)

        # Generate Mermaid diagram
        logger.info("Generating architecture diagram...")
        diagram_code = self._generate_diagram(analysis)

        # Compile statistics
        statistics = {
            "total_loc": analysis.statistics.total_loc,
            "total_files": analysis.statistics.total_files,
            "total_modules": analysis.statistics.total_modules,
            "total_classes": analysis.statistics.total_classes,
            "total_functions": analysis.statistics.total_functions,
        }

        return Section5(
            level_1=level_1,
            level_2_list=level_2_list,
            diagram_code=diagram_code,
            statistics=statistics,
        )

    def _generate_level_1(self, analysis: AnalysisResult) -> Level1Whitebox:
        """Generate Level 1 Whitebox using Claude API."""
        prompt = self._build_level_1_prompt(analysis)

        response = self._call_llm(prompt, max_tokens=4000)

        # Parse response into structured format
        return self._parse_level_1_response(response, analysis)

    def _build_level_1_prompt(self, analysis: AnalysisResult) -> str:
        """Build prompt for Level 1 generation."""
        module_tree_text = self._format_module_tree(analysis.module_tree.root)
        dependency_list = self._format_dependencies(analysis.dependency_graph)

        return f"""You are an expert software architect generating Arc42 documentation.

Given the following codebase analysis:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
TOTAL FILES: {analysis.statistics.total_files}
TOTAL LOC: {analysis.statistics.total_loc}

MODULE STRUCTURE:
{module_tree_text}

DEPENDENCIES:
{dependency_list}

Generate Arc42 Section 5.1 (Level 1 Whitebox) content. Respond with EXACTLY this format:

OVERVIEW:
[1-2 paragraph description of system purpose and architecture]

COMPONENTS:
- [Component Name 1]: [Responsibility description]
- [Component Name 2]: [Responsibility description]
(list 3-7 main components based on the module structure)

INTERFACES:
[Description of how components communicate and key interfaces between them]

RATIONALE:
[Explanation of architectural decisions evident from the code structure]

REQUIREMENTS:
- Use ACTUAL module/package names from the analysis
- Be SPECIFIC about responsibilities (not generic)
- Focus on ARCHITECTURAL patterns visible in the code
- Keep descriptions CONCISE (1-2 sentences each)
- Only describe what is evident from the code structure"""

    def _format_module_tree(self, module: Module, indent: int = 0) -> str:
        """Format module tree for prompt."""
        lines = []
        prefix = "  " * indent

        # Format current module
        module_info = f"{prefix}- {module.name} ({module.type}, {module.size_loc} LOC)"

        if module.interfaces:
            interfaces = module.interfaces[:5]  # Limit to 5
            module_info += f"\n{prefix}  Interfaces: {', '.join(interfaces)}"

        lines.append(module_info)

        # Format children (limit depth)
        if indent < 2:
            for child in module.children[:10]:  # Limit children
                lines.append(self._format_module_tree(child, indent + 1))

        return "\n".join(lines)

    def _format_dependencies(self, dep_graph) -> str:
        """Format dependency graph for prompt."""
        if not dep_graph.edges:
            return "No internal dependencies detected"

        lines = []
        for edge in dep_graph.edges[:20]:  # Limit to 20
            lines.append(f"- {edge.from_module} -> {edge.to_module}")

        if len(dep_graph.edges) > 20:
            lines.append(f"... and {len(dep_graph.edges) - 20} more")

        return "\n".join(lines)

    def _parse_level_1_response(self, response: str, analysis: AnalysisResult) -> Level1Whitebox:
        """Parse Claude response into Level1Whitebox."""
        # Extract sections using regex
        overview = self._extract_section(response, "OVERVIEW")
        components_text = self._extract_section(response, "COMPONENTS")
        interfaces = self._extract_section(response, "INTERFACES")
        rationale = self._extract_section(response, "RATIONALE")

        # Parse components
        components = self._parse_components(components_text, analysis)

        return Level1Whitebox(
            overview=overview or "System overview not available.",
            components=components,
            important_interfaces=interfaces or "Interface descriptions not available.",
            rationale=rationale or "Architectural rationale not available.",
        )

    def _extract_section(self, text: str, section_name: str) -> Optional[str]:
        """Extract a section from the response."""
        pattern = rf"{section_name}:\s*\n(.*?)(?=\n[A-Z]+:|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _parse_components(self, text: Optional[str], analysis: AnalysisResult) -> List[ComponentDescription]:
        """Parse components from text."""
        components = []

        if not text:
            # Fallback: create components from top-level modules
            for module in analysis.module_tree.get_top_level_modules()[:7]:
                components.append(ComponentDescription(
                    name=module.name,
                    responsibility=f"Contains {module.size_loc} LOC with {len(module.interfaces)} interfaces",
                    interfaces=module.interfaces[:3],
                    dependencies=module.dependencies[:3],
                ))
            return components

        # Parse "- Name: Description" format
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                line = line[1:].strip()
                if ':' in line:
                    name, responsibility = line.split(':', 1)
                    components.append(ComponentDescription(
                        name=name.strip(),
                        responsibility=responsibility.strip(),
                    ))

        return components

    def _generate_level_2_list(self, analysis: AnalysisResult) -> List[Level2Whitebox]:
        """Generate Level 2 Whiteboxes for major components."""
        level_2_list = []
        top_modules = analysis.module_tree.get_top_level_modules()

        # Generate Level 2 for top 5 largest modules
        sorted_modules = sorted(top_modules, key=lambda m: m.size_loc, reverse=True)[:5]

        for module in sorted_modules:
            if module.size_loc > 0 and module.children:
                level_2 = self._generate_level_2(module, analysis)
                level_2_list.append(level_2)

        return level_2_list

    def _generate_level_2(self, module: Module, analysis: AnalysisResult) -> Level2Whitebox:
        """Generate Level 2 Whitebox for a specific module."""
        prompt = self._build_level_2_prompt(module)

        response = self._call_llm(prompt, max_tokens=2000)

        return self._parse_level_2_response(response, module)

    def _build_level_2_prompt(self, module: Module) -> str:
        """Build prompt for Level 2 generation."""
        children_info = []
        for child in module.children[:10]:
            info = f"- {child.name} ({child.type}, {child.size_loc} LOC)"
            if child.interfaces:
                info += f": {', '.join(child.interfaces[:3])}"
            children_info.append(info)

        return f"""You are an expert software architect generating Arc42 documentation.

Analyze this module and generate a Level 2 Whitebox description:

MODULE: {module.name}
TYPE: {module.type}
LOC: {module.size_loc}

CONTENTS:
{chr(10).join(children_info)}

INTERFACES: {', '.join(module.interfaces[:5]) if module.interfaces else 'None detected'}
DEPENDENCIES: {', '.join(module.dependencies[:5]) if module.dependencies else 'None detected'}

Generate a Level 2 Whitebox. Respond with EXACTLY this format:

PURPOSE:
[1-2 sentences describing this module's purpose]

INTERNAL_STRUCTURE:
- [SubComponent 1]: [Responsibility]
- [SubComponent 2]: [Responsibility]
(list main internal components)

DEPENDENCIES:
[List external dependencies this module relies on]"""

    def _parse_level_2_response(self, response: str, module: Module) -> Level2Whitebox:
        """Parse Claude response into Level2Whitebox."""
        purpose = self._extract_section(response, "PURPOSE")
        structure_text = self._extract_section(response, "INTERNAL_STRUCTURE")
        deps_text = self._extract_section(response, "DEPENDENCIES")

        # Parse internal structure
        internal_structure = []
        if structure_text:
            for line in structure_text.split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    line = line[1:].strip()
                    if ':' in line:
                        name, resp = line.split(':', 1)
                        internal_structure.append(ComponentDescription(
                            name=name.strip(),
                            responsibility=resp.strip(),
                        ))
        else:
            # Fallback: use children
            for child in module.children[:5]:
                internal_structure.append(ComponentDescription(
                    name=child.name,
                    responsibility=f"{child.type} with {child.size_loc} LOC",
                ))

        # Parse dependencies
        dependencies = []
        if deps_text:
            for line in deps_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if line:
                    dependencies.append(line)
        else:
            dependencies = module.dependencies[:5]

        return Level2Whitebox(
            component_name=module.name,
            purpose=purpose or f"Module containing {module.size_loc} lines of code",
            internal_structure=internal_structure,
            dependencies=dependencies,
        )

    def _generate_diagram(self, analysis: AnalysisResult) -> str:
        """Generate Mermaid C4 diagram."""
        prompt = self._build_diagram_prompt(analysis)

        response = self._call_llm(prompt, max_tokens=2000)

        # Extract mermaid code block
        diagram_code = self._extract_mermaid_code(response)

        if not diagram_code:
            # Fallback: generate basic diagram
            diagram_code = self._generate_fallback_diagram(analysis)

        return diagram_code

    def _build_diagram_prompt(self, analysis: AnalysisResult) -> str:
        """Build prompt for diagram generation."""
        modules = analysis.module_tree.get_top_level_modules()[:7]
        module_info = []
        for m in modules:
            module_info.append(f"- {m.name}: {m.size_loc} LOC, deps: {m.dependencies[:3]}")

        return f"""Generate a Mermaid flowchart diagram for this system architecture.

SYSTEM: {analysis.repo_name}
MODULES:
{chr(10).join(module_info)}

DEPENDENCIES:
{self._format_dependencies(analysis.dependency_graph)}

Generate a simple Mermaid flowchart. Output ONLY the mermaid code block, nothing else:

```mermaid
flowchart TB
    subgraph System["{analysis.repo_name}"]
        ... components and relationships ...
    end
```

Keep it simple with 3-7 nodes maximum. Use actual module names."""

    def _extract_mermaid_code(self, response: str) -> Optional[str]:
        """Extract mermaid code block from response."""
        # Look for ```mermaid ... ``` block
        pattern = r"```mermaid\s*(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return "```mermaid\n" + match.group(1).strip() + "\n```"
        return None

    def _generate_fallback_diagram(self, analysis: AnalysisResult) -> str:
        """Generate a basic fallback diagram."""
        modules = analysis.module_tree.get_top_level_modules()[:5]

        lines = [
            "```mermaid",
            "flowchart TB",
            f'    subgraph System["{analysis.repo_name}"]',
        ]

        for i, module in enumerate(modules):
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', module.name)
            lines.append(f'        {safe_name}["{module.name}"]')

        lines.append("    end")
        lines.append("```")

        return "\n".join(lines)

    # =========================================================================
    # Section 1: Introduction and Goals
    # =========================================================================

    def generate_section_1(self, analysis: AnalysisResult) -> Section01:
        """Generate Arc42 Section 1 - Introduction and Goals."""
        logger.info("Generating Section 1: Introduction and Goals")
        prompt = self._build_section_1_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=3000)
        return self._parse_section_1_response(response)

    def _build_section_1_prompt(self, analysis: AnalysisResult) -> str:
        return f"""You are an expert software architect generating Arc42 documentation.

Analyze this codebase and generate Section 1 (Introduction and Goals):

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
TOTAL FILES: {analysis.statistics.total_files}
TOTAL LOC: {analysis.statistics.total_loc}
MODULES: {', '.join([m.name for m in analysis.module_tree.get_top_level_modules()[:10]])}

Generate Arc42 Section 1. Respond with EXACTLY this format:

OVERVIEW:
[1-2 paragraph description of what this system does and its purpose]

BUSINESS_GOALS:
- [Goal 1]
- [Goal 2]
- [Goal 3]

KEY_FEATURES:
- [Feature 1]
- [Feature 2]
- [Feature 3]

QUALITY_GOALS:
- [Attribute]|[Priority: Critical/High/Medium]|[Target]|[Measurement]
- [Attribute]|[Priority]|[Target]|[Measurement]

STAKEHOLDERS:
- [Role]|[Expectations]
- [Role]|[Expectations]

Base your analysis on the code structure and module names visible."""

    def _parse_section_1_response(self, response: str) -> Section01:
        overview = self._extract_section(response, "OVERVIEW") or "System overview not available."

        business_goals = []
        goals_text = self._extract_section(response, "BUSINESS_GOALS")
        if goals_text:
            for line in goals_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if line:
                    business_goals.append(line)

        key_features = []
        features_text = self._extract_section(response, "KEY_FEATURES")
        if features_text:
            for line in features_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if line:
                    key_features.append(line)

        quality_goals = []
        quality_text = self._extract_section(response, "QUALITY_GOALS")
        if quality_text:
            for line in quality_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 3:
                        quality_goals.append(QualityGoal(
                            attribute=parts[0],
                            priority=parts[1] if len(parts) > 1 else "Medium",
                            target=parts[2] if len(parts) > 2 else "",
                            measurement=parts[3] if len(parts) > 3 else "",
                        ))

        stakeholders = []
        stake_text = self._extract_section(response, "STAKEHOLDERS")
        if stake_text:
            for line in stake_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:
                        stakeholders.append(Stakeholder(
                            role=parts[0],
                            expectations=parts[1] if len(parts) > 1 else "",
                        ))

        return Section01(
            requirements_overview=overview,
            business_goals=business_goals,
            key_features=key_features,
            quality_goals=quality_goals,
            stakeholders=stakeholders,
        )

    # =========================================================================
    # Section 2: Architecture Constraints
    # =========================================================================

    def generate_section_2(self, analysis: AnalysisResult) -> Section02:
        """Generate Arc42 Section 2 - Architecture Constraints."""
        logger.info("Generating Section 2: Architecture Constraints")
        prompt = self._build_section_2_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=2500)
        return self._parse_section_2_response(response)

    def _build_section_2_prompt(self, analysis: AnalysisResult) -> str:
        deps = analysis.module_tree.root.dependencies[:20] if analysis.module_tree.root.dependencies else []
        return f"""You are an expert software architect generating Arc42 documentation.

Analyze this codebase and infer Architecture Constraints:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
DEPENDENCIES: {', '.join(deps)}
STRUCTURE: {', '.join([m.name for m in analysis.module_tree.get_top_level_modules()[:10]])}

Generate Arc42 Section 2. Respond with EXACTLY this format:

TECHNICAL_CONSTRAINTS:
- [Name]|[Description]|[Impact]
- [Name]|[Description]|[Impact]

ORGANIZATIONAL_CONSTRAINTS:
- [Name]|[Description]
- [Name]|[Description]

CONVENTIONS:
- [Name]|[Description]
- [Name]|[Description]

Infer constraints from the technology stack and code structure."""

    def _parse_section_2_response(self, response: str) -> Section02:
        technical = []
        tech_text = self._extract_section(response, "TECHNICAL_CONSTRAINTS")
        if tech_text:
            for line in tech_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:
                        technical.append(Constraint(
                            name=parts[0],
                            description=parts[1],
                            impact=parts[2] if len(parts) > 2 else "",
                            category="technical",
                        ))

        organizational = []
        org_text = self._extract_section(response, "ORGANIZATIONAL_CONSTRAINTS")
        if org_text:
            for line in org_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:
                        organizational.append(Constraint(
                            name=parts[0],
                            description=parts[1],
                            category="organizational",
                        ))

        conventions = []
        conv_text = self._extract_section(response, "CONVENTIONS")
        if conv_text:
            for line in conv_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:
                        conventions.append(Constraint(
                            name=parts[0],
                            description=parts[1],
                            category="convention",
                        ))

        return Section02(
            technical_constraints=technical,
            organizational_constraints=organizational,
            conventions=conventions,
        )

    # =========================================================================
    # Section 3: Context and Scope
    # =========================================================================

    def generate_section_3(self, analysis: AnalysisResult) -> Section03:
        """Generate Arc42 Section 3 - Context and Scope."""
        logger.info("Generating Section 3: Context and Scope")
        prompt = self._build_section_3_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=3000)
        return self._parse_section_3_response(response, analysis)

    def _build_section_3_prompt(self, analysis: AnalysisResult) -> str:
        deps = analysis.module_tree.root.dependencies[:20] if analysis.module_tree.root.dependencies else []
        return f"""You are an expert software architect generating Arc42 documentation.

Analyze this codebase and identify System Context:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
EXTERNAL DEPENDENCIES: {', '.join(deps)}
MODULES: {', '.join([m.name for m in analysis.module_tree.get_top_level_modules()[:10]])}

Generate Arc42 Section 3. Respond with EXACTLY this format:

SYSTEM_PURPOSE:
[One paragraph describing what this system does]

BUSINESS_CONTEXT:
[Description of business context and users]

EXTERNAL_SYSTEMS:
- [Name]|[Description]|[Protocol]|[Purpose]
- [Name]|[Description]|[Protocol]|[Purpose]

CONTEXT_DIAGRAM:
```mermaid
C4Context
title System Context for {analysis.repo_name}
Person(user, "User", "Uses the system")
System(system, "{analysis.repo_name}", "The main system")
[Add external systems as System_Ext nodes]
[Add relationships with Rel]
```

Identify external systems from dependencies (databases, APIs, message queues, etc.)."""

    def _parse_section_3_response(self, response: str, analysis: AnalysisResult) -> Section03:
        purpose = self._extract_section(response, "SYSTEM_PURPOSE") or f"{analysis.repo_name} system"
        context = self._extract_section(response, "BUSINESS_CONTEXT") or ""

        external_systems = []
        ext_text = self._extract_section(response, "EXTERNAL_SYSTEMS")
        if ext_text:
            for line in ext_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:
                        external_systems.append(ExternalSystem(
                            name=parts[0],
                            description=parts[1],
                            protocol=parts[2] if len(parts) > 2 else "",
                            purpose=parts[3] if len(parts) > 3 else "",
                        ))

        diagram = self._extract_mermaid_code(response) or ""

        return Section03(
            system_purpose=purpose,
            business_context=context,
            external_systems=external_systems,
            context_diagram=diagram,
        )

    # =========================================================================
    # Section 4: Solution Strategy
    # =========================================================================

    def generate_section_4(self, analysis: AnalysisResult) -> Section04:
        """Generate Arc42 Section 4 - Solution Strategy."""
        logger.info("Generating Section 4: Solution Strategy")
        prompt = self._build_section_4_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=2500)
        return self._parse_section_4_response(response)

    def _build_section_4_prompt(self, analysis: AnalysisResult) -> str:
        deps = analysis.module_tree.root.dependencies[:20] if analysis.module_tree.root.dependencies else []
        modules = [m.name for m in analysis.module_tree.get_top_level_modules()[:10]]
        return f"""You are an expert software architect generating Arc42 documentation.

Analyze this codebase and identify the Solution Strategy:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
DEPENDENCIES: {', '.join(deps)}
MODULE STRUCTURE: {', '.join(modules)}

Generate Arc42 Section 4. Respond with EXACTLY this format:

TECHNOLOGY_DECISIONS:
- [Technology]|[Rationale]
- [Technology]|[Rationale]

ARCHITECTURAL_PATTERNS:
- [Pattern description]
- [Pattern description]

QUALITY_STRATEGIES:
- [Quality Attribute]|[Strategy to achieve it]
- [Quality Attribute]|[Strategy to achieve it]

Infer technology choices and patterns from the code structure and dependencies."""

    def _parse_section_4_response(self, response: str) -> Section04:
        tech_decisions = []
        tech_text = self._extract_section(response, "TECHNOLOGY_DECISIONS")
        if tech_text:
            for line in tech_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:
                        tech_decisions.append(TechnologyDecision(
                            technology=parts[0],
                            rationale=parts[1],
                        ))

        patterns = []
        patterns_text = self._extract_section(response, "ARCHITECTURAL_PATTERNS")
        if patterns_text:
            for line in patterns_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if line:
                    patterns.append(line)

        strategies = {}
        strat_text = self._extract_section(response, "QUALITY_STRATEGIES")
        if strat_text:
            for line in strat_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:
                        strategies[parts[0]] = parts[1]

        return Section04(
            technology_decisions=tech_decisions,
            architectural_patterns=patterns,
            quality_strategies=strategies,
        )

    # =========================================================================
    # Section 6: Runtime View
    # =========================================================================

    def generate_section_6(self, analysis: AnalysisResult) -> Section06:
        """Generate Arc42 Section 6 - Runtime View."""
        logger.info("Generating Section 6: Runtime View")
        prompt = self._build_section_6_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=3000)
        return self._parse_section_6_response(response)

    def _build_section_6_prompt(self, analysis: AnalysisResult) -> str:
        modules = [m.name for m in analysis.module_tree.get_top_level_modules()[:10]]
        return f"""You are an expert software architect generating Arc42 documentation.

Analyze this codebase and describe Runtime Scenarios:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
MODULES: {', '.join(modules)}
DEPENDENCIES: {self._format_dependencies(analysis.dependency_graph)}

Generate Arc42 Section 6. Respond with EXACTLY this format:

OVERVIEW:
[Brief description of how the system operates at runtime]

SCENARIO_1:
NAME: [Scenario name like "User Authentication" or "Data Processing"]
DESCRIPTION: [What happens in this scenario]
DIAGRAM:
```mermaid
sequenceDiagram
    participant User
    participant API
    [Add participants and interactions]
```

SCENARIO_2:
NAME: [Another key scenario]
DESCRIPTION: [What happens]
DIAGRAM:
```mermaid
sequenceDiagram
    [Sequence diagram]
```

Identify 2-3 key runtime scenarios based on the module structure."""

    def _parse_section_6_response(self, response: str) -> Section06:
        overview = self._extract_section(response, "OVERVIEW") or ""

        scenarios = []
        for i in range(1, 5):
            scenario_text = self._extract_section(response, f"SCENARIO_{i}")
            if scenario_text:
                name = ""
                desc = ""
                diagram = ""

                name_match = re.search(r"NAME:\s*(.+?)(?=\n|DESCRIPTION)", scenario_text)
                if name_match:
                    name = name_match.group(1).strip()

                desc_match = re.search(r"DESCRIPTION:\s*(.+?)(?=\nDIAGRAM|$)", scenario_text, re.DOTALL)
                if desc_match:
                    desc = desc_match.group(1).strip()

                diagram = self._extract_mermaid_code(scenario_text) or ""

                if name:
                    scenarios.append(RuntimeScenario(
                        name=name,
                        description=desc,
                        sequence_diagram=diagram,
                    ))

        return Section06(overview=overview, scenarios=scenarios)

    # =========================================================================
    # Section 7: Deployment View
    # =========================================================================

    def generate_section_7(self, analysis: AnalysisResult) -> Section07:
        """Generate Arc42 Section 7 - Deployment View."""
        logger.info("Generating Section 7: Deployment View")
        prompt = self._build_section_7_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=2500)
        return self._parse_section_7_response(response, analysis)

    def _build_section_7_prompt(self, analysis: AnalysisResult) -> str:
        deps = analysis.module_tree.root.dependencies[:15] if analysis.module_tree.root.dependencies else []
        return f"""You are an expert software architect generating Arc42 documentation.

Analyze this codebase and describe Deployment:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
DEPENDENCIES: {', '.join(deps)}

Generate Arc42 Section 7. Respond with EXACTLY this format:

INFRASTRUCTURE_OVERVIEW:
[Description of likely infrastructure based on the tech stack]

DEPLOYMENT_DIAGRAM:
```mermaid
flowchart TB
    subgraph Production
        [Add deployment nodes]
    end
```

DEPLOYMENT_PROCESS:
- [Step 1]
- [Step 2]
- [Step 3]

Infer deployment based on the technology stack (e.g., Docker, cloud services, databases)."""

    def _parse_section_7_response(self, response: str, analysis: AnalysisResult) -> Section07:
        overview = self._extract_section(response, "INFRASTRUCTURE_OVERVIEW") or ""
        diagram = self._extract_mermaid_code(response) or ""

        process = []
        process_text = self._extract_section(response, "DEPLOYMENT_PROCESS")
        if process_text:
            for line in process_text.split('\n'):
                line = line.strip().lstrip('-').lstrip('0123456789.').strip()
                if line:
                    process.append(line)

        return Section07(
            infrastructure_overview=overview,
            deployment_diagram=diagram,
            deployment_process=process,
        )

    # =========================================================================
    # Section 8: Cross-Cutting Concepts
    # =========================================================================

    def generate_section_8(self, analysis: AnalysisResult) -> Section08:
        """Generate Arc42 Section 8 - Cross-Cutting Concepts."""
        logger.info("Generating Section 8: Cross-Cutting Concepts")
        prompt = self._build_section_8_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=3000)
        return self._parse_section_8_response(response)

    def _build_section_8_prompt(self, analysis: AnalysisResult) -> str:
        modules = [m.name for m in analysis.module_tree.get_top_level_modules()[:10]]
        deps = analysis.module_tree.root.dependencies[:15] if analysis.module_tree.root.dependencies else []
        return f"""You are an expert software architect generating Arc42 documentation.

Analyze this codebase and identify Cross-Cutting Concepts:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
MODULES: {', '.join(modules)}
DEPENDENCIES: {', '.join(deps)}

Generate Arc42 Section 8. Respond with EXACTLY this format:

CONCEPT_Logging:
[Description of logging approach]

CONCEPT_Error Handling:
[Description of error handling approach]

CONCEPT_Security:
[Description of security approach]

CONCEPT_Testing:
[Description of testing approach]

Add other relevant concepts based on the codebase (e.g., Caching, Configuration, etc.)."""

    def _parse_section_8_response(self, response: str) -> Section08:
        concepts = {}
        pattern = r"CONCEPT_([^:]+):\s*\n(.*?)(?=CONCEPT_|$)"
        matches = re.findall(pattern, response, re.DOTALL)
        for name, description in matches:
            concepts[name.strip()] = description.strip()

        return Section08(concepts=concepts)

    # =========================================================================
    # Section 9: Architecture Decisions
    # =========================================================================

    def generate_section_9(self, analysis: AnalysisResult) -> Section09:
        """Generate Arc42 Section 9 - Architecture Decisions."""
        logger.info("Generating Section 9: Architecture Decisions")
        prompt = self._build_section_9_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=3000)
        return self._parse_section_9_response(response)

    def _build_section_9_prompt(self, analysis: AnalysisResult) -> str:
        deps = analysis.module_tree.root.dependencies[:15] if analysis.module_tree.root.dependencies else []
        modules = [m.name for m in analysis.module_tree.get_top_level_modules()[:10]]
        return f"""You are an expert software architect generating Arc42 documentation.

Analyze this codebase and infer Architecture Decisions:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
DEPENDENCIES: {', '.join(deps)}
MODULES: {', '.join(modules)}

Generate Arc42 Section 9. Respond with EXACTLY this format:

ADR_001:
TITLE: [Decision title]
STATUS: Accepted
CONTEXT: [Why this decision was needed]
DECISION: [What was decided]
CONSEQUENCES: [Positive and negative consequences, separated by |]

ADR_002:
TITLE: [Another decision]
STATUS: Accepted
CONTEXT: [Context]
DECISION: [Decision]
CONSEQUENCES: [Consequences]

Infer 3-5 major architecture decisions from the technology stack and code structure."""

    def _parse_section_9_response(self, response: str) -> Section09:
        decisions = []
        pattern = r"ADR_(\d+):\s*\n(.*?)(?=ADR_\d+:|$)"
        matches = re.findall(pattern, response, re.DOTALL)

        for adr_id, content in matches:
            title = ""
            status = "Accepted"
            context = ""
            decision = ""
            consequences = []

            title_match = re.search(r"TITLE:\s*(.+?)(?=\n|STATUS)", content)
            if title_match:
                title = title_match.group(1).strip()

            status_match = re.search(r"STATUS:\s*(.+?)(?=\n|CONTEXT)", content)
            if status_match:
                status = status_match.group(1).strip()

            context_match = re.search(r"CONTEXT:\s*(.+?)(?=\nDECISION|$)", content, re.DOTALL)
            if context_match:
                context = context_match.group(1).strip()

            decision_match = re.search(r"DECISION:\s*(.+?)(?=\nCONSEQUENCES|$)", content, re.DOTALL)
            if decision_match:
                decision = decision_match.group(1).strip()

            cons_match = re.search(r"CONSEQUENCES:\s*(.+?)$", content, re.DOTALL)
            if cons_match:
                cons_text = cons_match.group(1).strip()
                consequences = [c.strip() for c in cons_text.split('|') if c.strip()]

            if title:
                decisions.append(ArchitectureDecision(
                    id=f"ADR-{adr_id.zfill(3)}",
                    title=title,
                    status=status,
                    context=context,
                    decision=decision,
                    consequences=consequences,
                ))

        return Section09(decisions=decisions)

    # =========================================================================
    # Section 10: Quality Requirements
    # =========================================================================

    def generate_section_10(self, analysis: AnalysisResult) -> Section10:
        """Generate Arc42 Section 10 - Quality Requirements."""
        logger.info("Generating Section 10: Quality Requirements")
        prompt = self._build_section_10_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=2500)
        return self._parse_section_10_response(response)

    def _build_section_10_prompt(self, analysis: AnalysisResult) -> str:
        return f"""You are an expert software architect generating Arc42 documentation.

Analyze this codebase and define Quality Requirements:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
LOC: {analysis.statistics.total_loc}
FILES: {analysis.statistics.total_files}

Generate Arc42 Section 10. Respond with EXACTLY this format:

QUALITY_TREE:
Quality
├── Performance
│   ├── Response Time
│   └── Throughput
├── Reliability
│   ├── Availability
│   └── Fault Tolerance
├── Security
│   └── Data Protection
└── Maintainability
    ├── Testability
    └── Modifiability

QUALITY_SCENARIOS:
- [Scenario]|[Stimulus]|[Response]|[Measure]
- [Scenario]|[Stimulus]|[Response]|[Measure]

Define realistic quality scenarios for this type of system."""

    def _parse_section_10_response(self, response: str) -> Section10:
        tree = self._extract_section(response, "QUALITY_TREE") or ""

        scenarios = []
        scenarios_text = self._extract_section(response, "QUALITY_SCENARIOS")
        if scenarios_text:
            for line in scenarios_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4:
                        scenarios.append({
                            "scenario": parts[0],
                            "stimulus": parts[1],
                            "response": parts[2],
                            "measure": parts[3],
                        })

        return Section10(quality_tree=tree, quality_scenarios=scenarios)

    # =========================================================================
    # Section 11: Risks and Technical Debt
    # =========================================================================

    def generate_section_11(self, analysis: AnalysisResult) -> Section11:
        """Generate Arc42 Section 11 - Risks and Technical Debt."""
        logger.info("Generating Section 11: Risks and Technical Debt")
        prompt = self._build_section_11_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=2500)
        return self._parse_section_11_response(response)

    def _build_section_11_prompt(self, analysis: AnalysisResult) -> str:
        deps = analysis.module_tree.root.dependencies[:15] if analysis.module_tree.root.dependencies else []
        return f"""You are an expert software architect generating Arc42 documentation.

Analyze this codebase and identify Risks and Technical Debt:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
LOC: {analysis.statistics.total_loc}
FILES: {analysis.statistics.total_files}
DEPENDENCIES: {', '.join(deps)}

Generate Arc42 Section 11. Respond with EXACTLY this format:

RISKS:
- [Risk Name]|[Probability: Low/Medium/High]|[Impact: Low/Medium/High]|[Mitigation]
- [Risk Name]|[Probability]|[Impact]|[Mitigation]

TECHNICAL_DEBT:
- [Description]|[Priority: High/Medium/Low]|[Location/Area]
- [Description]|[Priority]|[Location/Area]

Identify realistic risks and potential technical debt based on the codebase size and structure."""

    def _parse_section_11_response(self, response: str) -> Section11:
        risks = []
        risks_text = self._extract_section(response, "RISKS")
        if risks_text:
            for line in risks_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 3:
                        risks.append(Risk(
                            name=parts[0],
                            probability=parts[1] if len(parts) > 1 else "Medium",
                            impact=parts[2] if len(parts) > 2 else "Medium",
                            mitigation=parts[3] if len(parts) > 3 else "",
                        ))

        debt = []
        debt_text = self._extract_section(response, "TECHNICAL_DEBT")
        if debt_text:
            for line in debt_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:
                        debt.append(TechnicalDebt(
                            description=parts[0],
                            priority=parts[1] if len(parts) > 1 else "Medium",
                            location=parts[2] if len(parts) > 2 else "",
                        ))

        return Section11(risks=risks, technical_debt=debt)

    # =========================================================================
    # Section 12: Glossary
    # =========================================================================

    def generate_section_12(self, analysis: AnalysisResult) -> Section12:
        """Generate Arc42 Section 12 - Glossary."""
        logger.info("Generating Section 12: Glossary")
        prompt = self._build_section_12_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=2000)
        return self._parse_section_12_response(response)

    def _build_section_12_prompt(self, analysis: AnalysisResult) -> str:
        modules = [m.name for m in analysis.module_tree.get_top_level_modules()[:10]]
        return f"""You are an expert software architect generating Arc42 documentation.

Analyze this codebase and create a Glossary:

REPOSITORY: {analysis.repo_name}
LANGUAGE: {analysis.language}
MODULES: {', '.join(modules)}

Generate Arc42 Section 12. Respond with EXACTLY this format:

TECHNICAL_TERMS:
- [Term]|[Definition]
- [Term]|[Definition]

DOMAIN_TERMS:
- [Term]|[Definition]
- [Term]|[Definition]

Include common technical terms and any domain-specific terms from module names."""

    def _parse_section_12_response(self, response: str) -> Section12:
        terms = []

        tech_text = self._extract_section(response, "TECHNICAL_TERMS")
        if tech_text:
            for line in tech_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:
                        terms.append(GlossaryTerm(
                            term=parts[0],
                            definition=parts[1],
                            category="technical",
                        ))

        domain_text = self._extract_section(response, "DOMAIN_TERMS")
        if domain_text:
            for line in domain_text.split('\n'):
                line = line.strip().lstrip('-').strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:
                        terms.append(GlossaryTerm(
                            term=parts[0],
                            definition=parts[1],
                            category="domain",
                        ))

        return Section12(terms=terms)

    # =========================================================================
    # Generate All Sections
    # =========================================================================

    def generate_all_sections(self, analysis: AnalysisResult, sections: List[int] = None) -> Arc42Document:
        """
        Generate multiple Arc42 sections.

        Args:
            analysis: Codebase analysis result
            sections: List of section numbers to generate (1-12), or None for all

        Returns:
            Arc42Document with requested sections
        """
        if sections is None:
            sections = list(range(1, 13))

        logger.info(f"Generating Arc42 sections: {sections}")

        doc = Arc42Document()

        section_generators = {
            1: ("section_01", self.generate_section_1),
            2: ("section_02", self.generate_section_2),
            3: ("section_03", self.generate_section_3),
            4: ("section_04", self.generate_section_4),
            5: ("section_05", self.generate_section_5),
            6: ("section_06", self.generate_section_6),
            7: ("section_07", self.generate_section_7),
            8: ("section_08", self.generate_section_8),
            9: ("section_09", self.generate_section_9),
            10: ("section_10", self.generate_section_10),
            11: ("section_11", self.generate_section_11),
            12: ("section_12", self.generate_section_12),
        }

        for section_num in sections:
            if section_num in section_generators:
                attr_name, generator = section_generators[section_num]
                section = generator(analysis)
                setattr(doc, attr_name, section)

        return doc

    # =========================================================================
    # LLM Helpers
    # =========================================================================

    def _call_llm(self, prompt: str, max_tokens: int = 4000) -> str:
        """
        Call the LLM provider.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            Generated text response
        """
        try:
            response = self.provider.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.content
        except Exception as e:
            logger.error(f"LLM API error ({self.provider.provider_name}): {e}")
            raise

    # Backward compatibility alias
    def _call_claude(self, prompt: str, max_tokens: int = 4000) -> str:
        """Legacy method name for backward compatibility."""
        return self._call_llm(prompt, max_tokens)
