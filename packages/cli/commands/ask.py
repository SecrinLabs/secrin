"""
`secrin ask "<question>"` command.

Phase 1: keyword-matched wiki retrieval → LLM answer with citations.
No vector DB, no embeddings.
"""
from __future__ import annotations

import re
from pathlib import Path

import typer

from packages.cli.core import config as cfg_module
from packages.arc42gen.providers.factory import create_llm_provider
from packages.arc42gen.models.config import LLMConfig
import os

# ---------------------------------------------------------------------------
# LLM helper (same pattern as writer.py — direct provider call)
# ---------------------------------------------------------------------------

_MAX_CONTEXT_CHARS = 12_000   # total chars across all wiki files sent to LLM
_MAX_FILE_CHARS = 5_000       # per-file cap before truncation


def _llm_answer(question: str, context: str, provider: str, model: str) -> str:
    """Ask the LLM to answer `question` using `context`. Temperature 0.1."""
    _API_KEY_ENVS = {"anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY"}
    env_var = _API_KEY_ENVS.get(provider.lower())
    api_key = os.environ.get(env_var, "") if env_var else ""

    if provider.lower() not in ("ollama",) and not api_key:
        raise ValueError(
            f"API key not set. Export {env_var} before running `secrin ask`."
        )

    system_prompt = (
        "You are answering questions about a software project "
        "using only the wiki documentation provided below.\n\n"
        "Rules:\n"
        "- Answer clearly and specifically.\n"
        "- Cite which wiki file your answer comes from using [filename] format.\n"
        "- If the answer is not in the documentation, say so directly — "
        "do NOT hallucinate or guess.\n"
        "- Keep your answer concise (under 300 words unless the question demands more).\n\n"
        f"Documentation:\n{context}"
    )

    cfg = LLMConfig(
        provider=provider.lower(),
        model=model,
        api_key=api_key,
        max_tokens=1024,
        base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
    )
    llm = create_llm_provider(cfg)
    response = llm.generate(
        prompt=question,
        max_tokens=1024,
        temperature=0.1,
        system_prompt=system_prompt,
    )
    return response.content


# ---------------------------------------------------------------------------
# Relevance scoring
# ---------------------------------------------------------------------------

def _tokenise(text: str) -> set[str]:
    """Lower-case word tokens, length ≥ 3, no punctuation."""
    return {w for w in re.findall(r"[a-z0-9_]+", text.lower()) if len(w) >= 3}


def _score_file(question_tokens: set[str], content: str) -> int:
    """Count how many question tokens appear in the file content."""
    file_tokens = _tokenise(content)
    return len(question_tokens & file_tokens)


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

def ask(
    question: str = typer.Argument(..., help="Question about the codebase"),
) -> None:
    """Ask a question about the codebase. Answers are sourced from the wiki."""
    cwd = Path.cwd()

    try:
        cfg = cfg_module.load(cwd)
    except FileNotFoundError:
        typer.echo("Not initialised. Run: secrin init --repo <url>", err=True)
        raise typer.Exit(code=1)

    wiki_path = cwd / cfg.wiki_path
    wiki_files = sorted(wiki_path.rglob("*.md"))

    if not wiki_files:
        typer.echo("No wiki files found. Run: secrin init --repo <url>")
        raise typer.Exit(code=1)

    # Score every wiki file for relevance
    question_tokens = _tokenise(question)
    scored: list[tuple[int, Path, str]] = []
    for f in wiki_files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        score = _score_file(question_tokens, content)
        scored.append((score, f, content))

    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[:3]

    if not top or top[0][0] == 0:
        typer.echo(
            "No relevant wiki content found for this question.\n"
            "The wiki may not cover this topic yet.\n"
            "Try: secrin init --repo <url> --force  to regenerate."
        )
        raise typer.Exit()

    # Build context, capping each file to avoid token overflow
    context_parts: list[str] = []
    total_chars = 0
    sources: list[str] = []

    for score, f, content in top:
        if total_chars >= _MAX_CONTEXT_CHARS:
            break
        snippet = content[:_MAX_FILE_CHARS]
        if len(content) > _MAX_FILE_CHARS:
            snippet += f"\n... [{len(content) - _MAX_FILE_CHARS} chars truncated]"
        context_parts.append(f"--- {f.name} ---\n{snippet}")
        sources.append(f.name)
        total_chars += len(snippet)

    context = "\n\n".join(context_parts)

    # Call LLM
    try:
        answer = _llm_answer(
            question=question,
            context=context,
            provider=cfg.llm_provider,
            model=cfg.llm_model,
        )
    except ValueError as e:
        typer.echo(f"[error] {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"\n{answer}")
    typer.echo(f"\nSources: {', '.join(sources)}")
