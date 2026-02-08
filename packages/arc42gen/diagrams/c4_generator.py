"""
C4 diagram generator using LLM.

Generates diagrams at all 4 C4 model levels:
- Level 1: System Context - shows the system in context with external actors and systems
- Level 2: Container - shows high-level technology choices (web apps, databases, etc.)
- Level 3: Component - shows components within a container
- Level 4: Code - shows class/code structure within a component
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from ..models.analysis import AnalysisResult, Module
from ..models.config import LLMConfig
from ..providers.base import BaseLLMProvider
from ..providers.factory import create_llm_provider
from ..templates import load_prompt


logger = logging.getLogger(__name__)


@dataclass
class C4Diagram:
    """A C4 diagram with metadata."""
    level: int  # 1-4
    title: str
    description: str
    mermaid_code: str
    target_component: str = ""  # For levels 3-4, which component this is for

    def to_dict(self) -> Dict:
        return {
            "level": self.level,
            "title": self.title,
            "description": self.description,
            "mermaid_code": self.mermaid_code,
            "target_component": self.target_component,
        }

    def to_markdown(self) -> str:
        md = [f"# {self.title}\n"]
        md.append(f"{self.description}\n")
        md.append(self.mermaid_code)
        return "\n".join(md)


@dataclass
class C4DiagramSet:
    """Complete set of C4 diagrams."""
    context: Optional[C4Diagram] = None  # Level 1
    containers: Optional[C4Diagram] = None  # Level 2
    components: List[C4Diagram] = field(default_factory=list)  # Level 3
    code: List[C4Diagram] = field(default_factory=list)  # Level 4

    def to_dict(self) -> Dict:
        return {
            "context": self.context.to_dict() if self.context else None,
            "containers": self.containers.to_dict() if self.containers else None,
            "components": [c.to_dict() for c in self.components],
            "code": [c.to_dict() for c in self.code],
        }


class C4Generator:
    """Generates C4 diagrams at all 4 levels using LLM."""

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

        logger.info(f"C4Generator initialized with {self.provider.provider_name}")

    def generate_all_levels(
        self,
        analysis: AnalysisResult,
        levels: List[int] = None
    ) -> C4DiagramSet:
        """
        Generate C4 diagrams at specified levels.

        Args:
            analysis: Codebase analysis result
            levels: Which levels to generate (1-4), None for all

        Returns:
            C4DiagramSet with generated diagrams
        """
        if levels is None:
            levels = [1, 2, 3, 4]

        logger.info(f"Generating C4 diagrams for levels: {levels}")

        result = C4DiagramSet()

        if 1 in levels:
            result.context = self.generate_level_1(analysis)

        if 2 in levels:
            result.containers = self.generate_level_2(analysis)

        if 3 in levels:
            result.components = self.generate_level_3(analysis)

        if 4 in levels:
            result.code = self.generate_level_4(analysis)

        return result

    # =========================================================================
    # Level 1: System Context
    # =========================================================================

    def generate_level_1(self, analysis: AnalysisResult) -> C4Diagram:
        """Generate Level 1 (System Context) diagram."""
        logger.info("Generating Level 1: System Context diagram")
        prompt = self._build_level_1_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=2000)
        mermaid = self._extract_mermaid(response)

        return C4Diagram(
            level=1,
            title="System Context Diagram",
            description="Shows the system in context with its users and external systems.",
            mermaid_code=mermaid or self._fallback_level_1(analysis),
        )

    def _build_level_1_prompt(self, analysis: AnalysisResult) -> str:
        deps = analysis.module_tree.root.dependencies[:15] if analysis.module_tree.root.dependencies else []
        return load_prompt("c4/level_1",
            repo_name=analysis.repo_name,
            language=analysis.language,
            dependencies=', '.join(deps),
        )

    def _fallback_level_1(self, analysis: AnalysisResult) -> str:
        return f"""```mermaid
C4Context
title System Context for {analysis.repo_name}

Person(user, "User", "Interacts with the system")
System(system, "{analysis.repo_name}", "The main system")

Rel(user, system, "Uses")
```"""

    # =========================================================================
    # Level 2: Container
    # =========================================================================

    def generate_level_2(self, analysis: AnalysisResult) -> C4Diagram:
        """Generate Level 2 (Container) diagram."""
        logger.info("Generating Level 2: Container diagram")
        prompt = self._build_level_2_prompt(analysis)
        response = self._call_llm(prompt, max_tokens=2000)
        mermaid = self._extract_mermaid(response)

        return C4Diagram(
            level=2,
            title="Container Diagram",
            description="Shows the high-level technology choices and how containers communicate.",
            mermaid_code=mermaid or self._fallback_level_2(analysis),
        )

    def _build_level_2_prompt(self, analysis: AnalysisResult) -> str:
        modules = [m.name for m in analysis.module_tree.get_top_level_modules()[:10]]
        deps = analysis.module_tree.root.dependencies[:15] if analysis.module_tree.root.dependencies else []

        return load_prompt("c4/level_2",
            repo_name=analysis.repo_name,
            language=analysis.language,
            modules=', '.join(modules),
            dependencies=', '.join(deps),
        )

    def _fallback_level_2(self, analysis: AnalysisResult) -> str:
        return f"""```mermaid
C4Container
title Container Diagram for {analysis.repo_name}

Person(user, "User")

System_Boundary(system, "{analysis.repo_name}") {{
    Container(app, "Application", "{analysis.language}", "Main application logic")
}}

Rel(user, app, "Uses")
```"""

    # =========================================================================
    # Level 3: Component
    # =========================================================================

    def generate_level_3(self, analysis: AnalysisResult) -> List[C4Diagram]:
        """Generate Level 3 (Component) diagrams for major modules."""
        logger.info("Generating Level 3: Component diagrams")

        diagrams = []
        top_modules = analysis.module_tree.get_top_level_modules()[:3]

        for module in top_modules:
            if module.children:
                diagram = self._generate_component_diagram(module, analysis)
                diagrams.append(diagram)

        if not diagrams:
            # Generate a single component diagram for the whole system
            diagrams.append(self._generate_system_component_diagram(analysis))

        return diagrams

    def _generate_component_diagram(self, module: Module, analysis: AnalysisResult) -> C4Diagram:
        prompt = self._build_level_3_prompt(module, analysis)
        response = self._call_llm(prompt, max_tokens=2000)
        mermaid = self._extract_mermaid(response)

        return C4Diagram(
            level=3,
            title=f"Component Diagram: {module.name}",
            description=f"Shows internal components of the {module.name} module.",
            mermaid_code=mermaid or self._fallback_level_3(module),
            target_component=module.name,
        )

    def _generate_system_component_diagram(self, analysis: AnalysisResult) -> C4Diagram:
        modules = analysis.module_tree.get_top_level_modules()[:7]
        prompt = load_prompt("c4/level_3_system",
            repo_name=analysis.repo_name,
            modules=', '.join([m.name for m in modules]),
        )
        response = self._call_llm(prompt, max_tokens=2000)
        mermaid = self._extract_mermaid(response)

        return C4Diagram(
            level=3,
            title="Component Diagram",
            description="Shows the internal components of the system.",
            mermaid_code=mermaid or self._fallback_level_3_system(analysis),
        )

    def _build_level_3_prompt(self, module: Module, analysis: AnalysisResult) -> str:
        children = [c.name for c in module.children[:10]]
        return load_prompt("c4/level_3",
            module_name=module.name,
            module_safe_name=module.name.replace('-', '_'),
            components=', '.join(children),
            interfaces=', '.join(module.interfaces[:5]) if module.interfaces else 'None',
        )

    def _fallback_level_3(self, module: Module) -> str:
        safe_name = module.name.replace('-', '_').replace('.', '_')
        components = []
        for i, child in enumerate(module.children[:5]):
            safe_child = child.name.replace('-', '_').replace('.', '_')
            components.append(f'    Component({safe_child}, "{child.name}", "{child.type}")')

        return f"""```mermaid
C4Component
title Component Diagram for {module.name}

Container_Boundary({safe_name}, "{module.name}") {{
{chr(10).join(components)}
}}
```"""

    def _fallback_level_3_system(self, analysis: AnalysisResult) -> str:
        modules = analysis.module_tree.get_top_level_modules()[:5]
        components = []
        for module in modules:
            safe_name = module.name.replace('-', '_').replace('.', '_')
            components.append(f'    Component({safe_name}, "{module.name}", "Module")')

        return f"""```mermaid
C4Component
title Component Diagram for {analysis.repo_name}

Container_Boundary(app, "Application") {{
{chr(10).join(components)}
}}
```"""

    # =========================================================================
    # Level 4: Code
    # =========================================================================

    def generate_level_4(self, analysis: AnalysisResult) -> List[C4Diagram]:
        """Generate Level 4 (Code/Class) diagrams for major modules."""
        logger.info("Generating Level 4: Code diagrams")

        diagrams = []
        top_modules = analysis.module_tree.get_top_level_modules()[:3]

        for module in top_modules:
            # Only generate if module has meaningful structure
            if module.interfaces or module.children:
                diagram = self._generate_code_diagram(module, analysis)
                diagrams.append(diagram)

        return diagrams

    def _generate_code_diagram(self, module: Module, analysis: AnalysisResult) -> C4Diagram:
        prompt = self._build_level_4_prompt(module)
        response = self._call_llm(prompt, max_tokens=2000)
        mermaid = self._extract_mermaid(response)

        return C4Diagram(
            level=4,
            title=f"Code Diagram: {module.name}",
            description=f"Shows class/code structure within {module.name}.",
            mermaid_code=mermaid or self._fallback_level_4(module),
            target_component=module.name,
        )

    def _build_level_4_prompt(self, module: Module) -> str:
        interfaces = module.interfaces[:10] if module.interfaces else []
        return load_prompt("c4/level_4",
            module_name=module.name,
            interfaces=', '.join(interfaces),
            module_loc=module.size_loc,
        )

    def _fallback_level_4(self, module: Module) -> str:
        safe_name = module.name.replace('-', '_').replace('.', '_').title()
        interfaces = module.interfaces[:3] if module.interfaces else [safe_name]

        classes = []
        for iface in interfaces:
            safe_iface = iface.replace('-', '_').replace('.', '_')
            classes.append(f"""    class {safe_iface} {{
        +execute()
    }}""")

        return f"""```mermaid
classDiagram
{chr(10).join(classes)}
```"""

    # =========================================================================
    # Helpers
    # =========================================================================

    def _extract_mermaid(self, response: str) -> Optional[str]:
        """Extract mermaid code block from response."""
        pattern = r"```mermaid\s*(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return "```mermaid\n" + match.group(1).strip() + "\n```"
        return None

    def _call_llm(self, prompt: str, max_tokens: int = 2000) -> str:
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
