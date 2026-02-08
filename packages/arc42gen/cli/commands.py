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
@click.option("--verbose", "-v", is_flag=True, default=False, help="Show detailed step-by-step progress with LLM metrics")
@click.option("--quiet", "-q", is_flag=True, default=False, help="Suppress all output except errors")
def generate(repo: str, sections: str, output: str, config_path: str, verbose: bool, quiet: bool) -> None:
    """Generate Arc42 documentation from codebase."""
    from ..core.orchestrator import Orchestrator

    try:
        section_list = parse_sections(sections)
    except ValueError:
        click.echo(f"Invalid sections format: {sections}", err=True)
        click.echo("  Use: 'all', '5', '1,3,5', or '1-4'", err=True)
        sys.exit(1)

    # Resolve verbosity: --quiet overrides --verbose
    show_progress = not quiet
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)

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

        # Initialize orchestrator with verbose flag
        orchestrator = Orchestrator(cfg, verbose=verbose or show_progress)

        section_str = ', '.join(map(str, section_list))
        if show_progress:
            click.echo(f"Generating Arc42 Sections [{section_str}] for: {repo}")

        success = orchestrator.run(
            repo_path=repo,
            output_path=output,
            sections=section_list,
        )

        if success:
            if show_progress:
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


@cli.command()
@click.option("--output", default="./docs/arc42", help="Output directory to check for status")
@click.option("--watch", "-w", is_flag=True, default=False, help="Continuously watch status (refresh every 2s)")
def status(output: str, watch: bool) -> None:
    """Show current generation status from .arc42gen-status.json."""
    import time

    status_path = Path(output) / ".arc42gen-status.json"

    def _display_status():
        if not status_path.exists():
            click.echo("No status file found. Generation may not have started yet.")
            click.echo(f"  Expected: {status_path}")
            return False

        try:
            data = json.loads(status_path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            click.echo(f"Error reading status file: {e}", err=True)
            return False

        # Use Rich for display if available
        try:
            from rich.console import Console
            from rich.table import Table

            console = Console()

            current = data.get("current_step", "idle")
            elapsed = data.get("elapsed", 0)
            console.print(f"[bold]Status:[/] {data.get('status', 'unknown')} | "
                          f"[bold]Current:[/] {current or 'idle'} | "
                          f"[bold]Elapsed:[/] {elapsed:.1f}s")

            # Steps table
            steps = data.get("steps", [])
            if steps:
                table = Table(show_header=True)
                table.add_column("Step")
                table.add_column("Status")
                table.add_column("Duration")

                for step in steps:
                    status_val = step.get("status", "")
                    if status_val == "complete":
                        icon = "[green]\u2713[/]"
                    elif status_val == "failed":
                        icon = "[red]\u2717[/]"
                    elif status_val == "running":
                        icon = "[yellow]\u25cb[/]"
                    else:
                        icon = "[dim]\u25cb[/]"

                    dur = step.get("duration")
                    dur_str = f"{dur:.1f}s" if dur else "-"
                    table.add_row(step.get("name", "?"), f"{icon} {status_val}", dur_str)

                console.print(table)

            # Metrics
            metrics = data.get("metrics", {})
            if metrics:
                console.print(
                    f"  Files: {metrics.get('files_analyzed', 0)} | "
                    f"LOC: {metrics.get('total_loc', 0):,} | "
                    f"LLM calls: {metrics.get('llm_calls', 0)} | "
                    f"Tokens: {metrics.get('tokens_in', 0):,}in/{metrics.get('tokens_out', 0):,}out | "
                    f"Errors: {metrics.get('errors', 0)}"
                )

        except ImportError:
            # Fallback without Rich
            click.echo(json.dumps(data, indent=2))

        return data.get("status") == "running"

    if watch:
        try:
            while True:
                click.clear()
                is_running = _display_status()
                if not is_running:
                    break
                time.sleep(2)
        except KeyboardInterrupt:
            pass
    else:
        _display_status()


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
    """Diataxis framework documentation commands."""
    pass


@diataxis.command(name="generate")
@click.option("--repo", required=True, help="Repository path")
@click.option("--output", default="./docs", help="Output directory")
@click.option("--config", "config_path", default=".arc42gen.yaml", help="Config file path")
@click.option("--type", "doc_type", default="all", help="Type: all, tutorials, how-to, reference, explanation")
def diataxis_generate(repo: str, output: str, config_path: str, doc_type: str) -> None:
    """Generate Diataxis documentation."""
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

        click.echo("Generating Diataxis documentation...")
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

        click.echo("\nDiataxis documentation generated successfully!")

    except Exception as e:
        logger.exception("Generation failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def jobs() -> None:
    """Job queue management commands."""
    pass


@jobs.command(name="submit")
@click.option("--repo", required=True, help="Source repository URL (e.g. https://github.com/owner/repo)")
@click.option("--branch", default="main", help="Branch to analyze")
@click.option("--token", envvar="GITHUB_TOKEN", help="GitHub access token")
@click.option("--owner", required=True, help="GitHub owner of the docs repo")
@click.option("--repo-name", required=True, help="Docs repo name")
@click.option("--source-owner", required=True, help="Source repo owner")
@click.option("--source-name", required=True, help="Source repo name")
@click.option("--project-id", default="cli", help="Project ID for tracking")
@click.option("--api-url", default="http://localhost:8001", help="Arc42gen API URL")
@click.option("--wait", "-w", is_flag=True, help="Wait for job to complete")
def jobs_submit(
    repo: str, branch: str, token: str, owner: str, repo_name: str,
    source_owner: str, source_name: str, project_id: str, api_url: str, wait: bool,
) -> None:
    """Submit a doc generation job via the API."""
    import requests
    import time

    if not token:
        click.echo("Error: --token or GITHUB_TOKEN required", err=True)
        sys.exit(1)

    payload = {
        "source_repo_url": repo,
        "branch": branch,
        "github_token": token,
        "owner": owner,
        "repo_name": repo_name,
        "source_owner": source_owner,
        "source_name": source_name,
        "project_id": project_id,
    }

    try:
        resp = requests.post(f"{api_url}/jobs", json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        job_id = data["job_id"]
        click.echo(f"Job submitted: {job_id}")

        if wait:
            click.echo("Watching job progress...")
            while True:
                time.sleep(3)
                status_resp = requests.get(f"{api_url}/jobs/{job_id}", timeout=10)
                status_data = status_resp.json()
                progress = status_data.get("progress", 0)
                step = status_data.get("current_step", "")
                status = status_data.get("status", "unknown")

                click.echo(f"  [{progress}%] {status}: {step}")

                if status in ("success", "failed", "cancelled"):
                    if status == "success":
                        result = status_data.get("result", {})
                        click.echo(f"\nDone! {result.get('files_count', 0)} files generated in {result.get('total_time', 0)}s")
                    elif status == "failed":
                        click.echo(f"\nFailed: {status_data.get('error', 'Unknown error')}", err=True)
                        sys.exit(1)
                    break

    except requests.ConnectionError:
        click.echo(f"Error: Cannot connect to {api_url}. Is the API running?", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@jobs.command(name="status")
@click.argument("job_id")
@click.option("--api-url", default="http://localhost:8001", help="Arc42gen API URL")
@click.option("--watch", "-w", is_flag=True, help="Continuously poll status")
def jobs_status(job_id: str, api_url: str, watch: bool) -> None:
    """Check the status of a job."""
    import requests
    import time

    def _show_status():
        resp = requests.get(f"{api_url}/jobs/{job_id}", timeout=10)
        if resp.status_code == 404:
            click.echo(f"Job {job_id} not found", err=True)
            sys.exit(1)
        data = resp.json()
        click.echo(
            f"Status: {data['status']} | Progress: {data.get('progress', 0)}% | "
            f"Step: {data.get('current_step', '-')}"
        )
        if data.get("error"):
            click.echo(f"Error: {data['error']}", err=True)
        if data.get("result"):
            click.echo(f"Result: {json.dumps(data['result'], indent=2)}")
        return data["status"]

    try:
        if watch:
            while True:
                status = _show_status()
                if status in ("success", "failed", "cancelled"):
                    break
                time.sleep(3)
        else:
            _show_status()
    except requests.ConnectionError:
        click.echo(f"Error: Cannot connect to {api_url}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@jobs.command(name="cancel")
@click.argument("job_id")
@click.option("--api-url", default="http://localhost:8001", help="Arc42gen API URL")
def jobs_cancel(job_id: str, api_url: str) -> None:
    """Cancel a queued or running job."""
    import requests

    try:
        resp = requests.delete(f"{api_url}/jobs/{job_id}", timeout=10)
        if resp.status_code == 404:
            click.echo(f"Job {job_id} not found", err=True)
            sys.exit(1)
        data = resp.json()
        click.echo(f"Job {job_id}: {data.get('status', 'unknown')}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@jobs.command(name="list")
@click.option("--api-url", default="http://localhost:8001", help="Arc42gen API URL")
def jobs_list(api_url: str) -> None:
    """List recent jobs."""
    import requests

    try:
        resp = requests.get(f"{api_url}/jobs", timeout=10)
        data = resp.json()
        job_list = data.get("jobs", [])

        if not job_list:
            click.echo("No jobs found.")
            return

        for j in job_list:
            click.echo(
                f"  {j['job_id'][:12]}  {j.get('status', '?'):10s}  "
                f"{j.get('progress', 0):3d}%  {j.get('current_step', '-')}"
            )
    except requests.ConnectionError:
        click.echo(f"Error: Cannot connect to {api_url}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
