"""
Content planner - maps friction points and analysis to prioritized documentation plan.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from ..models.analysis import AnalysisResult
from ..research.user_research import FrictionLog, FrictionPoint

logger = logging.getLogger(__name__)


@dataclass
class ContentItem:
    """A single item in the documentation plan."""
    title: str
    doc_type: str  # arc42, diataxis-tutorial, diataxis-howto, diataxis-reference, diataxis-explanation, c4
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    section: str  # e.g., "section_01", "tutorials/getting-started"
    source_friction: Optional[str] = None  # Reference to friction point that triggered this
    description: str = ""
    estimated_facts: int = 0  # Number of facts expected to support this section

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "doc_type": self.doc_type,
            "priority": self.priority,
            "section": self.section,
            "source_friction": self.source_friction,
            "description": self.description,
            "estimated_facts": self.estimated_facts,
        }


@dataclass
class DocumentationPlan:
    """A prioritized plan for documentation generation."""
    repo_name: str
    items: List[ContentItem] = field(default_factory=list)
    total_sections: int = 0
    critical_items: int = 0
    estimated_generation_time: str = ""

    def to_dict(self) -> Dict:
        return {
            "repo_name": self.repo_name,
            "items": [i.to_dict() for i in self.items],
            "total_sections": self.total_sections,
            "critical_items": self.critical_items,
            "estimated_generation_time": self.estimated_generation_time,
        }

    def get_by_priority(self, priority: str) -> List[ContentItem]:
        return [i for i in self.items if i.priority == priority]

    def get_by_type(self, doc_type: str) -> List[ContentItem]:
        return [i for i in self.items if i.doc_type == doc_type]

    def get_ordered(self) -> List[ContentItem]:
        """Return items ordered by priority."""
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        return sorted(self.items, key=lambda i: priority_order.get(i.priority, 4))


class ContentPlanner:
    """Creates a prioritized documentation plan from friction analysis."""

    # Mapping of friction areas to documentation sections
    FRICTION_TO_DOCS = {
        "onboarding": [
            ("Getting Started Tutorial", "diataxis-tutorial", "tutorials/getting-started"),
            ("Introduction and Goals", "arc42", "section_01"),
        ],
        "setup": [
            ("Local Development Setup", "diataxis-howto", "how-to/setup"),
            ("Getting Started Tutorial", "diataxis-tutorial", "tutorials/getting-started"),
        ],
        "architecture": [
            ("Building Block View", "arc42", "section_05"),
            ("Architecture Explanation", "diataxis-explanation", "explanation/architecture"),
            ("C4 Diagrams", "c4", "diagrams/"),
        ],
        "dependencies": [
            ("Solution Strategy", "arc42", "section_04"),
            ("Architecture Constraints", "arc42", "section_02"),
        ],
        "contribution": [
            ("Development How-To", "diataxis-howto", "how-to/contributing"),
            ("Cross-Cutting Concepts", "arc42", "section_08"),
        ],
        "complexity": [
            ("Building Block View", "arc42", "section_05"),
            ("C4 Diagrams", "c4", "diagrams/"),
            ("Context and Scope", "arc42", "section_03"),
        ],
    }

    def create_plan(
        self,
        friction_log: FrictionLog,
        analysis: AnalysisResult,
    ) -> DocumentationPlan:
        """
        Create a prioritized documentation plan.

        Maps friction points to Arc42 sections and Diataxis types,
        prioritized by severity.
        """
        plan = DocumentationPlan(repo_name=analysis.repo_name)
        seen_sections = set()

        # Map friction points to content items
        for point in friction_log.friction_points:
            mappings = self.FRICTION_TO_DOCS.get(point.area, [])
            for title, doc_type, section in mappings:
                if section not in seen_sections:
                    seen_sections.add(section)
                    plan.items.append(ContentItem(
                        title=title,
                        doc_type=doc_type,
                        priority=point.severity,
                        section=section,
                        source_friction=point.description,
                        description=f"Addresses: {point.description}",
                    ))

        # Add baseline documentation items that are always needed
        baseline_items = [
            ("Introduction and Goals", "arc42", "section_01", "HIGH"),
            ("Context and Scope", "arc42", "section_03", "HIGH"),
            ("Building Block View", "arc42", "section_05", "HIGH"),
            ("Runtime View", "arc42", "section_06", "MEDIUM"),
            ("Deployment View", "arc42", "section_07", "MEDIUM"),
            ("Architecture Decisions", "arc42", "section_09", "MEDIUM"),
            ("Risks and Technical Debt", "arc42", "section_11", "LOW"),
            ("Glossary", "arc42", "section_12", "LOW"),
            ("API Reference", "diataxis-reference", "reference/api", "HIGH"),
            ("Troubleshooting", "diataxis-howto", "how-to/troubleshooting", "MEDIUM"),
        ]

        for title, doc_type, section, priority in baseline_items:
            if section not in seen_sections:
                seen_sections.add(section)
                plan.items.append(ContentItem(
                    title=title,
                    doc_type=doc_type,
                    priority=priority,
                    section=section,
                    description=f"Baseline {doc_type} documentation",
                ))

        plan.total_sections = len(plan.items)
        plan.critical_items = len(plan.get_by_priority("CRITICAL"))

        # Estimate generation time (rough: ~30s per LLM call, ~2 calls per section)
        estimated_seconds = plan.total_sections * 60
        if estimated_seconds > 120:
            plan.estimated_generation_time = f"{estimated_seconds // 60} minutes"
        else:
            plan.estimated_generation_time = f"{estimated_seconds} seconds"

        logger.info(
            f"Created documentation plan: {plan.total_sections} sections, "
            f"{plan.critical_items} critical"
        )

        return plan
