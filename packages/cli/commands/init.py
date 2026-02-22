"""
`secrin init --repo <url>` command.

Orchestrates: clone → parse → analyse → generate wiki → save config.
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import typer

from packages.cli.core import cloner, parser, analyser, writer
from packages.cli.core import config as cfg_module
from packages.cli.core.config import Config
from packages.arc42gen.providers.factory import get_default_model

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-5-20250929",
    "gemini": "gemini-2.0-flash",
    "ollama": "llama3.2",
}

_API_KEY_ENVS: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def _model_for_provider(provider: str, model_override: str) -> str:
    if model_override:
        return model_override
    return _DEFAULT_MODELS.get(provider.lower(), "")


def _check_api_key(provider: str) -> None:
    env_var = _API_KEY_ENVS.get(provider.lower())
    if env_var and not os.environ.get(env_var):
        typer.echo(
            f"\n[error] {env_var} is not set.\n"
            f"Export it before running:\n"
            f"  export {env_var}=<your-key>\n",
            err=True,
        )
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

def init(
    repo: str = typer.Option(..., "--repo", help="GitHub repo URL to clone and analyse"),
    force: bool = typer.Option(False, "--force", help="Regenerate if already initialised"),
    provider: str = typer.Option(
        "anthropic", "--provider",
        help="LLM provider: anthropic | gemini | ollama",
    ),
    model: str = typer.Option(
        "", "--model",
        help="Model name (defaults to provider's default)",
    ),
) -> None:
    """Clone a repo, parse it, and generate a decision-based wiki in .secrin/wiki/."""
    cwd = Path.cwd()

    if cfg_module.exists(cwd) and not force:
        typer.echo(".secrin/ already exists.")
        typer.echo("Run with --force to regenerate the wiki.")
        raise typer.Exit()

    _check_api_key(provider)

    resolved_model = _model_for_provider(provider, model)

    # 1. Clone
    typer.echo(f"\nCloning repo...")
    repo_path = cloner.clone(repo)
    typer.echo(f"  Cloned to {repo_path}\n")

    # 2. Parse (parser prints per-file progress)
    typer.echo("Parsing source files...")
    parsed = parser.parse_repo(repo_path)
    total_fns = sum(len(pf.functions) for pf in parsed)
    total_cls = sum(len(pf.classes) for pf in parsed)
    typer.echo(
        f"  Parsed {len(parsed)} files "
        f"({total_fns} functions/methods, {total_cls} classes)\n"
    )

    # 3. Analyse
    typer.echo("Analysing module structure...")
    modules = analyser.analyse(parsed)
    typer.echo(f"  Found {len(modules)} modules: {', '.join(m.name for m in modules)}\n")

    # 4. Generate wiki
    wiki_path = cwd / ".secrin" / "wiki"
    wiki_path.mkdir(parents=True, exist_ok=True)
    typer.echo("Generating wiki...")
    files = writer.generate_wiki(
        modules=modules,
        parsed_files=parsed,
        repo_url=repo,
        wiki_path=wiki_path,
        provider=provider,
        model=resolved_model,
    )

    # 5. Save config
    today = date.today().isoformat()
    cfg = Config(
        project_name=repo_path.name,
        repo_url=repo,
        repo_path=str(repo_path),
        wiki_path=".secrin/wiki",
        llm_provider=provider,
        llm_model=resolved_model,
        created_at=today,
        last_generated=today,
    )
    cfg_module.save(cfg, cwd)

    # 6. Summary
    typer.echo(f"\nWiki ready at .secrin/wiki/")
    for f in files:
        rel = f.relative_to(wiki_path)
        typer.echo(f"  {rel}")

    typer.echo(f'\nRun: secrin ask "how does this project work?"')
