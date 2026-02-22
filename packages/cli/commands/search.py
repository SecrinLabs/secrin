"""
`secrin search "<query>"` command.

Runs hybrid vector + graph search over the Neo4j knowledge graph
and displays ranked results in a rich table.

Run `secrin graph build --repo <url>` and `secrin analyze` first to
populate Neo4j with nodes and embeddings.
"""
from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from packages.cli.graph.neo4j_client import NeoClient
from packages.cli.search.hybrid import hybrid_search
from packages.config.settings import Settings

console = Console()


def search(
    query: str = typer.Argument(..., help='Natural-language query, e.g. "authentication flow"'),
    top_n: int = typer.Option(5,     "--top",     help="Number of results to return"),
    k: int     = typer.Option(10,    "--k",       help="Vector KNN candidates per label index"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full summaries in table"),
) -> None:
    """
    Hybrid vector + graph search over the code knowledge graph.

    Embeds your query via Ollama, runs KNN across all vector indexes,
    then expands top hits with 1-hop Cypher traversal to surface
    callers, callees, imports, and co-located siblings.

    Run `secrin graph build` and `secrin analyze` first.
    """
    settings = Settings()

    typer.echo(f'\nSearching for: "{query}"')
    typer.echo(f"Connecting to Neo4j at {settings.NEO4J_URI}...")

    client = NeoClient()
    try:
        client.connect()
    except ConnectionError as exc:
        typer.echo(f"[error] {exc}", err=True)
        raise typer.Exit(code=1)

    with client:
        # Guard: embeddings must exist before searching
        count = client.run(
            "MATCH (n) WHERE n.summary_embedding IS NOT NULL RETURN count(n) AS c"
        )[0]["c"]
        if count == 0:
            typer.echo(
                "[error] No embeddings found. Run `secrin analyze` first.",
                err=True,
            )
            raise typer.Exit(code=1)

        typer.echo(f"Running hybrid search over {count:,} embedded nodes...\n")

        try:
            results = hybrid_search(
                query=query,
                client=client,
                settings=settings,
                k=k,
                top_n=top_n,
            )
        except Exception as exc:
            typer.echo(f"[error] Search failed: {exc}", err=True)
            raise typer.Exit(code=1)

    if not results:
        typer.echo("No results found. Try a broader query.")
        return

    # ── Results table ──────────────────────────────────────────────────────────
    table = Table(
        title=f'Results for "{query}"',
        show_header=True,
        header_style="bold cyan",
        show_lines=True,
    )
    table.add_column("#",     style="dim", width=3, justify="right")
    table.add_column("Label", width=10)
    table.add_column("Name",  style="bold")
    table.add_column("Path",  style="dim", no_wrap=False)
    table.add_column("Score", width=7, justify="right")
    table.add_column("Via",   width=12)
    if verbose:
        table.add_column("Summary", no_wrap=False)

    for i, r in enumerate(results, 1):
        score_str = f"{r.score:.3f}"
        via = r.relation if r.relation else r.matched_by
        row: list[str] = [
            str(i),
            r.label,
            r.name or r.id,
            r.path or "",
            score_str,
            via,
        ]
        if verbose:
            row.append(r.summary[:300] if r.summary else "")
        table.add_row(*row)

    console.print(table)

    if not verbose:
        # Show top result summary as a panel
        top = results[0]
        console.print(
            Panel(
                top.summary[:600] if top.summary else "(no summary)",
                title=f"[bold]{top.label}: {top.name or top.id}[/bold]",
                subtitle=top.path or "",
                expand=False,
            )
        )
        typer.echo("\nTip: use --verbose / -v to see summaries for all results.\n")
