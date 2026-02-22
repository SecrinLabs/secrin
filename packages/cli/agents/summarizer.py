"""
Summarization agent.

Fetches Function, Class, and File nodes that have no summary from Neo4j,
calls the configured LLM, and writes the summary back.

LLM config is driven by packages.config.settings.Settings:
    LLM_PROVIDER         ollama | openai | anthropic
    LLM_MODEL_OLLAMA     model name when provider=ollama
    LLM_MODEL_OPENAI     model name when provider=openai
    LLM_MODEL_ANTHROPIC  model name when provider=anthropic
    ANTHROPIC_API_KEY    required when provider=anthropic
    OPENAI_API_KEY       required when provider=openai
    OLLAMA_BASE_URL      Ollama host when provider=ollama
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.cli.agents.llm_client import client_from_settings
from packages.cli.graph.neo4j_client import NeoClient
from packages.config.settings import Settings

# ---------------------------------------------------------------------------
# Prompt template (loaded once)
# ---------------------------------------------------------------------------

_PROMPT_FILE = Path(__file__).parent / "prompts" / "summarize.txt"
_PROMPT_TEMPLATE = _PROMPT_FILE.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Node queries — one per label
# ---------------------------------------------------------------------------

_FETCH_UNSUMMARIZED = """
MATCH (n:{label})
WHERE n.summary IS NULL
RETURN n.id AS id, n.name AS name, n.path AS path,
       n.signature AS signature, n.extension AS extension
ORDER BY n.id
LIMIT $batch_size
"""

_WRITE_SUMMARY = """
MATCH (n {id: $node_id})
SET n.summary = $summary,
    n.summarized_at = $summarized_at
"""

_LABELS = ("Function", "Class", "File")


# ---------------------------------------------------------------------------
# Prompt builder per node type
# ---------------------------------------------------------------------------

def _build_prompt(label: str, node: dict) -> str:
    name = node.get("name") or "(unnamed)"
    path = node.get("path") or ""
    signature = node.get("signature") or ""
    extension = node.get("extension") or ""

    if label == "File":
        # File nodes have no source code — describe from metadata
        code_snippet = (
            f"File name: {name}\n"
            f"Extension: {extension}\n"
            f"Path: {path}"
        )
    else:
        code_snippet = signature or f"(no source available for {name})"

    return _PROMPT_TEMPLATE.format(
        node_type=label.lower(),
        name=name,
        path=path,
        code_snippet=code_snippet,
    )


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_summarizer(
    client: NeoClient,
    settings: Settings,
    batch_size: int = 50,
    progress_cb: Any = None,
) -> dict[str, int]:
    """
    Summarize all unsummarized nodes across all labels.

    Args:
        client:       Connected NeoClient.
        settings:     Project settings (controls LLM provider + model).
        batch_size:   Nodes per label fetched per round-trip.
        progress_cb:  Optional callable(label, done, total) for progress display.

    Returns:
        dict mapping label → count of nodes summarized this run.
    """
    llm = client_from_settings(settings)

    counts: dict[str, int] = {label: 0 for label in _LABELS}
    now_iso = datetime.now(timezone.utc).isoformat()

    def _write(tx: Any, node_id: str, summary: str) -> None:
        tx.run(_WRITE_SUMMARY, node_id=node_id, summary=summary, summarized_at=now_iso)

    for label in _LABELS:
        query = _FETCH_UNSUMMARIZED.format(label=label)

        while True:
            rows = client.run(query, batch_size=batch_size)
            if not rows:
                break

            for node in rows:
                prompt = _build_prompt(label, node)
                try:
                    summary = llm.complete(prompt, max_tokens=300, temperature=0.2)[:1000]
                except Exception as exc:
                    summary = f"[summarization failed: {exc}]"

                with client.driver.session() as session:
                    session.execute_write(_write, node["id"], summary)

                counts[label] += 1
                if progress_cb:
                    progress_cb(label, counts[label])

    return counts
