"""
secrin generate — generate all documentation for a codebase.

Runs Arc42 + C4 diagrams + Diataxis docs inline (no Redis/workers needed).
"""

import json
import logging
import os
import time
import traceback
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from packages.arc42gen.models.config import Config, LLMConfig
from packages.arc42gen.core.analyzer import CodebaseAnalyzer
from packages.arc42gen.core.orchestrator import Orchestrator
from packages.arc42gen.diagrams import C4Generator
from packages.arc42gen.diataxis import DiátaxisGenerator
from packages.arc42gen.utils.git_utils import is_remote_url, clone_repository, cleanup_cloned_repo

logger = logging.getLogger(__name__)

console = Console()


def _add_mdx_frontmatter(content: str, title: str, description: str = "") -> str:
    """Add MDX frontmatter for Fumadocs compatibility."""
    safe_title = title.replace('"', '\\"')
    safe_description = (description or title).replace('"', '\\"')
    return f'---\ntitle: "{safe_title}"\ndescription: "{safe_description}"\n---\n\n' + content


def _detect_provider() -> tuple[str, str]:
    """Auto-detect LLM provider from environment variables.

    Returns (provider, api_key).
    """
    if key := os.environ.get("GEMINI_API_KEY"):
        return "gemini", key
    if key := os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic", key
    if os.environ.get("OLLAMA_BASE_URL"):
        return "ollama", "ollama"
    raise click.ClickException(
        "No LLM API key found. Set one of: GEMINI_API_KEY, ANTHROPIC_API_KEY, or OLLAMA_BASE_URL"
    )


def _build_config(provider: str, api_key: str) -> Config:
    """Build a Config object from detected/overridden provider settings."""
    model = LLMConfig.get_default_model(provider)
    config_dict = {
        "llm": {
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "max_tokens": 16000,
            "base_url": os.environ.get("OLLAMA_BASE_URL", "") if provider == "ollama" else "",
            "timeout": int(os.environ.get("OLLAMA_TIMEOUT", "0")) if provider == "ollama" else 0,
        },
        "repository": {},
        "arc42": {"sections": list(range(1, 13))},
        "decomposition": {},
        "output": {"path": "./docs"},
    }
    return Config.from_dict(config_dict)


def _write_files(files: dict[str, str], output_dir: Path) -> int:
    """Write generated files to disk. Returns count of files written."""
    count = 0
    for rel_path, content in files.items():
        dest = output_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        count += 1
    return count


@click.command()
@click.argument("repo_path", default=".")
@click.option("-o", "--output", "output_dir", default="./docs", help="Output directory (default: ./docs)")
@click.option("--provider", type=click.Choice(["gemini", "anthropic", "ollama"]), default=None, help="LLM provider override")
@click.option("--skip-arc42", is_flag=True, help="Skip Arc42 generation")
@click.option("--skip-diagrams", is_flag=True, help="Skip C4 diagram generation")
@click.option("--skip-diataxis", is_flag=True, help="Skip Diataxis generation")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def generate(repo_path, output_dir, provider, skip_arc42, skip_diagrams, skip_diataxis, verbose):
    """Generate documentation for a codebase.

    REPO_PATH can be a local directory, ".", or a remote git URL.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    pipeline_start = time.time()
    output_path = Path(output_dir).resolve()

    # --- Detect / override provider ---
    if provider:
        env_var = LLMConfig.API_KEY_ENV_VARS.get(provider, "")
        api_key = os.environ.get(env_var, "")
        if provider != "ollama" and not api_key:
            raise click.ClickException(f"Provider {provider} selected but ${env_var} is not set")
        if provider == "ollama":
            api_key = "ollama"
    else:
        provider, api_key = _detect_provider()

    cfg = _build_config(provider, api_key)

    console.print(Panel(
        f"[bold]Provider:[/bold] {provider} ({LLMConfig.get_default_model(provider)})\n"
        f"[bold]Repo:[/bold]     {repo_path}\n"
        f"[bold]Output:[/bold]   {output_path}",
        title="secrin generate",
    ))

    # --- Resolve repo path ---
    cloned_path = None
    if is_remote_url(repo_path):
        with console.status("Cloning repository..."):
            cloned_path = clone_repository(repo_path)
            actual_repo = str(cloned_path)
    else:
        actual_repo = str(Path(repo_path).resolve())
        if not Path(actual_repo).is_dir():
            raise click.ClickException(f"Not a directory: {actual_repo}")

    files: dict[str, str] = {}

    try:
        # --- Step 1: Analyze codebase ---
        with console.status("[bold]Analyzing codebase..."):
            t0 = time.time()
            analyzer = CodebaseAnalyzer(cfg)
            analysis = analyzer.analyze(actual_repo)
        console.print(
            f"  [green]Analysis complete[/green] — "
            f"{analysis.statistics.total_files} files, "
            f"{analysis.statistics.total_loc} LOC, "
            f"{analysis.statistics.total_modules} modules "
            f"[dim]({time.time() - t0:.1f}s)[/dim]"
        )

        # --- Step 2: Arc42 ---
        if not skip_arc42:
            with console.status("[bold]Generating Arc42 documentation..."):
                t0 = time.time()
                import tempfile
                arc42_tmp = tempfile.mkdtemp()
                try:
                    orchestrator = Orchestrator(cfg, verbose=False)
                    success = orchestrator.run(repo_path=actual_repo, output_path=arc42_tmp)
                    if success:
                        tmp_path = Path(arc42_tmp)
                        for file_path in tmp_path.rglob("*.md"):
                            rel = file_path.relative_to(tmp_path)
                            content = file_path.read_text()
                            title = rel.stem.replace("_", " ").replace("-", " ").title()
                            files[f"architecture/{rel.stem}.mdx"] = _add_mdx_frontmatter(
                                content, title, f"Arc42 - {title}"
                            )
                finally:
                    import shutil
                    shutil.rmtree(arc42_tmp, ignore_errors=True)
            console.print(
                f"  [green]Arc42 done[/green] — "
                f"{sum(1 for k in files if k.startswith('architecture/'))} files "
                f"[dim]({time.time() - t0:.1f}s)[/dim]"
            )

        # --- Step 3: C4 Diagrams ---
        if not skip_diagrams:
            with console.status("[bold]Generating C4 diagrams..."):
                t0 = time.time()
                try:
                    c4_gen = C4Generator(config=cfg.llm)
                    c4_diagrams = c4_gen.generate_all_levels(analysis, levels=[1, 2, 3, 4])

                    if c4_diagrams.context:
                        files["diagrams/c4-level1-context.mdx"] = _add_mdx_frontmatter(
                            c4_diagrams.context.to_markdown(),
                            "System Context Diagram",
                            "C4 Level 1 - Shows the system in context with external actors and systems",
                        )
                    if c4_diagrams.containers:
                        files["diagrams/c4-level2-container.mdx"] = _add_mdx_frontmatter(
                            c4_diagrams.containers.to_markdown(),
                            "Container Diagram",
                            "C4 Level 2 - Shows high-level technology choices",
                        )
                    for i, comp in enumerate(c4_diagrams.components):
                        name = comp.target_component or f"component-{i+1}"
                        safe_name = name.lower().replace(" ", "-").replace("_", "-")
                        files[f"diagrams/c4-level3-{safe_name}.mdx"] = _add_mdx_frontmatter(
                            comp.to_markdown(),
                            f"Component Diagram: {name}",
                            f"C4 Level 3 - Internal components of {name}",
                        )
                    for i, code in enumerate(c4_diagrams.code):
                        name = code.target_component or f"code-{i+1}"
                        safe_name = name.lower().replace(" ", "-").replace("_", "-")
                        files[f"diagrams/c4-level4-{safe_name}.mdx"] = _add_mdx_frontmatter(
                            code.to_markdown(),
                            f"Code Diagram: {name}",
                            f"C4 Level 4 - Class/code structure of {name}",
                        )
                except Exception as e:
                    console.print(f"  [yellow]C4 diagrams failed:[/yellow] {e}")
                    if verbose:
                        console.print(traceback.format_exc())
            console.print(
                f"  [green]C4 diagrams done[/green] — "
                f"{sum(1 for k in files if k.startswith('diagrams/'))} files "
                f"[dim]({time.time() - t0:.1f}s)[/dim]"
            )

        # --- Step 4: Diataxis ---
        if not skip_diataxis:
            with console.status("[bold]Generating Diataxis documentation..."):
                t0 = time.time()
                try:
                    diataxis_gen = DiátaxisGenerator(config=cfg.llm)
                    diataxis_doc = diataxis_gen.generate_all(analysis)

                    for tutorial in diataxis_doc.tutorials:
                        safe_name = tutorial.title.lower().replace(" ", "-").replace("_", "-")
                        files[f"tutorials/{safe_name}.mdx"] = _add_mdx_frontmatter(
                            tutorial.to_markdown(), f"Tutorial: {tutorial.title}", tutorial.goal,
                        )
                    for guide in diataxis_doc.how_to_guides:
                        safe_name = guide.title.lower().replace(" ", "-").replace("_", "-")
                        files[f"how-to/{safe_name}.mdx"] = _add_mdx_frontmatter(
                            guide.to_markdown(), f"How-To: {guide.title}", guide.problem,
                        )
                    for ref in diataxis_doc.references:
                        safe_name = ref.title.lower().replace(" ", "-").replace("_", "-")
                        files[f"reference/{safe_name}.mdx"] = _add_mdx_frontmatter(
                            ref.to_markdown(), ref.title,
                            ref.overview[:200] if ref.overview else "Technical reference documentation",
                        )
                    for exp in diataxis_doc.explanations:
                        safe_name = exp.title.lower().replace(" ", "-").replace("_", "-")
                        files[f"explanation/{safe_name}.mdx"] = _add_mdx_frontmatter(
                            exp.to_markdown(), f"Explanation: {exp.title}",
                            exp.problem[:200] if exp.problem else "Understanding the architecture",
                        )
                except Exception as e:
                    console.print(f"  [yellow]Diataxis failed:[/yellow] {e}")
                    if verbose:
                        console.print(traceback.format_exc())
            diataxis_count = sum(
                1 for k in files
                if k.startswith(("tutorials/", "how-to/", "reference/", "explanation/"))
            )
            console.print(
                f"  [green]Diataxis done[/green] — {diataxis_count} files "
                f"[dim]({time.time() - t0:.1f}s)[/dim]"
            )

        # --- Step 5: Index + meta.json ---
        files["index.mdx"] = f"""---
title: Documentation
description: Auto-generated documentation for {analysis.repo_name}
---

# {analysis.repo_name} Documentation

Welcome to the auto-generated documentation for **{analysis.repo_name}**.

## Documentation Structure

### Architecture
Arc42 architecture documentation covering system design, building blocks, and technical decisions.

### Diagrams
C4 model diagrams at all 4 levels: system context, containers, components, and code.

### Tutorials
Learning-oriented guides to help you get started with the project.

### How-To
Problem-solving guides for common tasks and troubleshooting.

### Reference
Technical reference documentation including API details and configuration.

### Explanation
Deep-dive explanations of architecture decisions and trade-offs.

---

*Generated by [Secrin](https://www.secrinlabs.com/)*
"""

        meta = {
            "title": analysis.repo_name,
            "pages": ["index", "architecture", "diagrams", "tutorials", "how-to", "reference", "explanation"],
        }
        files["meta.json"] = json.dumps(meta, indent=2)

        # --- Write to disk ---
        with console.status("[bold]Writing files..."):
            written = _write_files(files, output_path)

        total_time = time.time() - pipeline_start
        console.print(
            Panel(
                f"[bold green]{written} files[/bold green] written to [bold]{output_path}[/bold]\n"
                f"Total time: {total_time:.1f}s",
                title="Done",
            )
        )

    finally:
        if cloned_path:
            cleanup_cloned_repo(cloned_path)
