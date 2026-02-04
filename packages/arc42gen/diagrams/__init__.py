"""
C4 diagram generation module.

Generates C4 diagrams at all 4 levels:
- Level 1: System Context
- Level 2: Container
- Level 3: Component
- Level 4: Code (Class diagrams)
"""

from .c4_generator import C4Generator

__all__ = ["C4Generator"]
