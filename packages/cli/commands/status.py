"""
`secrin status` command.

Shows a live dashboard of the current Secrin state:
  - Neo4j graph node / edge counts
  - Coverage (% nodes summarized / embedded)
  - Last analysis timestamp + git commit
  - Wiki page count
  - .secrin.yml presence

Example output
--------------
Secrin v2  my-startup/backend
──────────────────────────────────────────────────────────────
Graph          847 nodes · 2,341 edges
               Files 124  ·  Functions 612  ·  Classes 111  ·  Modules 4
Domains        8 domain entities identified
Coverage       98% summarized  ·  96% embedded
Last analyzed  2 hours ago  (main @ a3f9c12)
Neo4j          ● connected  bolt://localhost:7687
Wiki           docs/wiki/  ·  47 pages
.secrin.yml    ✓  ollama / qwen2.5-coder:0.5b
──────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from packages.cli.core.secrin_yml import load as load_yml
from packages.cli.graph.neo4j_client import NeoClient
from packages.config.settings import Settings

console = Console()

# ---------------------------------------------------------------------------
# Cypher queries
# ---------------------------------------------------------------------------

_Q_NODES  = "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY cnt DESC"
_Q_EDGES  = "MATCH ()-[r]->() RETURN count(*) AS cnt"
_Q_COVER  = """
MATCH (n) WHERE labels(n)[0] IN ['Function', 'Class', 'File']
WITH count(*) AS total,
     sum(CASE WHEN n.summary IS NOT NULL THEN 1 ELSE 0 END) AS summarized,
     sum(CASE WHEN n.summary_embedding IS NOT NULL THEN 1 ELSE 0 END) AS embedded
RETURN total, summarized, embedded
"""
_Q_LAST   = "MATCH (n) WHERE n.summarized_at IS NOT NULL RETURN max(n.summarized_at) AS ts"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _time_ago(iso_ts: str) -> str:
    """Convert an ISO-8601 timestamp to a human-readable 'X ago' string."""
    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - ts
        secs  = int(delta.total_seconds())
        if secs < 60:
            return f"{secs}s ago"
        if secs < 3600:
            return f"{secs // 60}m ago"
        if secs < 86400:
            return f"{secs // 3600}h ago"
        return f"{secs // 86400}d ago"
    except Exception:
        return iso_ts[:19]  # fallback: raw timestamp


def _git_info(cwd: Path) -> str:
    """Return 'branch @ short-hash' from the current repo, or ''."""
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd, capture_output=True, text=True,
        ).stdout.strip()
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd, capture_output=True, text=True,
        ).stdout.strip()
        if branch and sha:
            return f"({branch} @ {sha})"
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

def status() -> None:
    """
    Show a live dashboard: graph stats, coverage, last analysis, and wiki state.

    Connects to Neo4j using settings from .env / environment.
    Reads .secrin.yml for wiki location and LLM config.
    """
    cwd      = Path.cwd()
    settings = Settings()
    yml      = load_yml(cwd)

    console.print()
    console.print(
        f"[bold green]Secrin[/bold green]  [dim]v2[/dim]  "
        f"[bold]{cwd.name}[/bold]"
    )
    console.print(Rule(style="dim"))

    # ── Try to connect to Neo4j ───────────────────────────────────────────────
    client    = NeoClient()
    neo4j_uri = settings.NEO4J_URI
    connected = False

    nodes_by_label: dict[str, int] = {}
    total_nodes = total_edges = 0
    total_code  = summarized = embedded = 0
    coverage_pct = embed_pct = 0
    last_ts: str | None = None

    try:
        client.connect()
        connected = True

        with client:
            for row in client.run(_Q_NODES):
                if row["label"]:
                    nodes_by_label[row["label"]] = row["cnt"]
            total_nodes = sum(nodes_by_label.values())
            total_edges = client.run(_Q_EDGES)[0]["cnt"]

            cov = client.run(_Q_COVER)
            if cov and cov[0]["total"]:
                total_code   = cov[0]["total"]
                summarized   = cov[0]["summarized"]
                embedded     = cov[0]["embedded"]
                coverage_pct = int(summarized / total_code * 100)
                embed_pct    = int(embedded   / total_code * 100)

            ts_row = client.run(_Q_LAST)
            if ts_row and ts_row[0]["ts"]:
                last_ts = ts_row[0]["ts"]

    except ConnectionError as exc:
        console.print(
            f"  [red]✗[/red] Neo4j not reachable  [dim]{neo4j_uri}[/dim]\n"
            f"  [dim]→ {exc}[/dim]\n"
            f"  [dim]→ Start Neo4j, or set NEO4J_URI in .env[/dim]"
        )
        console.print(Rule(style="dim"))
        console.print()
        raise typer.Exit(code=1)

    # ── Build display table ───────────────────────────────────────────────────
    table = Table(box=None, show_header=False, padding=(0, 2), show_edge=False)
    table.add_column("key",   style="bold", min_width=16)
    table.add_column("value")

    # Graph
    fn_cnt  = nodes_by_label.get("Function",    0)
    cls_cnt = nodes_by_label.get("Class",        0)
    file_cnt= nodes_by_label.get("File",         0)
    mod_cnt = nodes_by_label.get("Module",       0)
    dom_cnt = nodes_by_label.get("DomainEntity", 0)

    table.add_row(
        "Graph",
        f"[bold]{total_nodes:,}[/bold] nodes · [bold]{total_edges:,}[/bold] edges",
    )
    table.add_row(
        "",
        f"Files [bold]{file_cnt}[/bold]  ·  "
        f"Functions [bold]{fn_cnt}[/bold]  ·  "
        f"Classes [bold]{cls_cnt}[/bold]  ·  "
        f"Modules [bold]{mod_cnt}[/bold]",
    )

    if dom_cnt:
        table.add_row(
            "Domains",
            f"[bold]{dom_cnt}[/bold] domain entities identified",
        )

    # Coverage
    if total_code > 0:
        cov_color = "green" if coverage_pct >= 90 else "yellow" if coverage_pct >= 50 else "red"
        emb_color = "green" if embed_pct   >= 90 else "yellow" if embed_pct   >= 50 else "red"
        table.add_row(
            "Coverage",
            f"[{cov_color}]{coverage_pct}%[/{cov_color}] summarized  ·  "
            f"[{emb_color}]{embed_pct}%[/{emb_color}] embedded",
        )
    else:
        table.add_row("Coverage", "[dim]run `secrin analyze` to generate summaries[/dim]")

    # Last analyzed
    if last_ts:
        git_info = _git_info(cwd)
        table.add_row(
            "Last analyzed",
            f"{_time_ago(last_ts)}  [dim]{git_info}[/dim]",
        )
    else:
        table.add_row("Last analyzed", "[dim]never — run `secrin analyze`[/dim]")

    # Neo4j
    neo4j_icon = Text("● connected", style="green") if connected else Text("✗ unreachable", style="red")
    table.add_row("Neo4j", Text.assemble(neo4j_icon, f"  {neo4j_uri}"))

    # Wiki
    wiki_dir_str = yml.wiki_output_dir if yml else "docs/wiki"
    wiki_path    = cwd / wiki_dir_str
    if wiki_path.exists():
        page_count = len(list(wiki_path.rglob("*.md")))
        table.add_row("Wiki", f"[dim]{wiki_dir_str}[/dim]  ·  [bold]{page_count}[/bold] pages")
    else:
        table.add_row(
            "Wiki",
            f"[dim]{wiki_dir_str}[/dim]  "
            "[dim](not generated — run `secrin generate`)[/dim]",
        )

    # .secrin.yml
    if yml:
        table.add_row(
            ".secrin.yml",
            f"[green]✓[/green]  [dim]{yml.provider} / {yml.model}[/dim]",
        )
    else:
        table.add_row(
            ".secrin.yml",
            "[yellow]✗ not found — run `secrin init`[/yellow]",
        )

    console.print(table)
    console.print(Rule(style="dim"))
    console.print()
