"""
`secrin graph build --repo <url-or-path>` command.

Accepts either:
  - A GitHub / remote URL  → cloned to /tmp (same as `secrin init`)
  - A local directory path → used directly

Neo4j connection is configured via the project .env file (NEO4J_URI,
NEO4J_USER, NEO4J_PASS) — managed by packages.config.settings.Settings.
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from packages.cli.core import cloner
from packages.cli.graph.neo4j_client import NeoClient
from packages.cli.graph.schema import init_schema
from packages.cli.graph.builder import build_graph
from packages.config.settings import Settings

graph_app = typer.Typer(
    name="graph",
    help="Build and query the Neo4j code knowledge graph.",
    add_completion=False,
)

console = Console()

_URL_PREFIXES = ("https://", "http://", "git@", "ssh://")


def _is_remote(repo: str) -> bool:
    return any(repo.startswith(p) for p in _URL_PREFIXES)


@graph_app.command("build")
def build(
    repo: str = typer.Option(
        ...,
        "--repo",
        help="GitHub URL (cloned automatically) or local path to an existing checkout",
    ),
) -> None:
    """Parse a repo and insert it into Neo4j as a code knowledge graph."""
    # ── Resolve repo path ─────────────────────────────────────────────────
    if _is_remote(repo):
        typer.echo(f"\nCloning repo...")
        try:
            repo_path = cloner.clone(repo)
        except ValueError as exc:
            typer.echo(f"[error] {exc}", err=True)
            raise typer.Exit(code=1)
        typer.echo(f"  Cloned to {repo_path}\n")
    else:
        repo_path = Path(repo).resolve()
        if not repo_path.is_dir():
            typer.echo(
                f"[error] Path does not exist or is not a directory: {repo_path}",
                err=True,
            )
            raise typer.Exit(code=1)

    # ── Connect to Neo4j (settings come from .env via Settings) ──────────
    settings = Settings()
    typer.echo(f"Connecting to Neo4j at {settings.NEO4J_URI}...")

    client = NeoClient()
    try:
        client.connect()
    except ConnectionError as exc:
        typer.echo(f"[error] {exc}", err=True)
        raise typer.Exit(code=1)

    with client:
        typer.echo("Initialising schema (constraints + indexes)...")
        init_schema(client)

        typer.echo(f"\nBuilding graph from: {repo_path}\n")
        summary = build_graph(repo_path, client)

    # ── Summary tables ────────────────────────────────────────────────────
    typer.echo("")

    node_table = Table(title="Nodes", show_header=True, header_style="bold cyan")
    node_table.add_column("Label", style="cyan")
    node_table.add_column("Count", justify="right")
    total_nodes = 0
    for label, cnt in sorted(summary["nodes"].items()):
        node_table.add_row(label, str(cnt))
        total_nodes += cnt
    node_table.add_row("[bold]TOTAL[/bold]", f"[bold]{total_nodes}[/bold]")
    console.print(node_table)

    typer.echo("")

    rel_table = Table(title="Relationships", show_header=True, header_style="bold magenta")
    rel_table.add_column("Type", style="magenta")
    rel_table.add_column("Count", justify="right")
    total_rels = 0
    for rel_type, cnt in sorted(summary["relationships"].items()):
        rel_table.add_row(rel_type, str(cnt))
        total_rels += cnt
    rel_table.add_row("[bold]TOTAL[/bold]", f"[bold]{total_rels}[/bold]")
    console.print(rel_table)

    typer.echo("")
    console.print(
        "[green]✓ Graph ready.[/green]  "
        "Run [bold]secrin analyze[/bold] to generate summaries and embeddings."
    )
    typer.echo("")


@graph_app.command("visualize")
def visualize() -> None:
    """
    Open Neo4j Browser pointed at the Secrin database.

    For local Neo4j: opens http://localhost:7474/browser/
    For AuraDB (neo4j+s:// URI): opens https://console.neo4j.io/
    """
    import webbrowser

    settings = Settings()
    uri      = settings.NEO4J_URI

    console.print()
    if uri.startswith("neo4j+s://") or uri.startswith("neo4j+scc://"):
        url = "https://console.neo4j.io/"
        console.print(f"[green]Opening AuraDB Console[/green]: {url}")
        console.print(f"  Connect URI: [bold]{uri}[/bold]")
    else:
        url = "http://localhost:7474/browser/"
        console.print(f"[green]Opening Neo4j Browser[/green]: {url}")
        console.print(f"  Connect URI: [bold]{uri}[/bold]")
        console.print(
            f"  Username:    [bold]{settings.NEO4J_USER}[/bold]  "
            f"[dim](password from NEO4J_PASS in .env)[/dim]"
        )

    webbrowser.open(url)

    console.print()
    console.print("[dim]Useful Cypher queries:[/dim]")
    console.print("  MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100")
    console.print("  MATCH (m:Module) RETURN m.name, count{ (m)-[:CONTAINS]->() } AS files")
    console.print("  MATCH (d:DomainEntity) RETURN d.name, d.subdomain ORDER BY d.subdomain")
    console.print()
