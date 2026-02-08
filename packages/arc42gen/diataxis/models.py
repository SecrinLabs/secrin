"""
Diátaxis documentation models.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class TutorialStep:
    """A step in a tutorial."""
    title: str
    instructions: str
    code: str = ""
    checkpoint: str = ""

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "instructions": self.instructions,
            "code": self.code,
            "checkpoint": self.checkpoint,
        }


@dataclass
class Tutorial:
    """A learning-oriented tutorial."""
    title: str
    goal: str
    prerequisites: List[str] = field(default_factory=list)
    estimated_time: str = ""
    steps: List[TutorialStep] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "goal": self.goal,
            "prerequisites": self.prerequisites,
            "estimated_time": self.estimated_time,
            "steps": [s.to_dict() for s in self.steps],
            "next_steps": self.next_steps,
        }

    def to_markdown(self) -> str:
        md = [f"# Tutorial: {self.title}\n"]

        md.append(f"**Goal**: {self.goal}\n")

        if self.estimated_time:
            md.append(f"**Estimated Time**: {self.estimated_time}\n")

        if self.prerequisites:
            md.append("**Prerequisites**:")
            for prereq in self.prerequisites:
                md.append(f"- {prereq}")
            md.append("")

        for i, step in enumerate(self.steps, 1):
            md.append(f"## Step {i}: {step.title}\n")
            md.append(f"{step.instructions}\n")
            if step.code:
                md.append("```bash")
                md.append(step.code)
                md.append("```\n")
            if step.checkpoint:
                md.append(f"**Checkpoint**: {step.checkpoint}\n")

        if self.next_steps:
            md.append("## Next Steps\n")
            for next_step in self.next_steps:
                md.append(f"- {next_step}")
            md.append("")

        return "\n".join(md)


@dataclass
class TroubleshootingItem:
    """A troubleshooting problem and solution."""
    problem: str
    solution: str

    def to_dict(self) -> Dict:
        return {"problem": self.problem, "solution": self.solution}


@dataclass
class HowToGuide:
    """A problem-solving how-to guide."""
    title: str
    problem: str
    prerequisites: List[str] = field(default_factory=list)
    estimated_time: str = ""
    steps: List[str] = field(default_factory=list)
    troubleshooting: List[TroubleshootingItem] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "problem": self.problem,
            "prerequisites": self.prerequisites,
            "estimated_time": self.estimated_time,
            "steps": self.steps,
            "troubleshooting": [t.to_dict() for t in self.troubleshooting],
        }

    def to_markdown(self) -> str:
        md = [f"# How-To: {self.title}\n"]

        md.append(f"**Problem**: {self.problem}\n")

        if self.estimated_time:
            md.append(f"**Time**: {self.estimated_time}\n")

        if self.prerequisites:
            md.append("**Prerequisites**:")
            for prereq in self.prerequisites:
                md.append(f"- {prereq}")
            md.append("")

        if self.steps:
            md.append("## Steps\n")
            for i, step in enumerate(self.steps, 1):
                md.append(f"{i}. {step}")
            md.append("")

        if self.troubleshooting:
            md.append("## Troubleshooting\n")
            for item in self.troubleshooting:
                md.append(f"**Problem**: {item.problem}")
                md.append(f"**Solution**: {item.solution}\n")

        return "\n".join(md)


@dataclass
class APIEndpoint:
    """An API endpoint reference."""
    method: str
    path: str
    description: str
    request_body: str = ""
    response: str = ""
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "method": self.method,
            "path": self.path,
            "description": self.description,
            "request_body": self.request_body,
            "response": self.response,
            "errors": self.errors,
        }


@dataclass
class Reference:
    """Information-oriented reference documentation."""
    title: str
    overview: str = ""
    sections: Dict[str, str] = field(default_factory=dict)
    api_endpoints: List[APIEndpoint] = field(default_factory=list)
    configuration: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "overview": self.overview,
            "sections": self.sections,
            "api_endpoints": [e.to_dict() for e in self.api_endpoints],
            "configuration": self.configuration,
        }

    def to_markdown(self) -> str:
        md = [f"# {self.title}\n"]

        if self.overview:
            md.append(f"{self.overview}\n")

        for section_name, content in self.sections.items():
            md.append(f"## {section_name}\n")
            md.append(f"{content}\n")

        if self.api_endpoints:
            md.append("## API Reference\n")
            for endpoint in self.api_endpoints:
                md.append(f"### {endpoint.method} {endpoint.path}\n")
                md.append(f"{endpoint.description}\n")
                if endpoint.request_body:
                    md.append("**Request Body**:")
                    md.append("```json")
                    md.append(endpoint.request_body)
                    md.append("```\n")
                if endpoint.response:
                    md.append("**Response**:")
                    md.append("```json")
                    md.append(endpoint.response)
                    md.append("```\n")
                if endpoint.errors:
                    md.append("**Errors**:")
                    for error in endpoint.errors:
                        md.append(f"- {error}")
                    md.append("")

        if self.configuration:
            md.append("## Configuration\n")
            md.append("| Option | Description |")
            md.append("|--------|-------------|")
            for option, desc in self.configuration.items():
                md.append(f"| `{option}` | {desc} |")
            md.append("")

        return "\n".join(md)


@dataclass
class Explanation:
    """Understanding-oriented explanation content."""
    title: str
    problem: str = ""
    solution: str = ""
    benefits: List[str] = field(default_factory=list)
    tradeoffs: List[str] = field(default_factory=list)
    when_to_use: List[str] = field(default_factory=list)
    when_not_to_use: List[str] = field(default_factory=list)
    related_sections: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "problem": self.problem,
            "solution": self.solution,
            "benefits": self.benefits,
            "tradeoffs": self.tradeoffs,
            "when_to_use": self.when_to_use,
            "when_not_to_use": self.when_not_to_use,
            "related_sections": self.related_sections,
        }

    def to_markdown(self) -> str:
        md = [f"# Explanation: {self.title}\n"]

        if self.problem:
            md.append("## The Problem\n")
            md.append(f"{self.problem}\n")

        if self.solution:
            md.append("## The Solution\n")
            md.append(f"{self.solution}\n")

        if self.benefits:
            md.append("## Benefits\n")
            for benefit in self.benefits:
                md.append(f"- {benefit}")
            md.append("")

        if self.tradeoffs:
            md.append("## Trade-Offs\n")
            for tradeoff in self.tradeoffs:
                md.append(f"- {tradeoff}")
            md.append("")

        if self.when_to_use:
            md.append("## When to Use\n")
            for item in self.when_to_use:
                md.append(f"- {item}")
            md.append("")

        if self.when_not_to_use:
            md.append("## When NOT to Use\n")
            for item in self.when_not_to_use:
                md.append(f"- {item}")
            md.append("")

        if self.related_sections:
            md.append("## Related\n")
            for section in self.related_sections:
                md.append(f"- {section}")
            md.append("")

        return "\n".join(md)


@dataclass
class DiátaxisDocument:
    """Complete Diátaxis documentation."""
    tutorials: List[Tutorial] = field(default_factory=list)
    how_to_guides: List[HowToGuide] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)
    explanations: List[Explanation] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "tutorials": [t.to_dict() for t in self.tutorials],
            "how_to_guides": [h.to_dict() for h in self.how_to_guides],
            "references": [r.to_dict() for r in self.references],
            "explanations": [e.to_dict() for e in self.explanations],
        }
