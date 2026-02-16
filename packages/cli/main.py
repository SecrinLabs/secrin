"""
Secrin CLI — generate documentation for any codebase.

Usage:
    secrin generate ./my-repo
    secrin serve ./docs
    secrin doctor
"""

import click

from .generate import generate
from .serve import serve


@click.group()
@click.version_option(version="0.1.0", prog_name="secrin")
def cli():
    """Secrin — AI-powered documentation generator."""
    pass


@cli.command()
def doctor():
    """Check environment readiness."""
    import os
    import sys
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Secrin Doctor", show_header=True)
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Details")

    # Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 13)
    table.add_row(
        "Python version",
        "[green]OK[/green]" if py_ok else "[red]FAIL[/red]",
        py_ver,
    )

    # LLM API keys
    providers = {
        "Gemini": "GEMINI_API_KEY",
        "Anthropic": "ANTHROPIC_API_KEY",
        "Ollama": "OLLAMA_BASE_URL",
    }
    found_any = False
    for name, env_var in providers.items():
        val = os.environ.get(env_var)
        if val:
            found_any = True
            masked = val[:4] + "..." if len(val) > 4 else "set"
            table.add_row(name, "[green]OK[/green]", f"${env_var} = {masked}")
        else:
            table.add_row(name, "[dim]not set[/dim]", f"${env_var}")

    if not found_any:
        table.add_row(
            "LLM Provider",
            "[red]FAIL[/red]",
            "Set GEMINI_API_KEY, ANTHROPIC_API_KEY, or OLLAMA_BASE_URL",
        )

    # Git
    import shutil
    git_path = shutil.which("git")
    table.add_row(
        "Git",
        "[green]OK[/green]" if git_path else "[red]FAIL[/red]",
        git_path or "not found",
    )

    console.print(table)


cli.add_command(generate)
cli.add_command(serve)


if __name__ == "__main__":
    cli()
