"""
`secrin analyze` command.

Reads Function, Class, and File nodes already loaded into Neo4j by
`secrin graph build`, generates plain-English summaries via the configured
LLM, then generates and stores vector embeddings.

LLM + embedding config comes from .env (via Settings):
    LLM_PROVIDER             ollama | openai | anthropic
    LLM_MODEL_OLLAMA         Ollama completion model
    LLM_MODEL_OPENAI         OpenAI completion model
    LLM_MODEL_ANTHROPIC      Anthropic completion model
    ANTHROPIC_API_KEY        required when LLM_PROVIDER=anthropic
    OPENAI_API_KEY           required when LLM_PROVIDER=openai
    OLLAMA_BASE_URL          Ollama host
    OLLAMA_EMBEDDING_MODEL   Embedding model (ollama + anthropic)
    OPENAI_EMBEDDING_MODEL   Embedding model (openai)
    EMBEDDING_DIMENSION      Must match the embedding model (e.g. 768 or 1024)
"""
from __future__ import annotations

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
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

    Phase 1  — LLM generates a plain-English summary for every Function,
               Class, and File node that lacks one.
    Phase 2  — Embeds each summary into a float vector and stores it back
               in Neo4j (used by `secrin search` and `secrin chat`).

    Run `secrin graph build --repo <url>` first to populate Neo4j.
    """
    settings = Settings()

    # ── Resolve model name for display ───────────────────────────────────────
    provider = settings.LLM_PROVIDER.lower()
    if provider == "openai":
        model_name = settings.LLM_MODEL_OPENAI
    elif provider == "anthropic":
        model_name = settings.LLM_MODEL_ANTHROPIC
    else:
        model_name = settings.LLM_MODEL_OLLAMA

    # ── Connect to Neo4j ──────────────────────────────────────────────────────
    console.print(f"\nConnecting to Neo4j at [bold]{settings.NEO4J_URI}[/bold]...")
    client = NeoClient()
    try:
        client.connect()
    except ConnectionError as exc:
        console.print(f"[red]✗ Neo4j not reachable:[/red] {exc}")
        console.print("[dim]  → Start Neo4j or check NEO4J_URI in .env[/dim]\n")
        raise typer.Exit(code=1)

    with client:
        # ── Sanity check ─────────────────────────────────────────────────────
        total = client.run("MATCH (n) RETURN count(n) AS c")[0]["c"]
        if total == 0:
            console.print(
                "[yellow]Neo4j is empty.[/yellow] "
                "Run [bold]secrin graph build --repo <url>[/bold] first.\n"
            )
            raise typer.Exit(code=1)

        unsumm = client.run(
            "MATCH (n) WHERE labels(n)[0] IN ['Function','Class','File'] "
            "AND n.summary IS NULL RETURN count(n) AS c"
        )[0]["c"]
        console.print(
            f"  [green]✓[/green] Connected  "
            f"([bold]{total:,}[/bold] nodes, "
            f"[bold]{unsumm:,}[/bold] pending summarization)\n"
        )

        # ── Phase 1: Summarize ────────────────────────────────────────────────
        sum_counts: dict[str, int] = {}
        _running: dict[str, int]   = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=False,
        ) as progress:
            task = progress.add_task(
                f"[Phase 1] Summarizing  "
                f"[dim]{provider} / {model_name}[/dim]  …",
                total=None,
            )

            def _sum_cb(label: str, done: int) -> None:
                _running[label] = done
                counts_str = "  ".join(
                    f"{lbl} {n}" for lbl, n in sorted(_running.items())
                )
                progress.update(
                    task,
                    description=(
                        f"[Phase 1] Summarizing  "
                        f"[dim]{provider} / {model_name}[/dim]  "
                        f"[bold]{counts_str}[/bold]"
                    ),
                )

            try:
                sum_counts = run_summarizer(
                    client=client,
                    settings=settings,
                    batch_size=batch_size,
                    progress_cb=_sum_cb,
                )
            except ValueError as exc:
                console.print(f"[red]✗ Config error:[/red] {exc}\n")
                raise typer.Exit(code=1)
            except Exception as exc:
                console.print(f"[red]✗ Summarization failed:[/red] {exc}\n")
                console.print(
                    f"[dim]  → Is {provider} running?  "
                    f"Check {'OLLAMA_BASE_URL' if provider == 'ollama' else provider.upper() + '_API_KEY'} in .env[/dim]\n"
                )
                raise typer.Exit(code=1)

            total_sum = sum(sum_counts.values())
            progress.update(
                task,
                description=(
                    f"[Phase 1] [green]Done[/green]  "
                    f"[dim]{provider} / {model_name}[/dim]  "
                    f"— [bold]{total_sum}[/bold] nodes summarized"
                ),
                total=1, completed=1,
            )

        # ── Phase 2: Embed ─────────────────────────────────────────────────────
        embed_counts: dict[str, int] = {}
        if not skip_embed:
            _emb_running: dict[str, int] = {}

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=False,
            ) as progress:
                embed_model = (
                    settings.OPENAI_EMBEDDING_MODEL
                    if provider == "openai"
                    else settings.OLLAMA_EMBEDDING_MODEL
                )
                task = progress.add_task(
                    f"[Phase 2] Embedding   "
                    f"[dim]{embed_model}  {settings.EMBEDDING_DIMENSION}d[/dim]  …",
                    total=None,
                )

                def _emb_cb(label: str, done: int) -> None:
                    _emb_running[label] = done
                    counts_str = "  ".join(
                        f"{lbl} {n}" for lbl, n in sorted(_emb_running.items())
                    )
                    progress.update(
                        task,
                        description=(
                            f"[Phase 2] Embedding   "
                            f"[dim]{embed_model}[/dim]  "
                            f"[bold]{counts_str}[/bold]"
                        ),
                    )

                try:
                    embed_counts = run_embedder(
                        client=client,
                        settings=settings,
                        batch_size=batch_size,
                        progress_cb=_emb_cb,
                    )
                except Exception as exc:
                    console.print(f"\n[yellow]⚠ Embedding failed:[/yellow] {exc}")
                    console.print(
                        "[dim]  Summaries were saved.  "
                        "Re-run without --skip-embed once the embed service is running.[/dim]\n"
                    )

                total_emb = sum(embed_counts.values())
                progress.update(
                    task,
                    description=(
                        f"[Phase 2] [green]Done[/green]  "
                        f"[dim]{embed_model}[/dim]  "
                        f"— [bold]{total_emb}[/bold] nodes embedded"
                    ),
                    total=1, completed=1,
                )

        # ── Verification count ─────────────────────────────────────────────────
        verified = client.run(
            "MATCH (n) WHERE n.summary IS NOT NULL RETURN count(n) AS c"
        )[0]["c"]

    # ── Summary table ──────────────────────────────────────────────────────────
    console.print()
    table = Table(
        title="Analysis Results",
        show_header=True,
        header_style="bold green",
    )
    table.add_column("Label",      style="green")
    table.add_column("Summarized", justify="right")
    table.add_column("Embedded",   justify="right")

    for label in ("Function", "Class", "File"):
        table.add_row(
            label,
            str(sum_counts.get(label, 0)),
            str(embed_counts.get(label, 0)) if not skip_embed else "[dim]skipped[/dim]",
        )

    console.print(table)
    console.print(f"\n[green]✓[/green] Total nodes with summary: [bold]{verified:,}[/bold]")
    if not skip_embed:
        console.print("  Run [bold]secrin search \"<query>\"[/bold] or [bold]secrin chat \"<question>\"[/bold] to query the graph.")
    else:
        console.print("  Run [bold]secrin analyze[/bold] (without --skip-embed) to generate embeddings.")
    console.print()
