"""
secrin serve — clone the docs template, copy generated docs in, and run the dev server.

Flow:
1. Clone SecrinLabs/secrin-docs-template into a temp dir (or reuse existing)
2. Copy generated MDX files into content/docs/
3. pnpm install
4. pnpm dev
"""

import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

import click
from rich.console import Console

TEMPLATE_REPO = "https://github.com/SecrinLabs/secrin-docs-template.git"
DOCS_SUBDIR = "content/docs"

console = Console()


def _check_pnpm():
    """Ensure pnpm is available."""
    if not shutil.which("pnpm"):
        raise click.ClickException(
            "pnpm is required but not found. Install it: npm install -g pnpm"
        )


def _clone_template(target: Path):
    """Shallow-clone the docs template repo."""
    console.print(f"Cloning template into [bold]{target}[/bold] ...")
    subprocess.run(
        ["git", "clone", "--depth", "1", TEMPLATE_REPO, str(target)],
        check=True,
    )
    # Remove .git so it's a fresh copy, not a clone
    git_dir = target / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)


def _copy_docs(docs_src: Path, site_dir: Path):
    """Copy generated docs into the template's content/docs/ folder."""
    dest = site_dir / DOCS_SUBDIR
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(docs_src, dest)
    count = sum(1 for _ in dest.rglob("*") if _.is_file())
    console.print(f"Copied [bold]{count}[/bold] files into [dim]{dest}[/dim]")


def _pnpm_install(site_dir: Path):
    """Run pnpm install in the site directory."""
    with console.status("[bold]Installing dependencies (pnpm install)..."):
        subprocess.run(
            ["pnpm", "install"],
            cwd=str(site_dir),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    console.print("  [green]Dependencies installed[/green]")


def _pnpm_dev(site_dir: Path, port: int):
    """Run pnpm dev (blocking). Ctrl+C to stop."""
    console.print(f"\nStarting dev server on [bold]http://localhost:{port}[/bold]")
    console.print("Press Ctrl+C to stop.\n")
    try:
        subprocess.run(
            ["pnpm", "dev", "--port", str(port)],
            cwd=str(site_dir),
            check=True,
        )
    except KeyboardInterrupt:
        console.print("\nStopped.")


@click.command()
@click.argument("docs_dir", default="./docs")
@click.option("--port", default=3000, help="Dev server port (default: 3000)")
@click.option("--site-dir", default=None, help="Reuse an existing cloned template directory instead of cloning fresh")
@click.option("--no-browser", is_flag=True, help="Don't auto-open browser")
def serve(docs_dir, port, site_dir, no_browser):
    """Serve generated docs locally using the Secrin docs template.

    Clones the Fumadocs-based template, copies your generated MDX files into
    content/docs/, installs dependencies, and runs pnpm dev.

    DOCS_DIR is the directory containing generated documentation (default: ./docs).
    """
    _check_pnpm()

    docs_path = Path(docs_dir).resolve()
    if not docs_path.is_dir():
        raise click.ClickException(f"Docs directory not found: {docs_path}")

    # Determine site directory
    if site_dir:
        site = Path(site_dir).resolve()
        if not site.is_dir():
            raise click.ClickException(f"Site directory not found: {site}")
        console.print(f"Reusing existing site at [bold]{site}[/bold]")
    else:
        site = docs_path.parent / ".secrin-site"
        if site.exists():
            console.print(f"Reusing cached site at [bold]{site}[/bold]")
        else:
            _clone_template(site)

    _copy_docs(docs_path, site)
    _pnpm_install(site)

    if not no_browser:
        # Open after a short delay so the server has time to start
        import threading
        threading.Timer(3.0, webbrowser.open, args=[f"http://localhost:{port}"]).start()

    _pnpm_dev(site, port)
