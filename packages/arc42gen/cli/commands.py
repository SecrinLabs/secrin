"""
Click commands for arc42gen CLI.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Optional

import click

from ..models.config import Config


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.0")
@click.option('--debug/--no-debug', default=False, help='Enable debug logging')
def cli(debug: bool) -> None:
    """Arc42 Documentation Generator - AI-powered architectural docs from code."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.group()
def config() -> None:
    """Configuration management commands."""
    pass


@config.command(name="init")
@click.option("--output", default=".arc42gen.yaml", help="Output file path")
@click.option("--force", is_flag=True, help="Overwrite existing file")
def config_init(output: str, force: bool) -> None:
    """Create default configuration file."""
    from .utils import create_default_config

    try:
        create_default_config(output, force=force)
        click.echo(f"Configuration file created: {output}")
        click.echo("  Next steps:")
        click.echo("  1. Set your API key: export ANTHROPIC_API_KEY='your_key'")
        click.echo("  2. Edit .arc42gen.yaml to customize settings")
        click.echo("  3. Run: arc42gen generate --repo /path/to/repo")
    except FileExistsError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("  Use --force to overwrite", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error creating config: {e}", err=True)
        sys.exit(1)


@config.command(name="validate")
@click.option("--config", "config_path", default=".arc42gen.yaml", help="Config file to validate")
def config_validate(config_path: str) -> None:
    """Validate configuration file."""
    try:
        cfg = Config.from_yaml(config_path)
        errors = cfg.validate()

        if errors:
            click.echo("Configuration has errors:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)

        click.echo("Configuration is valid")
        click.echo(f"  Model: {cfg.llm.model}")
        click.echo(f"  Language: {cfg.repository.language or 'auto-detect'}")
        click.echo(f"  Sections: {cfg.arc42.sections}")
        click.echo(f"  Output: {cfg.output.path}")

    except FileNotFoundError:
        click.echo(f"Config file not found: {config_path}", err=True)
        click.echo("  Run: arc42gen config init", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Invalid configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--repo", required=True, help="Repository path (local path)")
@click.option("--section", default=5, type=int, help="Arc42 section number (MVP: 5 only)")
@click.option("--output", default="./docs/arc42", help="Output directory")
@click.option("--config", "config_path", default=".arc42gen.yaml", help="Config file path")
def generate(repo: str, section: int, output: str, config_path: str) -> None:
    """Generate Arc42 documentation from codebase."""
    from ..core.orchestrator import Orchestrator

    if section != 5:
        click.echo("MVP supports Section 5 only. Coming soon: all sections!", err=True)
        sys.exit(1)

    try:
        # Load configuration
        if Path(config_path).exists():
            cfg = Config.from_yaml(config_path)
        else:
            click.echo(f"Config file not found: {config_path}", err=True)
            click.echo("  Run: arc42gen config init", err=True)
            sys.exit(1)

        # Validate API key
        if not cfg.llm.api_key:
            click.echo("ANTHROPIC_API_KEY not set", err=True)
            click.echo("  Run: export ANTHROPIC_API_KEY='your_key'", err=True)
            sys.exit(1)

        # Initialize orchestrator
        orchestrator = Orchestrator(cfg)

        # Run generation with progress bar
        click.echo(f"Generating Arc42 Section {section} for: {repo}")

        with click.progressbar(
            length=100,
            label="Processing",
            show_eta=True
        ) as bar:
            def progress_callback(pct: int) -> None:
                current = bar.pos
                if pct > current:
                    bar.update(pct - current)

            success = orchestrator.run(
                repo_path=repo,
                output_path=output,
                progress_callback=progress_callback
            )

        if success:
            click.echo(f"\nDocumentation generated successfully!")
            click.echo(f"  Main file: {output}/arc42_section_5.md")
            if cfg.output.create_diagrams_folder:
                click.echo(f"  Diagrams: {output}/diagrams/")
        else:
            click.echo("\nGeneration failed. Check logs for details.", err=True)
            sys.exit(1)

    except FileNotFoundError as e:
        click.echo(f"File not found: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.exception("Generation failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--repo", required=True, help="Repository path")
@click.option("--output", default="analysis.json", help="Output JSON file")
@click.option("--config", "config_path", default=".arc42gen.yaml", help="Config file path")
def analyze(repo: str, output: str, config_path: str) -> None:
    """Analyze codebase and output raw analysis JSON (for debugging)."""
    from ..core.analyzer import CodebaseAnalyzer

    try:
        # Load or create config
        if Path(config_path).exists():
            cfg = Config.from_yaml(config_path)
        else:
            # Use default config for analysis-only mode
            cfg = Config.from_dict({
                'llm': {'api_key': 'not-needed-for-analysis'},
                'repository': {'language': 'python'},
                'arc42': {'sections': [5]},
                'decomposition': {},
                'output': {},
            })

        analyzer = CodebaseAnalyzer(cfg)

        click.echo(f"Analyzing: {repo}")
        analysis = analyzer.analyze(repo)

        # Save to JSON
        with open(output, 'w') as f:
            json.dump(analysis.to_dict(), f, indent=2)

        click.echo(f"Analysis saved to: {output}")
        click.echo(f"  Modules: {len(analysis.module_tree.get_top_level_modules())}")
        click.echo(f"  Total LOC: {analysis.statistics.total_loc:,}")
        click.echo(f"  Classes: {analysis.statistics.total_classes}")
        click.echo(f"  Functions: {analysis.statistics.total_functions}")

    except Exception as e:
        logger.exception("Analysis failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
