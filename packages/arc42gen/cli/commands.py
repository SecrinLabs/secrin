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
        click.echo("  1. Set your API key (default provider is Gemini):")
        click.echo("     export GEMINI_API_KEY='your_key'")
        click.echo("     OR for Anthropic: export ANTHROPIC_API_KEY='your_key'")
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
        click.echo(f"  Provider: {cfg.llm.provider}")
        click.echo(f"  Model: {cfg.llm.model}")
        click.echo(f"  API Key Env: {cfg.llm.get_api_key_env_var()}")
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


def parse_sections(sections_str: str) -> list:
    """Parse sections string like '1,3,5' or 'all' into list of ints."""
    if sections_str.lower() == 'all':
        return list(range(1, 13))

    sections = []
    for part in sections_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            sections.extend(range(int(start), int(end) + 1))
        else:
            sections.append(int(part))
    return sorted(set(sections))


@cli.command()
@click.option("--repo", required=True, help="Repository path (local path)")
@click.option("--sections", default="all", help="Sections to generate: 'all', '5', '1,3,5', '1-4'")
@click.option("--output", default="./docs/arc42", help="Output directory")
@click.option("--config", "config_path", default=".arc42gen.yaml", help="Config file path")
def generate(repo: str, sections: str, output: str, config_path: str) -> None:
    """Generate Arc42 documentation from codebase."""
    from ..core.orchestrator import Orchestrator

    try:
        section_list = parse_sections(sections)
    except ValueError:
        click.echo(f"Invalid sections format: {sections}", err=True)
        click.echo("  Use: 'all', '5', '1,3,5', or '1-4'", err=True)
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
            env_var = cfg.llm.get_api_key_env_var()
            click.echo(f"{env_var} not set for {cfg.llm.provider} provider", err=True)
            click.echo(f"  Run: export {env_var}='your_key'", err=True)
            sys.exit(1)

        # Initialize orchestrator
        orchestrator = Orchestrator(cfg)

        # Run generation with progress bar
        section_str = ', '.join(map(str, section_list))
        click.echo(f"Generating Arc42 Sections [{section_str}] for: {repo}")

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
                sections=section_list,
                progress_callback=progress_callback
            )

        if success:
            click.echo(f"\nDocumentation generated successfully!")
            click.echo(f"  Output: {output}/")
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
        click.echo(f"  Language: {analysis.language}")
        click.echo(f"  Modules: {len(analysis.module_tree.get_top_level_modules())}")
        click.echo(f"  Total LOC: {analysis.statistics.total_loc:,}")
        click.echo(f"  Classes: {analysis.statistics.total_classes}")
        click.echo(f"  Functions: {analysis.statistics.total_functions}")

    except Exception as e:
        logger.exception("Analysis failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def diagrams() -> None:
    """C4 diagram generation commands."""
    pass


@diagrams.command(name="generate")
@click.option("--repo", required=True, help="Repository path")
@click.option("--output", default="./docs/diagrams", help="Output directory")
@click.option("--levels", default="1,2,3,4", help="C4 levels to generate: '1,2,3,4' or 'all'")
@click.option("--config", "config_path", default=".arc42gen.yaml", help="Config file path")
def diagrams_generate(repo: str, output: str, levels: str, config_path: str) -> None:
    """Generate C4 diagrams at all levels."""
    from ..core.analyzer import CodebaseAnalyzer
    from ..diagrams import C4Generator

    try:
        # Parse levels
        if levels.lower() == 'all':
            level_list = [1, 2, 3, 4]
        else:
            level_list = [int(l.strip()) for l in levels.split(',')]
    except ValueError:
        click.echo(f"Invalid levels: {levels}", err=True)
        sys.exit(1)

    try:
        # Load configuration
        if Path(config_path).exists():
            cfg = Config.from_yaml(config_path)
        else:
            click.echo(f"Config file not found: {config_path}", err=True)
            sys.exit(1)

        if not cfg.llm.api_key:
            env_var = cfg.llm.get_api_key_env_var()
            click.echo(f"{env_var} not set", err=True)
            sys.exit(1)

        analyzer = CodebaseAnalyzer(cfg)
        generator = C4Generator(config=cfg.llm)

        click.echo(f"Analyzing: {repo}")
        analysis = analyzer.analyze(repo)

        click.echo(f"Generating C4 diagrams (levels: {level_list})...")
        diagrams = generator.generate_all_levels(analysis, level_list)

        # Write output
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)

        if diagrams.context:
            path = output_dir / "c4_level1_context.md"
            path.write_text(diagrams.context.to_markdown())
            click.echo(f"  Level 1: {path}")

        if diagrams.containers:
            path = output_dir / "c4_level2_container.md"
            path.write_text(diagrams.containers.to_markdown())
            click.echo(f"  Level 2: {path}")

        for i, comp in enumerate(diagrams.components):
            filename = f"c4_level3_component_{comp.target_component or i+1}.md"
            path = output_dir / filename.replace(' ', '_').lower()
            path.write_text(comp.to_markdown())
            click.echo(f"  Level 3: {path}")

        for i, code in enumerate(diagrams.code):
            filename = f"c4_level4_code_{code.target_component or i+1}.md"
            path = output_dir / filename.replace(' ', '_').lower()
            path.write_text(code.to_markdown())
            click.echo(f"  Level 4: {path}")

        click.echo("\nC4 diagrams generated successfully!")

    except Exception as e:
        logger.exception("Generation failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def diataxis() -> None:
    """Diátaxis framework documentation commands."""
    pass


@diataxis.command(name="generate")
@click.option("--repo", required=True, help="Repository path")
@click.option("--output", default="./docs", help="Output directory")
@click.option("--config", "config_path", default=".arc42gen.yaml", help="Config file path")
@click.option("--type", "doc_type", default="all", help="Type: all, tutorials, how-to, reference, explanation")
def diataxis_generate(repo: str, output: str, config_path: str, doc_type: str) -> None:
    """Generate Diátaxis documentation."""
    from ..core.analyzer import CodebaseAnalyzer
    from ..diataxis import DiátaxisGenerator

    try:
        # Load configuration
        if Path(config_path).exists():
            cfg = Config.from_yaml(config_path)
        else:
            click.echo(f"Config file not found: {config_path}", err=True)
            sys.exit(1)

        if not cfg.llm.api_key:
            env_var = cfg.llm.get_api_key_env_var()
            click.echo(f"{env_var} not set", err=True)
            sys.exit(1)

        analyzer = CodebaseAnalyzer(cfg)
        generator = DiátaxisGenerator(config=cfg.llm)

        click.echo(f"Analyzing: {repo}")
        analysis = analyzer.analyze(repo)

        click.echo("Generating Diátaxis documentation...")
        doc = generator.generate_all(analysis)

        # Write output
        output_dir = Path(output)

        if doc_type in ("all", "tutorials"):
            tutorials_dir = output_dir / "tutorials"
            tutorials_dir.mkdir(parents=True, exist_ok=True)
            for tutorial in doc.tutorials:
                filename = tutorial.title.lower().replace(' ', '_') + ".md"
                (tutorials_dir / filename).write_text(tutorial.to_markdown())
            click.echo(f"  Tutorials: {tutorials_dir}/")

        if doc_type in ("all", "how-to"):
            howto_dir = output_dir / "how-to"
            howto_dir.mkdir(parents=True, exist_ok=True)
            for guide in doc.how_to_guides:
                filename = guide.title.lower().replace(' ', '_') + ".md"
                (howto_dir / filename).write_text(guide.to_markdown())
            click.echo(f"  How-To: {howto_dir}/")

        if doc_type in ("all", "reference"):
            ref_dir = output_dir / "reference"
            ref_dir.mkdir(parents=True, exist_ok=True)
            for ref in doc.references:
                filename = ref.title.lower().replace(' ', '_') + ".md"
                (ref_dir / filename).write_text(ref.to_markdown())
            click.echo(f"  Reference: {ref_dir}/")

        if doc_type in ("all", "explanation"):
            exp_dir = output_dir / "explanation"
            exp_dir.mkdir(parents=True, exist_ok=True)
            for exp in doc.explanations:
                filename = exp.title.lower().replace(' ', '_') + ".md"
                (exp_dir / filename).write_text(exp.to_markdown())
            click.echo(f"  Explanation: {exp_dir}/")

        click.echo("\nDiátaxis documentation generated successfully!")

    except Exception as e:
        logger.exception("Generation failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
