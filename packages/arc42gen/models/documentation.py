"""
Documentation output models for Arc42 generation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ComponentDescription:
    """Description of a building block component."""
    name: str
    responsibility: str
    interfaces: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    technology: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "responsibility": self.responsibility,
            "interfaces": self.interfaces,
            "dependencies": self.dependencies,
            "technology": self.technology,
        }


@dataclass
class Level1Whitebox:
    """Arc42 Section 5.1 - Level 1 Whitebox."""
    overview: str
    components: List[ComponentDescription]
    important_interfaces: str
    rationale: str

    def to_dict(self) -> Dict:
        return {
            "overview": self.overview,
            "components": [c.to_dict() for c in self.components],
            "important_interfaces": self.important_interfaces,
            "rationale": self.rationale,
        }


@dataclass
class Level2Whitebox:
    """Arc42 Section 5.2.X - Level 2 Whitebox for a component."""
    component_name: str
    purpose: str
    internal_structure: List[ComponentDescription]
    dependencies: List[str]

    def to_dict(self) -> Dict:
        return {
            "component_name": self.component_name,
            "purpose": self.purpose,
            "internal_structure": [c.to_dict() for c in self.internal_structure],
            "dependencies": self.dependencies,
        }


@dataclass
class Section5:
    """Complete Arc42 Section 5 - Building Block View."""
    level_1: Level1Whitebox
    level_2_list: List[Level2Whitebox]
    diagram_code: str  # Mermaid diagram
    statistics: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "level_1": self.level_1.to_dict(),
            "level_2_list": [l2.to_dict() for l2 in self.level_2_list],
            "diagram_code": self.diagram_code,
            "statistics": self.statistics,
        }

    def to_markdown(self) -> str:
        """Generate markdown representation."""
        md = ["# 5. Building Block View\n"]

        # Level 1
        md.append("## 5.1 Level 1 - Whitebox Overall System\n")
        md.append("### Overview\n")
        md.append(f"{self.level_1.overview}\n")

        md.append("### Contained Building Blocks\n")
        md.append("| Component | Responsibility |")
        md.append("|-----------|---------------|")
        for comp in self.level_1.components:
            md.append(f"| {comp.name} | {comp.responsibility} |")
        md.append("")

        md.append("### Important Interfaces\n")
        md.append(f"{self.level_1.important_interfaces}\n")

        md.append("### Rationale\n")
        md.append(f"{self.level_1.rationale}\n")

        # Level 2
        md.append("## 5.2 Level 2 - Whiteboxes\n")
        for level_2 in self.level_2_list:
            md.append(f"### {level_2.component_name}\n")
            md.append(f"**Purpose**: {level_2.purpose}\n")

            if level_2.internal_structure:
                md.append("**Internal Structure**:\n")
                md.append("| Component | Responsibility |")
                md.append("|-----------|---------------|")
                for comp in level_2.internal_structure:
                    md.append(f"| {comp.name} | {comp.responsibility} |")
                md.append("")

            if level_2.dependencies:
                md.append(f"**Dependencies**: {', '.join(level_2.dependencies)}\n")

        # Diagram
        md.append("## 5.3 Architecture Diagram\n")
        md.append(self.diagram_code)
        md.append("")

        # Statistics
        if self.statistics:
            md.append("---\n")
            md.append("## Statistics\n")
            for key, value in self.statistics.items():
                label = key.replace('_', ' ').title()
                md.append(f"- **{label}**: {value:,}")

        return "\n".join(md)
