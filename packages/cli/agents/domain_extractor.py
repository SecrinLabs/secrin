"""
Domain Entity Extraction Agent.

Reads node summaries from Neo4j, asks the LLM to identify business/domain
concepts, then writes DomainEntity nodes + IMPLEMENTS_DOMAIN edges back.

New Neo4j nodes:
    (:DomainEntity {id, name, description, subdomain, extracted_at})

New Neo4j edges:
    (:Function)-[:IMPLEMENTS_DOMAIN]->(:DomainEntity)
    (:Class)-[:IMPLEMENTS_DOMAIN]->(:DomainEntity)
    (:File)-[:IMPLEMENTS_DOMAIN]->(:DomainEntity)

Config from packages.config.settings.Settings:
    LLM_PROVIDER        ollama | anthropic | gemini
    LLM_MODEL_OLLAMA    model name when provider=ollama
    ANTHROPIC_API_KEY   required when provider=anthropic
    GEMINI_API_KEY      required when provider=gemini
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.cli.agents.llm_client import client_from_settings
from packages.cli.graph.neo4j_client import NeoClient
from packages.config.settings import Settings

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_PROMPT_FILE = Path(__file__).parent / "prompts" / "domains.txt"
_PROMPT_TEMPLATE = _PROMPT_FILE.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Neo4j queries
# ---------------------------------------------------------------------------

_CREATE_CONSTRAINT = """
CREATE CONSTRAINT domain_id IF NOT EXISTS FOR (d:DomainEntity) REQUIRE d.id IS UNIQUE
"""

_FETCH_SUMMARIES = """
MATCH (n)
WHERE n.summary IS NOT NULL
  AND labels(n)[0] IN ['Function', 'Class', 'File']
RETURN n.id AS id, n.name AS name, n.path AS path,
       n.summary AS summary, labels(n)[0] AS label
ORDER BY
    CASE labels(n)[0]
        WHEN 'Function' THEN 1
        WHEN 'Class' THEN 2
        ELSE 3
    END,
    n.id
LIMIT $limit
"""

_MERGE_DOMAIN = """
MERGE (d:DomainEntity {id: $id})
SET d.name = $name,
    d.description = $description,
    d.subdomain = $subdomain,
    d.extracted_at = $extracted_at
"""

_LINK_NODE_TO_DOMAIN = """
MATCH (n)
WHERE toLower(n.name) = toLower($node_name)
  AND labels(n)[0] IN ['Function', 'Class', 'File']
MATCH (d:DomainEntity {id: $domain_id})
MERGE (n)-[:IMPLEMENTS_DOMAIN]->(d)
RETURN count(*) AS linked
"""

_COUNT_DOMAINS = "MATCH (d:DomainEntity) RETURN count(d) AS c"
_COUNT_EDGES = "MATCH ()-[r:IMPLEMENTS_DOMAIN]->() RETURN count(r) AS c"


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_batch_prompt(nodes: list[dict]) -> str:
    lines = []
    for node in nodes:
        label   = node.get("label", "")
        name    = node.get("name", "")
        path    = node.get("path", "")
        summary = node.get("summary", "").replace("\n", " ")
        lines.append(f"[{label}] {name} ({path}): {summary}")
    # Use str.replace() not .format() — summaries may contain {curly braces}
    # that would be mis-interpreted as format placeholders.
    return _PROMPT_TEMPLATE.replace("{summaries}", "\n".join(lines))


# ---------------------------------------------------------------------------
# JSON extraction from LLM response
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Strip markdown fences if present and parse the first JSON object."""
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in LLM response")
    return json.loads(text[start:end])


# ---------------------------------------------------------------------------
# Domain merging across batches
# ---------------------------------------------------------------------------

def _merge_domains(
    existing: dict[str, dict],
    new_domains: list[dict],
) -> dict[str, dict]:
    """
    Merge a list of domain dicts into the running accumulator.
    Key is the normalized name (lowercase, underscores).
    Existing descriptions are kept; implements lists are union-merged.
    """
    for d in new_domains:
        name = (d.get("name") or "").strip()
        if not name:
            continue
        key = re.sub(r"\s+", "_", name.lower())
        if key not in existing:
            existing[key] = {
                "name":        name,
                "description": d.get("description", ""),
                "subdomain":   d.get("subdomain", ""),
                "implements":  list(d.get("implements", [])),
            }
        else:
            seen = set(existing[key]["implements"])
            for impl in d.get("implements", []):
                if impl and impl not in seen:
                    existing[key]["implements"].append(impl)
                    seen.add(impl)
    return existing


# ---------------------------------------------------------------------------
# Neo4j write helpers
# ---------------------------------------------------------------------------

def _write_domain_node(
    client: NeoClient,
    domain_id: str,
    name: str,
    description: str,
    subdomain: str,
    now_iso: str,
) -> None:
    def _tx(tx: Any) -> None:
        tx.run(
            _MERGE_DOMAIN,
            id=domain_id,
            name=name,
            description=description,
            subdomain=subdomain,
            extracted_at=now_iso,
        )
    with client.driver.session() as session:
        session.execute_write(_tx)


def _write_impl_edge(client: NeoClient, node_name: str, domain_id: str) -> int:
    """Returns number of nodes linked (0 if no node matched the name)."""
    def _tx(tx: Any) -> int:
        result = tx.run(_LINK_NODE_TO_DOMAIN, node_name=node_name, domain_id=domain_id)
        record = result.single()
        return int(record["linked"]) if record else 0
    with client.driver.session() as session:
        return session.execute_write(_tx)


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_domain_extractor(
    client: NeoClient,
    settings: Settings,
    sample_limit: int = 200,
    batch_size: int = 60,
    progress_cb: Any = None,
) -> dict:
    """
    Extract domain entities from existing Neo4j summaries.

    Args:
        client:       Connected NeoClient.
        settings:     Project settings (controls LLM provider + model).
        sample_limit: Max nodes to sample for domain extraction.
        batch_size:   Nodes per LLM call.
        progress_cb:  Optional callable(step: str, detail: str).

    Returns:
        dict with keys: domains (int), edges (int), domain_list (list[dict])
    """
    # Ensure DomainEntity uniqueness constraint exists
    client.run(_CREATE_CONSTRAINT)

    # 1. Fetch summaries from Neo4j
    if progress_cb:
        progress_cb("fetch", f"Sampling up to {sample_limit} node summaries...")
    nodes = client.run(_FETCH_SUMMARIES, limit=sample_limit)
    if not nodes:
        raise ValueError("No summarized nodes found. Run `secrin analyze` first.")

    if progress_cb:
        progress_cb("fetch", f"Loaded {len(nodes)} nodes.")

    # 2. Call LLM in batches; merge domains across responses
    llm = client_from_settings(settings)

    merged: dict[str, dict] = {}
    batches = [nodes[i : i + batch_size] for i in range(0, len(nodes), batch_size)]

    for i, batch in enumerate(batches, 1):
        if progress_cb:
            progress_cb("llm", f"LLM call {i}/{len(batches)} ({len(batch)} nodes)...")
        prompt = _build_batch_prompt(batch)
        try:
            raw_text = llm.complete(prompt, max_tokens=2000, temperature=0.1)
            parsed   = _extract_json(raw_text)
            domains  = parsed.get("domains", [])
            _merge_domains(merged, domains)
        except Exception as exc:
            if progress_cb:
                progress_cb("warn", f"Batch {i} failed: {exc}")

    if not merged:
        raise ValueError(
            "LLM returned no domain entities. "
            "Try a different provider or add more summaries with `secrin analyze`."
        )

    # 3. Write DomainEntity nodes + IMPLEMENTS_DOMAIN edges
    if progress_cb:
        progress_cb("write", f"Writing {len(merged)} domain entities to Neo4j...")

    now_iso = datetime.now(timezone.utc).isoformat()
    domain_list: list[dict] = []

    for key, d in merged.items():
        domain_id = f"domain::{key}"

        _write_domain_node(
            client,
            domain_id=domain_id,
            name=d["name"],
            description=d["description"],
            subdomain=d["subdomain"],
            now_iso=now_iso,
        )

        unmatched: list[str] = []
        for raw_name in d.get("implements", []):
            # Strip path prefix if LLM included it (e.g. "auth.py::verify_token")
            node_name = raw_name.strip().split("::")[-1].strip()
            if not node_name:
                continue
            try:
                linked = _write_impl_edge(client, node_name, domain_id)
                if linked == 0:
                    unmatched.append(node_name)
            except Exception as exc:
                unmatched.append(f"{node_name} ({exc})")

        if unmatched and progress_cb:
            progress_cb(
                "warn",
                f"[{d['name']}] unmatched names: {', '.join(unmatched[:5])}"
                + (f" (+{len(unmatched) - 5} more)" if len(unmatched) > 5 else ""),
            )

        domain_list.append({
            "id":          domain_id,
            "name":        d["name"],
            "subdomain":   d["subdomain"],
            "description": d["description"],
            "implements":  d.get("implements", []),
        })

    # 4. Return verified counts
    final_domains = client.run(_COUNT_DOMAINS)[0]["c"]
    final_edges   = client.run(_COUNT_EDGES)[0]["c"]

    return {
        "domains":     final_domains,
        "edges":       final_edges,
        "domain_list": domain_list,
    }
