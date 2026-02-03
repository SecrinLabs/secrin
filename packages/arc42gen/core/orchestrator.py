"""
Main workflow orchestrator.
"""

import logging
from pathlib import Path
from typing import Callable, Optional

from ..models.config import Config
from ..utils.git_utils import is_remote_url
from .analyzer import CodebaseAnalyzer
from .generator import Arc42Generator
from .formatter import OutputFormatter


logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Coordinates the documentation generation workflow.

    Workflow:
    1. Validate inputs
    2. Analyze codebase (CodebaseAnalyzer)
    3. Generate Section 5 (Arc42Generator)
    4. Format and save output (OutputFormatter)

    Supports multiple LLM providers (Anthropic, Gemini) and
    multiple languages (Python, JavaScript, TypeScript).
    """

    def __init__(self, config: Config):
        """
        Initialize the orchestrator.

        Args:
            config: Configuration object
        """
        self.config = config
        self.analyzer = CodebaseAnalyzer(config)
        # Use the new config-based initialization for the generator
        self.generator = Arc42Generator(config=config.llm)
        self.formatter = OutputFormatter(config)

    def run(
        self,
        repo_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> bool:
        """
        Execute full documentation generation pipeline.

        Args:
            repo_path: Path to repository (local)
            output_path: Output directory path
            progress_callback: Optional callback for progress updates (0-100)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Step 1: Validate inputs
            logger.info("Validating inputs...")
            self._validate_inputs(repo_path)
            if progress_callback:
                progress_callback(10)

            # Step 2: Analyze codebase
            logger.info(f"Analyzing codebase: {repo_path}")
            analysis = self.analyzer.analyze(repo_path)
            logger.info(f"Analysis complete: {analysis.statistics.total_modules} modules found")
            if progress_callback:
                progress_callback(40)

            # Step 3: Generate Arc42 Section 5
            logger.info("Generating Arc42 Section 5...")
            section_5 = self.generator.generate_section_5(analysis)
            logger.info("Section 5 generated successfully")
            if progress_callback:
                progress_callback(80)

            # Step 4: Format and save output
            logger.info(f"Writing output to: {output_path}")
            self.formatter.write_section_5(section_5, output_path)
            logger.info("Output written successfully")
            if progress_callback:
                progress_callback(100)

            return True

        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            return False
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return False
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
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
