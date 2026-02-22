"""
`secrin post-commit` and `secrin install-hooks` commands.

post-commit:
    Detects files changed in HEAD commit, updates Neo4j incrementally,
    re-summarizes + re-embeds new nodes, then regenerates only the
    affected wiki pages (module pages + architecture.md).

install-hooks:
    Writes a git post-commit hook script to .git/hooks/post-commit
    and makes it executable.
"""
from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from packages.cli.graph.neo4j_client import NeoClient
from packages.cli.graph.diff import get_changed_files, update_changed_files
from packages.cli.agents.wiki_writer import (
    _fetch_module,
    _render_module_md,
    _render_architecture_md,
    _render_readme,
    _slug,
    _Q_ALL_MODULES,
    _Q_ALL_DOMAINS,
    _Q_IMPORT_GRAPH,
)
from packages.config.settings import Settings

console = Console()

# ---------------------------------------------------------------------------
# Hook script content
# ---------------------------------------------------------------------------

_HOOK_SCRIPT = """\
#!/bin/sh
# Secrin post-commit hook
# Auto-updates the Neo4j graph and wiki for files changed in this commit.
# Installed by: secrin install-hooks
# Remove to disable: rm .git/hooks/post-commit

cd "$(git rev-parse --show-toplevel)"
secrin post-commit 2>&1 || true
exit 0
"""


# ---------------------------------------------------------------------------
# post-commit command
# ---------------------------------------------------------------------------

def post_commit(
    output: str = typer.Option(
        "docs/wiki",
        "--output", "-o",
        help="Wiki output directory (must already exist)",
    ),
    repo: str = typer.Option(
        ".",
        "--repo",
        help="Path to the git repo root (defaults to cwd)",
    ),
    skip_wiki: bool = typer.Option(
        False,
        "--skip-wiki",
        help="Update graph only; skip wiki regeneration",
    ),
) -> None:
    """
    Incrementally update the graph + wiki for files changed in HEAD commit.

    Detects changed files via `git diff-tree HEAD`, deletes stale Neo4j
    nodes, re-parses, re-summarizes, re-embeds, then regenerates only
    the affected module pages and architecture.md.

    This command is designed to be called from a git post-commit hook.
    """
    repo_path  = Path(repo).resolve()
    output_dir = Path(output)
    settings   = Settings()

    # ── 1. Get changed files ──────────────────────────────────────────────────
    to_update, to_delete = get_changed_files(repo_path)

    if not to_update and not to_delete:
        typer.echo("[secrin] No supported files changed — nothing to do.")
        return

    typer.echo(
        f"\n[secrin] Post-commit: "
        f"{len(to_update)} updated, {len(to_delete)} deleted"
    )

    # ── 2. Connect to Neo4j ───────────────────────────────────────────────────
    client = NeoClient()
    try:
        client.connect()
    except ConnectionError as exc:
        typer.echo(f"[secrin] Neo4j unavailable — skipping update: {exc}")
        return  # don't raise; hooks must not block commits

    with client:
        count = client.run("MATCH (n) RETURN count(n) AS c")[0]["c"]
        if count == 0:
            typer.echo("[secrin] Neo4j is empty — run `secrin graph build` first.")
            return

        def _cb(step: str, detail: str) -> None:
            typer.echo(f"[secrin]   {detail}")

        # ── 3. Incremental graph update ───────────────────────────────────────
        try:
            result = update_changed_files(
                repo_path=repo_path,
                to_update=to_update,
                to_delete=to_delete,
                client=client,
                settings=settings,
                progress_cb=_cb,
            )
        except Exception as exc:
            typer.echo(f"[secrin] Graph update failed: {exc}")
            return

        affected = result.get("affected_modules", [])
        typer.echo(
            f"[secrin] Graph updated — "
            f"summarized {result['summarized']}, "
            f"embedded {result['embedded']}, "
            f"modules affected: {', '.join(affected) or 'none'}"
        )

        # ── 4. Regenerate wiki pages ──────────────────────────────────────────
        if skip_wiki or not output_dir.exists():
            if not skip_wiki:
                typer.echo(
                    f"[secrin] Wiki dir '{output_dir}' not found — "
                    "run `secrin generate` to create it."
                )
            return

        typer.echo(f"[secrin] Regenerating affected wiki pages → {output_dir}/")

        # Module pages for affected modules
        modules_dir = output_dir / "modules"
        for mn in affected:
            try:
                data    = _fetch_module(client, mn)
                summary = (
                    f"*The `{mn}` module — updated {_GEN_DATE_HOOK}.*"
                )
                md      = _render_module_md(data, summary)
                page    = modules_dir / f"{_slug(mn)}.md"
                if page.parent.exists():
                    page.write_text(md, encoding="utf-8")
                    typer.echo(f"[secrin]   updated: modules/{_slug(mn)}.md")
            except Exception as exc:
                typer.echo(f"[secrin]   [warn] module {mn}: {exc}")

        # architecture.md — regenerate without LLM (fast)
        try:
            all_modules = [
                _fetch_module(client, row["name"])
                for row in client.run(_Q_ALL_MODULES)
            ]
            domains      = client.run(_Q_ALL_DOMAINS)
            import_graph = client.run(_Q_IMPORT_GRAPH)
            overview     = (
                "*(Architecture overview — run `secrin generate` to refresh with LLM.)*"
            )
            arch_md = _render_architecture_md(
                all_modules, domains, import_graph, overview
            )
            (output_dir / "architecture.md").write_text(arch_md, encoding="utf-8")
            typer.echo("[secrin]   updated: architecture.md")

            # README gets a fresh module/domain listing too
            readme_md = _render_readme(all_modules, domains)
            (output_dir / "README.md").write_text(readme_md, encoding="utf-8")
            typer.echo("[secrin]   updated: README.md")
        except Exception as exc:
            typer.echo(f"[secrin]   [warn] architecture.md: {exc}")

    typer.echo("[secrin] Done.\n")


# lazy date so the module can be imported without side effects
def _GEN_DATE_HOOK() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# install-hooks command
# ---------------------------------------------------------------------------

def install_hooks(
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Overwrite existing post-commit hook without asking",
    ),
) -> None:
    """
    Install a git post-commit hook that runs `secrin post-commit` automatically.

    Writes .git/hooks/post-commit and makes it executable.
    Requires `secrin` to be available on PATH when commits are made
    (e.g. activate the project virtualenv or use `poetry shell`).
    """
    # Find .git directory
    git_result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True, text=True,
    )
    if git_result.returncode != 0:
        typer.echo(
            "[error] Not inside a git repository "
            "(or git is not installed).",
            err=True,
        )
        raise typer.Exit(code=1)

    hooks_dir  = Path(git_result.stdout.strip()) / "hooks"
    hook_path  = hooks_dir / "post-commit"
    hooks_dir.mkdir(exist_ok=True)

    # Check for existing hook
    if hook_path.exists() and not force:
        typer.echo(
            f"A post-commit hook already exists at {hook_path}.\n"
            "Use --force to overwrite it."
        )
        raise typer.Exit(code=1)

    # Write the hook script
    hook_path.write_text(_HOOK_SCRIPT, encoding="utf-8")

    # Make it executable (chmod +x)
    current_mode = hook_path.stat().st_mode
    hook_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    typer.echo(f"\nHook installed: {hook_path}")
    typer.echo("\nAfter every `git commit`, Secrin will automatically:")
    typer.echo("  1. Update Neo4j for changed files")
    typer.echo("  2. Re-summarize + re-embed new nodes")
    typer.echo("  3. Regenerate affected wiki pages in docs/wiki/")
    typer.echo(
        "\nNote: `secrin` must be on PATH when committing.\n"
        "Tip:  activate your virtualenv or use `poetry shell` before committing.\n"
        "\nTo uninstall: rm .git/hooks/post-commit\n"
    )
