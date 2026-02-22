"""
`secrin analyze` command.

Reads Function, Class, and File nodes already loaded into Neo4j by
`secrin graph build`, generates plain-English summaries via the configured
LLM, then generates and stores vector embeddings via Ollama.

LLM + embedding config comes from the project .env (via Settings):
    LLM_PROVIDER            ollama | anthropic | gemini
    LLM_MODEL_OLLAMA        model name for Ollama inference
    ANTHROPIC_API_KEY       required if LLM_PROVIDER=anthropic
    GEMINI_API_KEY          required if LLM_PROVIDER=gemini
    OLLAMA_BASE_URL         Ollama host
    OLLAMA_EMBEDDING_MODEL  model for embeddings
    EMBEDDING_DIMENSION     must match the embedding model (e.g. 768 or 1024)
"""
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from packages.cli.graph.neo4j_client import NeoClient
from packages.cli.agents.summarizer import run_summarizer
from packages.cli.agents.embedder import run_embedder
from packages.config.settings import Settings

analyze_app = typer.Typer(
    name="analyze",
    help="Summarize graph nodes with LLM and store vector embeddings.",
    add_completion=False,
    invoke_without_command=True,
)

console = Console()


@analyze_app.callback(invoke_without_command=True)
def analyze(
    skip_embed: bool = typer.Option(
        False,
        "--skip-embed",
        help="Generate summaries only; skip embedding step",
    ),
    batch_size: int = typer.Option(
        50,
        "--batch-size",
        help="Nodes processed per round-trip to Neo4j",
    ),
) -> None:
    """
    Summarize all unsummarized nodes in Neo4j, then embed the summaries.

    Run `secrin graph build --repo <url>` first to populate Neo4j.
    """
    settings = Settings()

    # ── Connect to Neo4j ──────────────────────────────────────────────────
    typer.echo(f"\nConnecting to Neo4j at {settings.NEO4J_URI}...")
    client = NeoClient()
    try:
        client.connect()
    except ConnectionError as exc:
        typer.echo(f"[error] {exc}", err=True)
        raise typer.Exit(code=1)

    with client:
        # ── Sanity check: any nodes at all? ───────────────────────────────
        total = client.run("MATCH (n) RETURN count(n) AS c")[0]["c"]
        if total == 0:
            typer.echo(
                "[error] Neo4j is empty. Run `secrin graph build --repo <url>` first.",
                err=True,
            )
            raise typer.Exit(code=1)

        # ── Phase 1: Summarize ─────────────────────────────────────────────
        typer.echo(
            f"\nPhase 1 — Summarizing nodes "
            f"(provider: {settings.LLM_PROVIDER}, "
            f"model: {settings.LLM_MODEL_OLLAMA if settings.LLM_PROVIDER == 'ollama' else 'default'})..."
        )

        _label_counts: dict[str, int] = {}

        def _sum_progress(label: str, done: int) -> None:
            _label_counts[label] = done
            typer.echo(f"  [{label}] summarized {done}", nl=False)
            typer.echo("\r", nl=False)

        try:
            sum_counts = run_summarizer(
                client=client,
                settings=settings,
                batch_size=batch_size,
                progress_cb=_sum_progress,
            )
        except ValueError as exc:
            typer.echo(f"[error] {exc}", err=True)
            raise typer.Exit(code=1)
        except Exception as exc:
            typer.echo(f"[error] Summarization failed: {exc}", err=True)
            raise typer.Exit(code=1)

        typer.echo("")  # clear \r line

        # ── Phase 2: Embed ─────────────────────────────────────────────────
        embed_counts: dict[str, int] = {}
        if not skip_embed:
            typer.echo(
                f"\nPhase 2 — Embedding summaries "
                f"(model: {settings.OLLAMA_EMBEDDING_MODEL}, "
                f"dims: {settings.EMBEDDING_DIMENSION})..."
            )

            def _emb_progress(label: str, done: int) -> None:
                typer.echo(f"  [{label}] embedded {done}", nl=False)
                typer.echo("\r", nl=False)

            try:
                embed_counts = run_embedder(
                    client=client,
                    settings=settings,
                    batch_size=batch_size,
                    progress_cb=_emb_progress,
                )
            except Exception as exc:
                typer.echo(f"\n[warn] Embedding failed: {exc}", err=True)
                typer.echo("Summaries were saved. Re-run without --skip-embed once Ollama is running.")

            typer.echo("")  # clear \r line

        # ── Verify ────────────────────────────────────────────────────────
        verified = client.run(
            "MATCH (n) WHERE n.summary IS NOT NULL RETURN count(n) AS c"
        )[0]["c"]

    # ── Summary table ──────────────────────────────────────────────────────
    typer.echo("")

    table = Table(title="Analysis Results", show_header=True, header_style="bold green")
    table.add_column("Label",     style="green")
    table.add_column("Summarized", justify="right")
    table.add_column("Embedded",  justify="right")

    for label in ("Function", "Class", "File"):
        table.add_row(
            label,
            str(sum_counts.get(label, 0)),
            str(embed_counts.get(label, 0)) if not skip_embed else "skipped",
        )

    console.print(table)
    typer.echo(f"\nTotal nodes with summary: {verified}")
    typer.echo("Verify in Neo4j Browser: MATCH (n) WHERE n.summary IS NOT NULL RETURN count(n)")
