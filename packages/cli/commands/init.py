"""
`secrin init` — interactive setup wizard.

Creates .secrin.yml in the current directory with LLM provider, Neo4j
connection, and wiki settings.  Secrets (API keys, Neo4j password) are
written to .env and never stored in .secrin.yml.

Interactive flow
----------------
  ? LLM provider (ollama / openai / anthropic): ollama
  ? Ollama host [http://localhost:11434]:
  ? Ollama model [llama3]:
  ? Embed model [nomic-embed-text]:
  ? Neo4j URI [bolt://localhost:7687]:
  ? Neo4j username [neo4j]:
  ? Neo4j password:
  ? Neo4j database [neo4j]:
  ? Wiki output directory [docs/wiki]:

  ✓ Created .secrin.yml
  ✓ Updated .env  (NEO4J_PASS)
  ✓ Connected to Neo4j  (42 nodes found)
  ✓ Connected to Ollama  (llama3 available)

  Run `secrin graph build --repo <url-or-path>` to index your repo.

After init, commit .secrin.yml.  Never commit .env.
"""
from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from packages.cli.core.secrin_yml import (
    SecrinYml,
    load  as load_yml,
    write as write_yml,
    exists as yml_exists,
)
from packages.cli.agents.llm_client import (
    LLMClient,
    client_from_yml,
    _DEFAULT_MODELS,
    _DEFAULT_EMBED_MODELS,
)

console = Console()

# Provider → default completion model
_COMPLETION_DEFAULTS: dict[str, str] = {
    "ollama":    "llama3",
    "openai":    "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
}

# Provider → default embed model
_EMBED_DEFAULTS: dict[str, str] = {
    "ollama":    "nomic-embed-text",
    "openai":    "text-embedding-3-small",
    "anthropic": "nomic-embed-text",  # via Ollama
}


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

def init(
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Overwrite existing .secrin.yml without asking",
    ),
) -> None:
    """
    Interactive setup wizard — creates .secrin.yml in the current directory.

    Prompts for LLM provider, model, Neo4j connection, and wiki output
    directory.  API keys and the Neo4j password are written to .env (which
    should be git-ignored) and are never stored in .secrin.yml.

    Commit .secrin.yml so teammates can run `secrin init` with the same
    defaults after cloning your repo.

    After init, index your codebase:
        secrin graph build --repo <url-or-path>
    """
    cwd = Path.cwd()

    if yml_exists(cwd) and not force:
        typer.echo(".secrin.yml already exists. Use --force to reconfigure.")
        raise typer.Exit()

    # Load existing config as prompt defaults (re-init flow)
    existing = load_yml(cwd)
    d = existing or SecrinYml()

    typer.echo("")
    console.print(Panel.fit(
        "[bold green]Secrin Setup Wizard[/bold green]\n"
        "[dim]Creates .secrin.yml — commit this file to your repo[/dim]",
        border_style="green",
    ))
    typer.echo("")

    # ── 1. LLM provider ──────────────────────────────────────────────────────
    provider = typer.prompt(
        "? LLM provider (ollama / openai / anthropic)",
        default=d.provider,
    ).strip().lower()

    if provider not in ("ollama", "openai", "anthropic"):
        typer.echo(
            f"[error] Unknown provider {provider!r}. "
            "Choose: ollama, openai, anthropic",
            err=True,
        )
        raise typer.Exit(code=1)

    # Use existing model only if provider hasn't changed
    model_default = (
        d.model if d.provider == provider
        else _COMPLETION_DEFAULTS[provider]
    )
    embed_default = (
        d.embed_model if d.provider == provider
        else _EMBED_DEFAULTS[provider]
    )

    model       = typer.prompt(f"? {provider.capitalize()} model", default=model_default).strip()
    embed_model = typer.prompt("? Embed model",                    default=embed_default).strip()

    # Provider-specific config
    base_url = d.base_url
    api_key  = ""

    if provider == "ollama":
        base_url = typer.prompt(
            "? Ollama host",
            default=d.base_url,
        ).strip().rstrip("/")

    else:
        # Cloud providers need an API key (written to .env, not .secrin.yml)
        env_var      = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}[provider]
        existing_key = os.environ.get(env_var, "")
        if existing_key:
            typer.echo(f"  ({env_var} already set — press Enter to keep it)")
        api_key = typer.prompt(
            f"? {env_var}",
            default="",
            hide_input=True,
        ).strip()
        if not api_key:
            api_key = existing_key

        if provider == "anthropic":
            # Anthropic has no embed API; Ollama handles embeddings
            base_url = typer.prompt(
                "? Ollama host (for embeddings — Anthropic has no embed API)",
                default=d.base_url,
            ).strip().rstrip("/")

    # ── 2. Neo4j ──────────────────────────────────────────────────────────────
    typer.echo("")
    neo4j_uri  = typer.prompt("? Neo4j URI",      default=d.neo4j_uri).strip()
    neo4j_user = typer.prompt("? Neo4j username", default=d.neo4j_user).strip()
    neo4j_pass = typer.prompt(
        "? Neo4j password",
        default="",
        hide_input=True,
    ).strip()
    if not neo4j_pass:
        neo4j_pass = os.environ.get("NEO4J_PASS", "")
    neo4j_db = typer.prompt("? Neo4j database", default=d.neo4j_database).strip()

    # ── 3. Wiki ────────────────────────────────────────────────────────────────
    typer.echo("")
    wiki_dir = typer.prompt(
        "? Wiki output directory",
        default=d.wiki_output_dir,
    ).strip()

    # ── 4. Write .secrin.yml ──────────────────────────────────────────────────
    cfg = SecrinYml(
        provider        = provider,
        model           = model,
        embed_model     = embed_model,
        base_url        = base_url,
        neo4j_uri       = neo4j_uri,
        neo4j_user      = neo4j_user,
        neo4j_database  = neo4j_db,
        wiki_output_dir = wiki_dir,
    )

    typer.echo("")
    yml_path = write_yml(cfg, cwd)
    typer.echo(f"✓ Created {yml_path.name}")

    # ── 5. Write secrets to .env ──────────────────────────────────────────────
    _update_env(cwd, provider, api_key, neo4j_pass)

    # ── 6. Verify connections ─────────────────────────────────────────────────
    typer.echo("")
    _verify_neo4j(neo4j_uri, neo4j_user, neo4j_pass, neo4j_db)
    _verify_llm(cfg, api_key)

    # ── 7. Next steps ─────────────────────────────────────────────────────────
    typer.echo("")
    typer.echo("Run `secrin graph build --repo <url-or-path>` to index your repo.")
    typer.echo("")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _update_env(
    cwd: Path,
    provider: str,
    api_key: str,
    neo4j_pass: str,
) -> None:
    """
    Append or update secret lines in <cwd>/.env.

    Existing unrelated lines are preserved.  New keys are appended.
    If there is nothing to write the function returns silently.
    """
    env_path = cwd / ".env"

    updates: dict[str, str] = {}
    if neo4j_pass:
        updates["NEO4J_PASS"] = neo4j_pass
    if api_key:
        if provider == "openai":
            updates["OPENAI_API_KEY"] = api_key
        elif provider == "anthropic":
            updates["ANTHROPIC_API_KEY"] = api_key

    if not updates:
        return

    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    already_set: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        key = line.split("=", 1)[0].strip()
        if key in updates:
            new_lines.append(f"{key}={updates[key]}")
            already_set.add(key)
        else:
            new_lines.append(line)

    for key, val in updates.items():
        if key not in already_set:
            new_lines.append(f"{key}={val}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    typer.echo(f"✓ Updated .env  ({', '.join(updates)})")


def _verify_neo4j(uri: str, user: str, password: str, database: str) -> None:
    """Try to connect to Neo4j and print a node count."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session(database=database) as session:
            result = session.run("MATCH (n) RETURN count(n) AS c")
            count  = result.single()["c"]
        driver.close()
        typer.echo(f"✓ Connected to Neo4j  ({count} nodes found)")
    except Exception as exc:
        typer.echo(f"✗ Neo4j connection failed: {exc}")
        typer.echo(
            "  → Start Neo4j and re-run `secrin init`, "
            "or continue and fix later."
        )


def _verify_llm(cfg: SecrinYml, api_key: str) -> None:
    """Ping the LLM provider and report success or failure."""
    try:
        client = client_from_yml(cfg, api_key=api_key)
        ok = client.ping_llm()
        if ok:
            typer.echo(
                f"✓ Connected to {cfg.provider.capitalize()}"
                f"  ({cfg.model} available)"
            )
        else:
            typer.echo(
                f"✗ {cfg.provider.capitalize()} ping returned unexpected result."
            )
    except Exception as exc:
        typer.echo(f"✗ {cfg.provider.capitalize()} connection failed: {exc}")
        typer.echo(
            "  → Check provider settings and API key, "
            "then re-run `secrin init`."
        )
