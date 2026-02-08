"""
Output formatting and file writing.
"""

import logging
import re
from pathlib import Path

from ..models.config import Config
from ..models.documentation import Section5, Arc42Document


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

    def write_arc42_document(self, doc: Arc42Document, output_path: str) -> None:
        """
        Write Arc42 document sections to markdown files.

        Args:
            doc: Arc42Document with sections
            output_path: Output directory path
        """
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        section_names = {
            1: "introduction_and_goals",
            2: "architecture_constraints",
            3: "context_and_scope",
            4: "solution_strategy",
            5: "building_block_view",
            6: "runtime_view",
            7: "deployment_view",
            8: "crosscutting_concepts",
            9: "architecture_decisions",
            10: "quality_requirements",
            11: "risks_and_technical_debt",
            12: "glossary",
        }

        diagrams_written = []

        for i in range(1, 13):
            attr_name = f"section_{i:02d}" if i != 5 else "section_05"
            section = getattr(doc, attr_name, None)
            if section:
                # Write section markdown
                filename = f"section_{i:02d}_{section_names[i]}.md"
                md_path = output_dir / filename
                md_path.write_text(section.to_markdown(), encoding='utf-8')
                logger.info(f"Section {i} written to: {md_path}")

                # Extract and save diagrams
                if self.config.output.create_diagrams_folder:
                    diagrams = self._extract_diagrams(section)
                    if diagrams:
                        diagrams_written.extend(diagrams)

        # Write diagrams
        if self.config.output.create_diagrams_folder and diagrams_written:
            diagram_dir = output_dir / "diagrams"
            diagram_dir.mkdir(exist_ok=True)
            for name, code in diagrams_written:
                diagram_path = diagram_dir / f"{name}.mmd"
                diagram_path.write_text(code, encoding='utf-8')
                logger.info(f"Diagram written to: {diagram_path}")

        # Write combined document
        combined_path = output_dir / "arc42_complete.md"
        combined_path.write_text(doc.to_markdown(), encoding='utf-8')
        logger.info(f"Complete document written to: {combined_path}")

    def _extract_diagrams(self, section) -> list:
        """Extract mermaid diagrams from a section."""
        diagrams = []
        markdown = section.to_markdown()

        # Find all mermaid code blocks
        pattern = r"```mermaid\s*(.*?)```"
        matches = re.findall(pattern, markdown, re.DOTALL)

        for i, code in enumerate(matches):
            code = code.strip()
            if code:
                # Generate name based on diagram type
                if "sequenceDiagram" in code:
                    name = f"sequence_{i+1}"
                elif "C4Context" in code:
                    name = f"context_{i+1}"
                elif "C4Container" in code:
                    name = f"container_{i+1}"
                elif "C4Component" in code:
                    name = f"component_{i+1}"
                elif "flowchart" in code.lower():
                    name = f"flowchart_{i+1}"
                else:
                    name = f"diagram_{i+1}"
                diagrams.append((name, code))

        return diagrams

    def write_section_5(self, section: Section5, output_path: str) -> None:
        """
        Write Section 5 to markdown file (legacy method for backward compatibility).

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
