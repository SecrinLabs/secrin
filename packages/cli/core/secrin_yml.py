"""
.secrin.yml — repo-level config for Secrin.

This file is committed to the repo. It contains non-secret configuration
shared across the whole team. Secrets (API keys, Neo4j password) are read
from environment variables and written to .env (which is git-ignored).

Format
------
llm:
  provider: ollama          # ollama | openai | anthropic
  model: llama3
  embed_model: nomic-embed-text
  base_url: http://localhost:11434   # Ollama only

neo4j:
  uri: bolt://localhost:7687
  username: neo4j
  database: neo4j

wiki:
  output_dir: docs/wiki
  languages:
    - python
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

_FILENAME = ".secrin.yml"


@dataclass
class SecrinYml:
    # LLM
    provider:        str        = "ollama"
    model:           str        = "llama3"
    embed_model:     str        = "nomic-embed-text"
    base_url:        str        = "http://localhost:11434"  # Ollama host

    # Neo4j
    neo4j_uri:       str        = "bolt://localhost:7687"
    neo4j_user:      str        = "neo4j"
    neo4j_database:  str        = "neo4j"

    # Wiki
    wiki_output_dir: str        = "docs/wiki"
    languages:       list       = field(default_factory=lambda: ["python"])


def load(cwd: Path) -> Optional[SecrinYml]:
    """
    Load .secrin.yml from cwd.

    Returns None if the file does not exist.
    Unknown keys are silently ignored.
    """
    path = cwd / _FILENAME
    if not path.exists():
        return None

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    llm   = data.get("llm",   {}) or {}
    neo4j = data.get("neo4j", {}) or {}
    wiki  = data.get("wiki",  {}) or {}

    return SecrinYml(
        provider        = llm.get("provider",   "ollama"),
        model           = llm.get("model",       "llama3"),
        embed_model     = llm.get("embed_model", "nomic-embed-text"),
        base_url        = llm.get("base_url",    "http://localhost:11434"),
        neo4j_uri       = neo4j.get("uri",       "bolt://localhost:7687"),
        neo4j_user      = neo4j.get("username",  "neo4j"),
        neo4j_database  = neo4j.get("database",  "neo4j"),
        wiki_output_dir = wiki.get("output_dir", "docs/wiki"),
        languages       = wiki.get("languages",  ["python"]),
    )


def write(config: SecrinYml, cwd: Path) -> Path:
    """
    Write config to <cwd>/.secrin.yml.

    Returns the Path that was written.
    Passwords and API keys are NOT written here — they stay in .env.
    """
    path = cwd / _FILENAME

    data: dict = {
        "llm": {
            "provider":    config.provider,
            "model":       config.model,
            "embed_model": config.embed_model,
        },
        "neo4j": {
            "uri":      config.neo4j_uri,
            "username": config.neo4j_user,
            "database": config.neo4j_database,
        },
        "wiki": {
            "output_dir": config.wiki_output_dir,
            "languages":  list(config.languages),
        },
    }

    # Include base_url only for ollama (keeps YAML clean for cloud providers)
    if config.provider == "ollama":
        data["llm"]["base_url"] = config.base_url
    elif config.base_url != "http://localhost:11434":
        # Non-default base_url even for cloud providers (e.g. Anthropic needs
        # Ollama for embeddings) — store so teams can share it.
        data["llm"]["base_url"] = config.base_url

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    return path


def exists(cwd: Path) -> bool:
    """Return True if .secrin.yml exists in cwd."""
    return (cwd / _FILENAME).exists()
