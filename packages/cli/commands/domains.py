"""
`secrin domains` command.

Extracts business domain entities from Neo4j node summaries using
the configured LLM, then writes DomainEntity nodes + IMPLEMENTS_DOMAIN
edges into Neo4j.

Run `secrin graph build --repo <url>` and `secrin analyze` first.
"""
from __future__ import annotations

import typer
from rich.console import Console
from rich.tree import Tree

from packages.cli.graph.neo4j_client import NeoClient
from packages.cli.agents.domain_extractor import run_domain_extractor
from packages.config.settings import Settings

domains_app = typer.Typer(
    name="domains",
    help="Extract business domain entities and link them to code nodes.",
    add_completion=False,
    invoke_without_command=True,
)

console = Console()


@domains_app.callback(invoke_without_command=True)
def domains(
    sample: int = typer.Option(
        200,
        "--sample",
        help="Max nodes to sample for domain extraction",
    ),
    batch_size: int = typer.Option(
        60,
        "--batch-size",
        help="Nodes per LLM call",
    ),
) -> None:
    """
    Extract business domain concepts from Neo4j summaries.

    Sends batches of code summaries to the LLM, which identifies distinct
    business capabilities (Authentication, Billing, etc.), then writes
    DomainEntity nodes + IMPLEMENTS_DOMAIN edges to Neo4j.

    Run `secrin graph build` and `secrin analyze` first.
    """
    settings = Settings()

    typer.echo(f"\nConnecting to Neo4j at {settings.NEO4J_URI}...")
    client = NeoClient()
    try:
        client.connect()
    except ConnectionError as exc:
        typer.echo(f"[error] {exc}", err=True)
        raise typer.Exit(code=1)

    with client:
        count = client.run(
            "MATCH (n) WHERE n.summary IS NOT NULL RETURN count(n) AS c"
        )[0]["c"]
        if count == 0:
            typer.echo(
                "[error] No summaries found. Run `secrin analyze` first.",
                err=True,
            )
            raise typer.Exit(code=1)

        typer.echo(
            f"\nExtracting domains from up to {min(sample, count):,} node summaries "
            f"(provider: {settings.LLM_PROVIDER})..."
        )

        def _progress(step: str, detail: str) -> None:
            prefix = "  [warn]" if step == "warn" else "  "
            typer.echo(f"{prefix} {detail}")

        try:
            result = run_domain_extractor(
                client=client,
                settings=settings,
                sample_limit=sample,
                batch_size=batch_size,
                progress_cb=_progress,
            )
        except ValueError as exc:
            typer.echo(f"\n[error] {exc}", err=True)
            raise typer.Exit(code=1)
        except Exception as exc:
            typer.echo(f"\n[error] Domain extraction failed: {exc}", err=True)
            raise typer.Exit(code=1)

    # ── Domain map display ────────────────────────────────────────────────────
    typer.echo("")

    domain_list: list[dict] = result.get("domain_list", [])
    domain_list.sort(key=lambda d: (d.get("subdomain", ""), d.get("name", "")))

    tree = Tree("[bold cyan]Domain Map[/bold cyan]")

    for d in domain_list:
        header = (
            f"[bold]{d['name']}[/bold]  "
            f"[dim]({d.get('subdomain', '?')})[/dim]"
        )
        if d.get("description"):
            header += f"\n  [italic dim]{d['description']}[/italic dim]"

        branch = tree.add(header)
        impls = d.get("implements", [])
        for impl in impls[:10]:
            branch.add(f"[green]→[/green] {impl}")
        if len(impls) > 10:
            branch.add(f"[dim]... and {len(impls) - 10} more[/dim]")

    console.print(tree)

    typer.echo(f"\nTotal domain entities : {result['domains']}")
    typer.echo(f"Total IMPLEMENTS_DOMAIN edges : {result['edges']}")
    typer.echo(
        "\nVerify in Neo4j Browser:\n"
        "  MATCH (n)-[:IMPLEMENTS_DOMAIN]->(d:DomainEntity) RETURN n, d"
    )
