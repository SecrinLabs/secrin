"""
`secrin generate` command.

Reads the Neo4j knowledge graph and generates a structured Markdown wiki.

Default output: docs/wiki/
Override with: --output <path>

Prerequisite pipeline:
    secrin graph build --repo <url>   # build graph
    secrin analyze                    # summarize + embed nodes
    secrin domains                    # extract domain entities  (optional)
    secrin generate                   # ← this command
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from packages.cli.graph.neo4j_client import NeoClient
from packages.cli.agents.wiki_writer import run_wiki_writer
from packages.config.settings import Settings

console = Console()


def generate(
    output: str = typer.Option(
        "docs/wiki",
        "--output", "-o",
        help="Directory to write wiki files into",
    ),
    skip_llm: bool = typer.Option(
        False,
        "--skip-llm",
        help="Skip LLM narrative summaries (faster; uses raw node summaries only)",
    ),
) -> None:
    """
    Generate a Markdown wiki from the Neo4j knowledge graph.

    Produces:
      <output>/README.md          — Auto-linked index
      <output>/architecture.md   — System overview + Mermaid diagrams
      <output>/modules/*.md      — One page per module
      <output>/domains/*.md      — One page per domain entity

    Run `secrin graph build`, `secrin analyze`, and optionally
    `secrin domains` before running this command.
    """
    settings = Settings()
    output_dir = Path(output)

    typer.echo(f"\nConnecting to Neo4j at {settings.NEO4J_URI}...")
    client = NeoClient()
    try:
        client.connect()
    except ConnectionError as exc:
        typer.echo(f"[error] {exc}", err=True)
        raise typer.Exit(code=1)

    with client:
        count = client.run("MATCH (n) RETURN count(n) AS c")[0]["c"]
        if count == 0:
            typer.echo(
                "[error] Neo4j is empty. Run `secrin graph build --repo <url>` first.",
                err=True,
            )
            raise typer.Exit(code=1)

        llm_note = "without LLM" if skip_llm else f"with LLM ({settings.LLM_PROVIDER})"
        typer.echo(
            f"\nGenerating wiki → {output_dir}/ [{llm_note}]\n"
        )

        def _progress(step: str, detail: str) -> None:
            if step == "warn":
                typer.echo(f"  [warn] {detail}")
            elif step in ("module", "fetch", "done"):
                typer.echo(f"  {detail}")

        try:
            result = run_wiki_writer(
                client=client,
                settings=settings,
                output_dir=output_dir,
                skip_llm=skip_llm,
                progress_cb=_progress,
            )
        except ValueError as exc:
            typer.echo(f"\n[error] {exc}", err=True)
            raise typer.Exit(code=1)
        except Exception as exc:
            typer.echo(f"\n[error] Wiki generation failed: {exc}", err=True)
            raise typer.Exit(code=1)

    # ── Summary table ──────────────────────────────────────────────────────────
    typer.echo("")
    table = Table(title="Wiki Generated", show_header=True, header_style="bold green")
    table.add_column("Type",         style="green")
    table.add_column("Count",        justify="right")
    table.add_column("Location",     style="dim")

    table.add_row("Module pages",  str(result["modules"]), f"{output_dir}/modules/")
    table.add_row("Domain pages",  str(result["domains"]), f"{output_dir}/domains/")
    table.add_row("Architecture",  "1",                    f"{output_dir}/architecture.md")
    table.add_row("Index",         "1",                    f"{output_dir}/README.md")
    table.add_row("Total files",   str(result["files_written"]), "")

    console.print(table)
    typer.echo(f"\nWiki written to: {result['output_dir']}")
    typer.echo(
        "\nNext: open docs/wiki/README.md or run a local markdown server.\n"
        "Tip: use --skip-llm for a faster pass without narrative summaries.\n"
    )
