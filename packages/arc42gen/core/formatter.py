"""
Output formatting and file writing.
"""

import logging
from pathlib import Path

from ..models.config import Config
from ..models.documentation import Section5


logger = logging.getLogger(__name__)


class OutputFormatter:
    """Formats and writes documentation output."""

    def __init__(self, config: Config):
        """
        Initialize the formatter.

        Args:
            config: Configuration object
        """
        self.config = config

    def write_section_5(self, section: Section5, output_path: str) -> None:
        """
        Write Section 5 to markdown file.

        Args:
            section: Section5 object
            output_path: Output directory path
        """
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write main markdown file
        md_path = output_dir / "arc42_section_5.md"
        markdown = section.to_markdown()
        md_path.write_text(markdown, encoding='utf-8')

        logger.info(f"Section 5 written to: {md_path}")

        # Write diagram file
        if self.config.output.create_diagrams_folder:
            diagram_dir = output_dir / "diagrams"
            diagram_dir.mkdir(exist_ok=True)

            # Extract raw mermaid code (without markdown fences)
            diagram_code = section.diagram_code
            if diagram_code.startswith("```mermaid"):
                diagram_code = diagram_code[10:]  # Remove ```mermaid
            if diagram_code.endswith("```"):
                diagram_code = diagram_code[:-3]  # Remove ```
            diagram_code = diagram_code.strip()

            diagram_path = diagram_dir / "architecture.mmd"
            diagram_path.write_text(diagram_code, encoding='utf-8')

            logger.info(f"Diagram written to: {diagram_path}")

    def format_section_5(self, section: Section5) -> str:
        """
        Format Section5 as markdown string.

        Args:
            section: Section5 object

        Returns:
            Formatted markdown string
        """
        return section.to_markdown()
