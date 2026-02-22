"""
`secrin diff` command.

Dry-run that shows exactly which wiki pages would be created, updated, or
deleted if you ran `secrin generate` right now.  Nothing is written.

Status legend
-------------
  [green]+ NEW[/green]    page does not exist yet — will be created
  [dim]● OK[/dim]     page exists and the module is fully summarized
  [yellow]~ STALE?[/yellow] page exists but module has unsummarized nodes
  [red]✗ REMOVED[/red] page exists in wiki but the module/domain is gone from graph

Run `secrin generate` to apply all pending changes.
"""
from __future__ import annotations

import re
from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.rule import Rule
from rich.table import Table

from packages.cli.core.secrin_yml import load as load_yml
from packages.cli.graph.neo4j_client import NeoClient
from packages.config.settings import Settings

console = Console()

# ---------------------------------------------------------------------------
# Cypher
# ---------------------------------------------------------------------------

_Q_MODULES = "MATCH (m:Module) RETURN m.name AS name ORDER BY m.name"
_Q_DOMAINS = "MATCH (d:DomainEntity) RETURN d.name AS name, d.id AS id ORDER BY d.name"
_Q_UNSUMM  = """
MATCH (m:Module {name: $mn})-[:CONTAINS]->(:File)-[:DEFINES]->(n)
WHERE n.summary IS NULL
RETURN count(n) AS cnt
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "unnamed"


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

def diff(
    output: str = typer.Option(
        "",
        "--output", "-o",
        help="Wiki output directory (overrides .secrin.yml)",
    ),
) -> None:
    """
    Dry run: show which wiki pages would be created, updated, or deleted.

    Compares the current Neo4j graph state against existing files in the
    wiki output directory.  Nothing is written.

    Run `secrin generate` to apply the changes shown here.
    """
    cwd      = Path.cwd()
    yml      = load_yml(cwd)
    settings = Settings()

    wiki_dir_str = output or (yml.wiki_output_dir if yml else "docs/wiki")
    wiki_path    = cwd / wiki_dir_str

    # ── Connect ───────────────────────────────────────────────────────────────
    client = NeoClient()
    try:
        client.connect()
    except ConnectionError as exc:
        console.print(f"[red]✗ Neo4j not reachable:[/red] {exc}")
        console.print("[dim]  → Start Neo4j or check NEO4J_URI in .env[/dim]\n")
        raise typer.Exit(code=1)

    with client:
        total = client.run("MATCH (n) RETURN count(n) AS c")[0]["c"]
        if total == 0:
            console.print(
                "[yellow]Neo4j is empty.[/yellow] "
                "Run [bold]secrin graph build --repo <url>[/bold] first.\n"
            )
            raise typer.Exit(code=1)

        modules = [r["name"] for r in client.run(_Q_MODULES)]
        domains = client.run(_Q_DOMAINS)

        # Unsummarized node counts per module
        unsummarized: dict[str, int] = {}
        for mn in modules:
            rows = client.run(_Q_UNSUMM, mn=mn)
            unsummarized[mn] = rows[0]["cnt"] if rows else 0

    # ── Build the diff table ──────────────────────────────────────────────────
    table = Table(
        title=f"[bold]secrin diff[/bold]  →  {wiki_dir_str}/",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold",
    )
    table.add_column("Status",  width=16)
    table.add_column("Type",    width=10, style="dim")
    table.add_column("Page",    style="bold")
    table.add_column("Notes",   style="dim")

    new_cnt = stale_cnt = ok_cnt = warn_cnt = 0

    modules_dir = wiki_path / "modules"
    domains_dir = wiki_path / "domains"

    # ── Module pages ──────────────────────────────────────────────────────────
    graph_slugs: set[str] = set()
    for mn in modules:
        slug     = _slug(mn)
        graph_slugs.add(slug)
        page     = modules_dir / f"{slug}.md"
        unsumm   = unsummarized.get(mn, 0)

        if not page.exists():
            table.add_row("[green]+ NEW[/green]",    "Module", f"modules/{slug}.md", "will be created")
            new_cnt += 1
        elif unsumm > 0:
            table.add_row(
                "[yellow]~ STALE?[/yellow]", "Module", f"modules/{slug}.md",
                f"{unsumm} node(s) lack summaries",
            )
            warn_cnt += 1
        else:
            table.add_row("[dim]● OK[/dim]",         "Module", f"modules/{slug}.md", "")
            ok_cnt += 1

    # Stale module pages (exist in wiki but not in graph)
    if modules_dir.exists():
        for existing in sorted(modules_dir.glob("*.md")):
            if existing.stem not in graph_slugs:
                table.add_row(
                    "[red]✗ REMOVED[/red]", "Module",
                    f"modules/{existing.stem}.md", "module no longer in graph",
                )
                stale_cnt += 1

    # ── Domain pages ──────────────────────────────────────────────────────────
    domain_slugs: set[str] = set()
    for d in domains:
        slug  = _slug(d["name"])
        domain_slugs.add(slug)
        page  = domains_dir / f"{slug}.md"

        if not page.exists():
            table.add_row("[green]+ NEW[/green]",  "Domain", f"domains/{slug}.md", "will be created")
            new_cnt += 1
        else:
            table.add_row("[dim]● OK[/dim]",       "Domain", f"domains/{slug}.md", "")
            ok_cnt += 1

    if domains_dir.exists():
        for existing in sorted(domains_dir.glob("*.md")):
            if existing.stem not in domain_slugs:
                table.add_row(
                    "[red]✗ REMOVED[/red]", "Domain",
                    f"domains/{existing.stem}.md", "domain no longer in graph",
                )
                stale_cnt += 1

    # ── Index pages ───────────────────────────────────────────────────────────
    for page_name in ("README.md", "architecture.md"):
        page = wiki_path / page_name
        if not page.exists():
            table.add_row("[green]+ NEW[/green]",  "Index", page_name, "will be created")
            new_cnt += 1
        else:
            table.add_row("[dim]● OK[/dim]",       "Index", page_name, "")
            ok_cnt += 1

    # ── Print ─────────────────────────────────────────────────────────────────
    console.print()
    console.print(table)
    console.print()

    if new_cnt == 0 and stale_cnt == 0 and warn_cnt == 0:
        console.print("[green]✓ Wiki is up to date.[/green]\n")
    else:
        parts: list[str] = []
        if new_cnt:   parts.append(f"[green]{new_cnt} new[/green]")
        if warn_cnt:  parts.append(f"[yellow]{warn_cnt} may be stale[/yellow]")
        if stale_cnt: parts.append(f"[red]{stale_cnt} removed[/red]")
        console.print("  " + "  ·  ".join(parts))
        console.print("  Run [bold]secrin generate[/bold] to apply changes.\n")
