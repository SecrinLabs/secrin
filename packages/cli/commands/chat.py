"""
`secrin chat "<question>"` command.

Interactive architecture Q&A powered by hybrid vector + graph search.
Finds the most relevant code nodes from Neo4j, formats them as context,
and passes them to the configured LLM for a precise, sourced answer.

Ideal for questions like:
  "How does authentication work?"
  "Where is the rate limiting implemented?"
  "What calls the payment processing service?"
  "How do I add a new API endpoint?"

Prerequisites: `secrin graph build` + `secrin analyze`
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from packages.cli.agents.llm_client import client_from_settings, client_from_yml
from packages.cli.core.secrin_yml import load as load_yml
from packages.cli.graph.neo4j_client import NeoClient
from packages.cli.search.hybrid import hybrid_search
from packages.config.settings import Settings

console = Console()

# ---------------------------------------------------------------------------
# System prompt — anti-hallucination, source-grounded
# ---------------------------------------------------------------------------

_SYSTEM = """\
You are a senior software architect assistant.

Answer the user's question using ONLY the context below (extracted from a \
real code knowledge graph). If the answer is not present in the context, \
say "I don't have enough context to answer that" — do not invent information.

Rules:
- Be concise and precise.
- Use bullet points for multi-part answers.
- Reference specific class or function names from the context when relevant.
- If you quote code, use short inline snippets rather than large blocks.
"""

_CONTEXT_HEADER = "=== CONTEXT FROM CODE KNOWLEDGE GRAPH ==="
_CONTEXT_FOOTER = "=== END OF CONTEXT ==="


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

def chat(
    question: str = typer.Argument(
        ..., help='Architecture question, e.g. "how does authentication work?"'
    ),
    top_n: int = typer.Option(8,  "--top", "-n", help="Context nodes to retrieve"),
    k: int     = typer.Option(15, "--k",         help="Vector KNN candidates per label index"),
) -> None:
    """
    Ask an architecture question answered from the code knowledge graph.

    Runs hybrid search (vector KNN + graph traversal) to find relevant
    code nodes, then passes them as context to the LLM for a sourced answer.

    Prerequisites:
        secrin graph build --repo <url>
        secrin analyze
    """
    cwd      = Path.cwd()
    settings = Settings()
    yml      = load_yml(cwd)

    provider_name = (yml.provider if yml else settings.LLM_PROVIDER).capitalize()

    # ── Connect ───────────────────────────────────────────────────────────────
    client = NeoClient()
    try:
        client.connect()
    except ConnectionError as exc:
        console.print(f"[red]✗ Neo4j not reachable:[/red] {exc}")
        console.print("[dim]  → Start Neo4j or check NEO4J_URI in .env[/dim]\n")
        raise typer.Exit(code=1)

    with client:
        emb_count = client.run(
            "MATCH (n) WHERE n.summary_embedding IS NOT NULL RETURN count(n) AS c"
        )[0]["c"]
        if emb_count == 0:
            console.print(
                "[yellow]No embeddings found.[/yellow] "
                "Run [bold]secrin analyze[/bold] first.\n"
            )
            raise typer.Exit(code=1)

        # ── Step 1: Hybrid search ─────────────────────────────────────────────
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(
                f"Searching {emb_count:,} embedded nodes...", total=None
            )
            try:
                results = hybrid_search(
                    query=question,
                    client=client,
                    settings=settings,
                    k=k,
                    top_n=top_n,
                )
            except Exception as exc:
                console.print(f"[red]Search failed:[/red] {exc}\n")
                raise typer.Exit(code=1)

    if not results:
        console.print(
            "[yellow]No relevant context found.[/yellow] "
            "Try rephrasing your question.\n"
        )
        return

    # ── Step 2: Build context block ───────────────────────────────────────────
    ctx_parts: list[str] = []
    for i, r in enumerate(results, 1):
        ctx_parts.append(
            f"[{i}] {r.label}: {r.name}  ({r.path})\n"
            f"     {(r.summary or '(no summary)').replace(chr(10), ' ')}"
        )
    context = "\n\n".join(ctx_parts)

    # ── Step 3: Ask LLM ───────────────────────────────────────────────────────
    prompt = (
        f"{_SYSTEM}\n\n"
        f"{_CONTEXT_HEADER}\n{context}\n{_CONTEXT_FOOTER}\n\n"
        f"Question: {question}"
    )

    llm = client_from_yml(yml) if yml else client_from_settings(settings)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(f"Asking {provider_name}...", total=None)
        try:
            answer = llm.complete(prompt, max_tokens=1500, temperature=0.2)
        except Exception as exc:
            console.print(f"[red]{provider_name} error:[/red] {exc}")
            console.print(
                f"[dim]  → Check that {provider_name} is running and the API key is set[/dim]\n"
            )
            raise typer.Exit(code=1)

    # ── Step 4: Render ────────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        Markdown(answer),
        title="[bold cyan]secrin chat[/bold cyan]",
        subtitle=(
            f"[dim]{question[:70]}{'…' if len(question) > 70 else ''}[/dim]"
        ),
        expand=False,
        padding=(1, 2),
    ))

    # Sources footer
    label_counts: dict[str, int] = {}
    for r in results:
        label_counts[r.label] = label_counts.get(r.label, 0) + 1
    breakdown = "  ·  ".join(f"{v} {k}{'s' if v > 1 else ''}" for k, v in label_counts.items())

    console.print(f"\n[dim]Sources — {len(results)} nodes ({breakdown})[/dim]")
    for r in results[:6]:
        via = f"  [dim]via {r.relation}[/dim]" if r.relation else ""
        console.print(
            f"  [dim]•[/dim] [bold]{r.label}[/bold]: {r.name}  "
            f"[dim]({r.path})[/dim]{via}"
        )
    if len(results) > 6:
        console.print(f"  [dim]… and {len(results) - 6} more[/dim]")
    console.print()
