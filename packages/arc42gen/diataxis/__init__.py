"""
Diátaxis documentation framework generators.

Generates four types of documentation:
- Tutorials: Learning-oriented, step-by-step guides
- How-To Guides: Problem-solving, task-oriented guides
- Reference: Information-oriented, factual documentation
- Explanation: Understanding-oriented, conceptual content
"""

from .generator import DiátaxisGenerator
from .models import Tutorial, HowToGuide, Reference, Explanation, DiátaxisDocument

__all__ = [
    "DiátaxisGenerator",
    "Tutorial",
    "HowToGuide",
    "Reference",
    "Explanation",
    "DiátaxisDocument",
]
