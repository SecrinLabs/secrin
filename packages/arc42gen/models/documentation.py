"""
Documentation output models for Arc42 generation.

Contains dataclass models for all Arc42 sections (1-12) and Diátaxis content types.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


# =============================================================================
# Shared Models
# =============================================================================

@dataclass
class Stakeholder:
    """A project stakeholder."""
    role: str
    name: str = ""
    expectations: str = ""

    def to_dict(self) -> Dict:
        return {"role": self.role, "name": self.name, "expectations": self.expectations}


@dataclass
class QualityGoal:
    """A quality attribute with target."""
    attribute: str
    priority: str  # Critical, High, Medium, Low
    target: str
    measurement: str = ""

    def to_dict(self) -> Dict:
        return {
            "attribute": self.attribute,
            "priority": self.priority,
            "target": self.target,
            "measurement": self.measurement,
        }


@dataclass
class Constraint:
    """Technical or organizational constraint."""
    name: str
    description: str
    impact: str = ""
    category: str = "technical"  # technical, organizational, convention

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "impact": self.impact,
            "category": self.category,
        }


@dataclass
class ExternalSystem:
    """External system or interface."""
    name: str
    description: str
    protocol: str = ""
    purpose: str = ""

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "protocol": self.protocol,
            "purpose": self.purpose,
        }


@dataclass
class TechnologyDecision:
    """A technology choice with rationale."""
    technology: str
    rationale: str
    category: str = ""  # framework, database, infrastructure, etc.

    def to_dict(self) -> Dict:
        return {
            "technology": self.technology,
            "rationale": self.rationale,
            "category": self.category,
        }


@dataclass
class ArchitectureDecision:
    """An Architecture Decision Record (ADR)."""
    id: str
    title: str
    status: str  # Proposed, Accepted, Deprecated, Superseded
    context: str
    decision: str
    consequences: List[str] = field(default_factory=list)
    date: str = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "context": self.context,
            "decision": self.decision,
            "consequences": self.consequences,
            "date": self.date,
        }


@dataclass
class Risk:
    """A technical risk."""
    name: str
    probability: str  # Low, Medium, High
    impact: str  # Low, Medium, High
    mitigation: str = ""

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "probability": self.probability,
            "impact": self.impact,
            "mitigation": self.mitigation,
        }


@dataclass
class TechnicalDebt:
    """A technical debt item."""
    description: str
    priority: str  # Low, Medium, High
    effort: str = ""
    location: str = ""

    def to_dict(self) -> Dict:
        return {
            "description": self.description,
            "priority": self.priority,
            "effort": self.effort,
            "location": self.location,
        }


@dataclass
class GlossaryTerm:
    """A glossary term definition."""
    term: str
    definition: str
    category: str = "general"  # general, domain, technical

    def to_dict(self) -> Dict:
        return {"term": self.term, "definition": self.definition, "category": self.category}


# =============================================================================
# Arc42 Section Models
# =============================================================================

@dataclass
class Section01:
    """Arc42 Section 1 - Introduction and Goals."""
    requirements_overview: str
    business_goals: List[str] = field(default_factory=list)
    key_features: List[str] = field(default_factory=list)
    quality_goals: List[QualityGoal] = field(default_factory=list)
    stakeholders: List[Stakeholder] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "requirements_overview": self.requirements_overview,
            "business_goals": self.business_goals,
            "key_features": self.key_features,
            "quality_goals": [q.to_dict() for q in self.quality_goals],
            "stakeholders": [s.to_dict() for s in self.stakeholders],
        }

    def to_markdown(self) -> str:
        md = ["# 1. Introduction and Goals\n"]

        md.append("## 1.1 Requirements Overview\n")
        md.append(f"{self.requirements_overview}\n")

        if self.business_goals:
            md.append("### Business Goals\n")
            for goal in self.business_goals:
                md.append(f"- {goal}")
            md.append("")

        if self.key_features:
            md.append("### Key Features\n")
            for feature in self.key_features:
                md.append(f"- {feature}")
            md.append("")

        if self.quality_goals:
            md.append("## 1.2 Quality Goals\n")
            md.append("| Quality Attribute | Priority | Target | Measurement |")
            md.append("|-------------------|----------|--------|-------------|")
            for q in self.quality_goals:
                md.append(f"| {q.attribute} | {q.priority} | {q.target} | {q.measurement} |")
            md.append("")

        if self.stakeholders:
            md.append("## 1.3 Stakeholders\n")
            md.append("| Role | Name | Expectations |")
            md.append("|------|------|--------------|")
            for s in self.stakeholders:
                md.append(f"| {s.role} | {s.name} | {s.expectations} |")
            md.append("")

        return "\n".join(md)


@dataclass
class Section02:
    """Arc42 Section 2 - Architecture Constraints."""
    technical_constraints: List[Constraint] = field(default_factory=list)
    organizational_constraints: List[Constraint] = field(default_factory=list)
    conventions: List[Constraint] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "technical_constraints": [c.to_dict() for c in self.technical_constraints],
            "organizational_constraints": [c.to_dict() for c in self.organizational_constraints],
            "conventions": [c.to_dict() for c in self.conventions],
        }

    def to_markdown(self) -> str:
        md = ["# 2. Architecture Constraints\n"]

        if self.technical_constraints:
            md.append("## 2.1 Technical Constraints\n")
            md.append("| Constraint | Description | Impact |")
            md.append("|------------|-------------|--------|")
            for c in self.technical_constraints:
                md.append(f"| {c.name} | {c.description} | {c.impact} |")
            md.append("")

        if self.organizational_constraints:
            md.append("## 2.2 Organizational Constraints\n")
            for c in self.organizational_constraints:
                md.append(f"- **{c.name}**: {c.description}")
            md.append("")

        if self.conventions:
            md.append("## 2.3 Conventions\n")
            for c in self.conventions:
                md.append(f"- **{c.name}**: {c.description}")
            md.append("")

        return "\n".join(md)


@dataclass
class Section03:
    """Arc42 Section 3 - System Context and Scope."""
    system_purpose: str
    business_context: str = ""
    external_systems: List[ExternalSystem] = field(default_factory=list)
    context_diagram: str = ""  # Mermaid diagram

    def to_dict(self) -> Dict:
        return {
            "system_purpose": self.system_purpose,
            "business_context": self.business_context,
            "external_systems": [e.to_dict() for e in self.external_systems],
            "context_diagram": self.context_diagram,
        }

    def to_markdown(self) -> str:
        md = ["# 3. Context and Scope\n"]

        md.append("## 3.1 Business Context\n")
        md.append(f"**System Purpose**: {self.system_purpose}\n")
        if self.business_context:
            md.append(f"{self.business_context}\n")

        if self.external_systems:
            md.append("### External Systems\n")
            for ext in self.external_systems:
                md.append(f"- **{ext.name}**: {ext.description}")
            md.append("")

        if self.context_diagram:
            md.append("## 3.2 Technical Context\n")
            md.append("### System Context Diagram\n")
            md.append(self.context_diagram)
            md.append("")

        if self.external_systems:
            md.append("## 3.3 External Interfaces\n")
            md.append("| Interface | Protocol | Purpose |")
            md.append("|-----------|----------|---------|")
            for ext in self.external_systems:
                md.append(f"| {ext.name} | {ext.protocol} | {ext.purpose} |")
            md.append("")

        return "\n".join(md)


@dataclass
class Section04:
    """Arc42 Section 4 - Solution Strategy."""
    technology_decisions: List[TechnologyDecision] = field(default_factory=list)
    architectural_patterns: List[str] = field(default_factory=list)
    quality_strategies: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "technology_decisions": [t.to_dict() for t in self.technology_decisions],
            "architectural_patterns": self.architectural_patterns,
            "quality_strategies": self.quality_strategies,
        }

    def to_markdown(self) -> str:
        md = ["# 4. Solution Strategy\n"]

        if self.technology_decisions:
            md.append("## 4.1 Technology Decisions\n")
            md.append("| Technology | Rationale |")
            md.append("|------------|-----------|")
            for t in self.technology_decisions:
                md.append(f"| {t.technology} | {t.rationale} |")
            md.append("")

        if self.architectural_patterns:
            md.append("## 4.2 Architectural Patterns\n")
            for pattern in self.architectural_patterns:
                md.append(f"- {pattern}")
            md.append("")

        if self.quality_strategies:
            md.append("## 4.3 Quality Strategy\n")
            for quality, strategy in self.quality_strategies.items():
                md.append(f"- **{quality}**: {strategy}")
            md.append("")

        return "\n".join(md)


# Section 5 is defined below (existing)


@dataclass
class RuntimeScenario:
    """A runtime scenario with sequence diagram."""
    name: str
    description: str
    sequence_diagram: str = ""

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "sequence_diagram": self.sequence_diagram,
        }


@dataclass
class Section06:
    """Arc42 Section 6 - Runtime View."""
    overview: str = ""
    scenarios: List[RuntimeScenario] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "overview": self.overview,
            "scenarios": [s.to_dict() for s in self.scenarios],
        }

    def to_markdown(self) -> str:
        md = ["# 6. Runtime View\n"]

        if self.overview:
            md.append(f"{self.overview}\n")

        if self.scenarios:
            md.append("## 6.1 Key Scenarios\n")
            for scenario in self.scenarios:
                md.append(f"### {scenario.name}\n")
                md.append(f"{scenario.description}\n")
                if scenario.sequence_diagram:
                    md.append(scenario.sequence_diagram)
                    md.append("")

        return "\n".join(md)


@dataclass
class Section07:
    """Arc42 Section 7 - Deployment View."""
    infrastructure_overview: str = ""
    deployment_diagram: str = ""
    deployment_process: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "infrastructure_overview": self.infrastructure_overview,
            "deployment_diagram": self.deployment_diagram,
            "deployment_process": self.deployment_process,
        }

    def to_markdown(self) -> str:
        md = ["# 7. Deployment View\n"]

        if self.infrastructure_overview:
            md.append("## 7.1 Infrastructure Overview\n")
            md.append(f"{self.infrastructure_overview}\n")

        if self.deployment_diagram:
            md.append("## 7.2 Deployment Diagram\n")
            md.append(self.deployment_diagram)
            md.append("")

        if self.deployment_process:
            md.append("## 7.3 Deployment Process\n")
            for i, step in enumerate(self.deployment_process, 1):
                md.append(f"{i}. {step}")
            md.append("")

        return "\n".join(md)


@dataclass
class Section08:
    """Arc42 Section 8 - Cross-Cutting Concepts."""
    concepts: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {"concepts": self.concepts}

    def to_markdown(self) -> str:
        md = ["# 8. Cross-Cutting Concepts\n"]

        for concept_name, description in self.concepts.items():
            md.append(f"## 8.{list(self.concepts.keys()).index(concept_name) + 1} {concept_name}\n")
            md.append(f"{description}\n")

        return "\n".join(md)


@dataclass
class Section09:
    """Arc42 Section 9 - Architecture Decisions."""
    decisions: List[ArchitectureDecision] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {"decisions": [d.to_dict() for d in self.decisions]}

    def to_markdown(self) -> str:
        md = ["# 9. Architecture Decisions\n"]

        for decision in self.decisions:
            md.append(f"## {decision.id}: {decision.title}\n")
            md.append(f"**Status**: {decision.status}")
            if decision.date:
                md.append(f"  \n**Date**: {decision.date}")
            md.append(f"\n\n**Context**: {decision.context}\n")
            md.append(f"**Decision**: {decision.decision}\n")
            if decision.consequences:
                md.append("**Consequences**:")
                for c in decision.consequences:
                    md.append(f"- {c}")
            md.append("")

        return "\n".join(md)


@dataclass
class Section10:
    """Arc42 Section 10 - Quality Requirements."""
    quality_tree: str = ""
    quality_scenarios: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "quality_tree": self.quality_tree,
            "quality_scenarios": self.quality_scenarios,
        }

    def to_markdown(self) -> str:
        md = ["# 10. Quality Requirements\n"]

        if self.quality_tree:
            md.append("## 10.1 Quality Tree\n")
            md.append("```")
            md.append(self.quality_tree)
            md.append("```\n")

        if self.quality_scenarios:
            md.append("## 10.2 Quality Scenarios\n")
            md.append("| Scenario | Stimulus | Response | Measure |")
            md.append("|----------|----------|----------|---------|")
            for s in self.quality_scenarios:
                md.append(f"| {s.get('scenario', '')} | {s.get('stimulus', '')} | {s.get('response', '')} | {s.get('measure', '')} |")
            md.append("")

        return "\n".join(md)


@dataclass
class Section11:
    """Arc42 Section 11 - Risks and Technical Debt."""
    risks: List[Risk] = field(default_factory=list)
    technical_debt: List[TechnicalDebt] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "risks": [r.to_dict() for r in self.risks],
            "technical_debt": [t.to_dict() for t in self.technical_debt],
        }

    def to_markdown(self) -> str:
        md = ["# 11. Risks and Technical Debt\n"]

        if self.risks:
            md.append("## 11.1 Technical Risks\n")
            md.append("| Risk | Probability | Impact | Mitigation |")
            md.append("|------|-------------|--------|------------|")
            for r in self.risks:
                md.append(f"| {r.name} | {r.probability} | {r.impact} | {r.mitigation} |")
            md.append("")

        if self.technical_debt:
            md.append("## 11.2 Technical Debt\n")
            for priority in ["High", "Medium", "Low"]:
                items = [t for t in self.technical_debt if t.priority == priority]
                if items:
                    md.append(f"### {priority} Priority\n")
                    for t in items:
                        location = f" ({t.location})" if t.location else ""
                        md.append(f"- [ ] **{t.description}**{location}")
                    md.append("")

        return "\n".join(md)


@dataclass
class Section12:
    """Arc42 Section 12 - Glossary."""
    terms: List[GlossaryTerm] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {"terms": [t.to_dict() for t in self.terms]}

    def to_markdown(self) -> str:
        md = ["# 12. Glossary\n"]

        # Group by category
        general = [t for t in self.terms if t.category == "general"]
        technical = [t for t in self.terms if t.category == "technical"]
        domain = [t for t in self.terms if t.category == "domain"]

        if general or technical:
            md.append("## Technical Terms\n")
            md.append("| Term | Definition |")
            md.append("|------|------------|")
            for t in general + technical:
                md.append(f"| **{t.term}** | {t.definition} |")
            md.append("")

        if domain:
            md.append("## Domain-Specific Terms\n")
            md.append("| Term | Definition |")
            md.append("|------|------------|")
            for t in domain:
                md.append(f"| **{t.term}** | {t.definition} |")
            md.append("")

        return "\n".join(md)


# =============================================================================
# Section 5 - Building Block View (existing, kept for compatibility)
# =============================================================================

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


# =============================================================================
# Complete Arc42 Document
# =============================================================================

@dataclass
class Arc42Document:
    """Complete Arc42 documentation with all sections."""
    section_01: Optional[Section01] = None
    section_02: Optional[Section02] = None
    section_03: Optional[Section03] = None
    section_04: Optional[Section04] = None
    section_05: Optional[Section5] = None
    section_06: Optional[Section06] = None
    section_07: Optional[Section07] = None
    section_08: Optional[Section08] = None
    section_09: Optional[Section09] = None
    section_10: Optional[Section10] = None
    section_11: Optional[Section11] = None
    section_12: Optional[Section12] = None

    def to_dict(self) -> Dict:
        result = {}
        for i in range(1, 13):
            attr_name = f"section_{i:02d}" if i != 5 else "section_05"
            section = getattr(self, attr_name, None)
            if section:
                result[f"section_{i}"] = section.to_dict()
        return result

    def to_markdown(self) -> str:
        """Generate complete Arc42 documentation as markdown."""
        sections = []
        for i in range(1, 13):
            attr_name = f"section_{i:02d}" if i != 5 else "section_05"
            section = getattr(self, attr_name, None)
            if section:
                sections.append(section.to_markdown())
        return "\n---\n\n".join(sections)
