"""
Arc42 documentation generation using Claude API.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional

import anthropic

from ..models.analysis import AnalysisResult, Module
from ..models.documentation import (
    Section5,
    Level1Whitebox,
    Level2Whitebox,
    ComponentDescription,
)


logger = logging.getLogger(__name__)


class Arc42Generator:
    """
    Generates Arc42 Section 5 using Claude API.

    Workflow:
    1. Generate Level 1 Whitebox (system overview)
    2. Generate Level 2 Whiteboxes for each major component
    3. Generate Mermaid C4 diagram
    4. Assemble complete Section 5
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize the generator.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

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

        response = self._call_claude(prompt, max_tokens=4000)

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

        response = self._call_claude(prompt, max_tokens=2000)

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

        response = self._call_claude(prompt, max_tokens=2000)

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

    def _call_claude(self, prompt: str, max_tokens: int = 4000) -> str:
        """Call Claude API with retry logic."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Claude: {e}")
            raise
