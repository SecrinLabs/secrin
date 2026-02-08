"""
Main workflow orchestrator.
"""

import logging
from pathlib import Path
from typing import Callable, List, Optional

from ..models.config import Config
from ..models.documentation import Arc42Document
from ..utils.git_utils import is_remote_url
from ..utils.progress import ProgressTracker
from .analyzer import CodebaseAnalyzer
from .generator import Arc42Generator
from .formatter import OutputFormatter


logger = logging.getLogger(__name__)


SECTION_NAMES = {
    1: "Introduction & Goals",
    2: "Architecture Constraints",
    3: "Context & Scope",
    4: "Solution Strategy",
    5: "Building Block View",
    6: "Runtime View",
    7: "Deployment View",
    8: "Cross-Cutting Concepts",
    9: "Architecture Decisions",
    10: "Quality Requirements",
    11: "Risks & Technical Debt",
    12: "Glossary",
}

SECTION_ATTR_NAMES = {
    1: "section_01", 2: "section_02", 3: "section_03", 4: "section_04",
    5: "section_05", 6: "section_06", 7: "section_07", 8: "section_08",
    9: "section_09", 10: "section_10", 11: "section_11", 12: "section_12",
}


class Orchestrator:
    """
    Coordinates the documentation generation workflow.

    Workflow:
    1. Validate inputs
    2. Analyze codebase (CodebaseAnalyzer)
    3. Generate Arc42 sections
    4. Format and save output (OutputFormatter)

    Supports multiple LLM providers (Anthropic, Gemini) and
    multiple languages (Python, JavaScript, TypeScript).
    """

    def __init__(self, config: Config, verbose: bool = True):
        """
        Initialize the orchestrator.

        Args:
            config: Configuration object
            verbose: Enable Rich progress output (default True)
        """
        self.config = config
        self.verbose = verbose
        self.analyzer = CodebaseAnalyzer(config)
        self.generator = Arc42Generator(config=config.llm)
        self.formatter = OutputFormatter(config)

    def run(
        self,
        repo_path: str,
        output_path: str,
        sections: Optional[List[int]] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> bool:
        """
        Execute full documentation generation pipeline.

        Args:
            repo_path: Path to repository (local)
            output_path: Output directory path
            sections: List of section numbers to generate (1-12), None for all
            progress_callback: Optional callback for progress updates (0-100)

        Returns:
            True if successful, False otherwise
        """
        if sections is None:
            sections = list(range(1, 13))

        progress = ProgressTracker(output_dir=output_path, verbose=self.verbose)

        try:
            # Step 1: Validate inputs
            progress.start_step("Validate inputs")
            logger.info("Validating inputs...")
            self._validate_inputs(repo_path)
            progress.complete_step()
            if progress_callback:
                progress_callback(10)

            # Step 2: Analyze codebase
            progress.start_step("Analyze codebase", {"repo_path": repo_path})
            logger.info(f"Analyzing codebase: {repo_path}")
            analysis = self.analyzer.analyze(repo_path)
            progress.log_file_analysis(
                repo_path,
                analysis.statistics.total_loc,
            )
            progress.complete_step({
                "modules": analysis.statistics.total_modules,
                "files": analysis.statistics.total_files,
                "loc": analysis.statistics.total_loc,
            })
            logger.info(f"Analysis complete: {analysis.statistics.total_modules} modules found")
            if progress_callback:
                progress_callback(30)

            # Step 3: Generate Arc42 sections one-by-one with progress
            logger.info(f"Generating Arc42 sections: {sections}")
            doc = Arc42Document()

            section_generators = {
                1: self.generator.generate_section_1,
                2: self.generator.generate_section_2,
                3: self.generator.generate_section_3,
                4: self.generator.generate_section_4,
                5: self.generator.generate_section_5,
                6: self.generator.generate_section_6,
                7: self.generator.generate_section_7,
                8: self.generator.generate_section_8,
                9: self.generator.generate_section_9,
                10: self.generator.generate_section_10,
                11: self.generator.generate_section_11,
                12: self.generator.generate_section_12,
            }

            for section_num in sections:
                name = SECTION_NAMES.get(section_num, f"Section {section_num}")
                progress.start_step(f"Generate Section {section_num}: {name}")

                try:
                    gen_func = section_generators.get(section_num)
                    if gen_func:
                        section_obj = gen_func(analysis)
                        attr_name = SECTION_ATTR_NAMES.get(section_num)
                        if attr_name:
                            setattr(doc, attr_name, section_obj)

                    # Log LLM call metrics from generator
                    last_call = self.generator.last_llm_call
                    if last_call:
                        progress.log_llm_call(**last_call)

                    progress.complete_step()

                except Exception as e:
                    progress.fail_step(str(e))
                    logger.error(f"Section {section_num} failed: {e}")

            logger.info("Sections generated successfully")
            if progress_callback:
                progress_callback(80)

            # Step 4: Format and save output
            progress.start_step("Write output", {"output_path": output_path})
            logger.info(f"Writing output to: {output_path}")
            self.formatter.write_arc42_document(doc, output_path)
            progress.complete_step()
            logger.info("Output written successfully")
            if progress_callback:
                progress_callback(100)

            progress.show_summary()
            return True

        except FileNotFoundError as e:
            progress.fail_step(str(e))
            logger.error(f"File not found: {e}")
            progress.show_summary()
            return False
        except ValueError as e:
            progress.fail_step(str(e))
            logger.error(f"Validation error: {e}")
            progress.show_summary()
            return False
        except Exception as e:
            progress.fail_step(str(e))
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            progress.show_summary()
            return False

    def _validate_inputs(self, repo_path: str) -> None:
        """
        Validate input parameters.

        Args:
            repo_path: Path to repository (local path or remote URL)

        Raises:
            FileNotFoundError: If local repo path doesn't exist
            ValueError: If configuration is invalid
        """
        # Skip path validation for remote URLs (will be cloned by analyzer)
        if not is_remote_url(repo_path):
            path = Path(repo_path)

            # Check if local path exists
            if not path.exists():
                raise FileNotFoundError(f"Repository path not found: {repo_path}")

            if not path.is_dir():
                raise ValueError(f"Repository path is not a directory: {repo_path}")

        # Validate API key with provider-specific message
        if not self.config.llm.api_key:
            env_var = self.config.llm.get_api_key_env_var()
            provider = self.config.llm.provider
            raise ValueError(
                f"API key not set for {provider} provider. "
                f"Set the {env_var} environment variable."
            )

        # Validate config
        errors = self.config.validate()
        if errors:
            # Filter out API key error since we already checked
            errors = [e for e in errors if "API key" not in e]
            if errors:
                raise ValueError(f"Configuration errors: {'; '.join(errors)}")
