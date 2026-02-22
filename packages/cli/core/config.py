"""
.secrin/config.yaml read/write.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

SECRIN_DIR = ".secrin"
CONFIG_FILE = "config.yaml"


@dataclass
class Config:
    project_name: str
    repo_url: str
    repo_path: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_generated: str = ""
    version: int = 1
    wiki_path: str = ".secrin/wiki"
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-5"
    api_key_env: str = "ANTHROPIC_API_KEY"


def load(cwd: Path) -> Config:
    """Read .secrin/config.yaml; raise FileNotFoundError if missing."""
    path = cwd / SECRIN_DIR / CONFIG_FILE
    if not path.exists():
        raise FileNotFoundError(
            f"No .secrin/config.yaml found in {cwd}. Run `secrin init --repo <url>` first."
        )
    with open(path) as f:
        data = yaml.safe_load(f)
    return Config(**data)


def save(config: Config, cwd: Path) -> None:
    """Write .secrin/config.yaml, creating .secrin/ if needed."""
    secrin_dir = cwd / SECRIN_DIR
    secrin_dir.mkdir(parents=True, exist_ok=True)
    path = secrin_dir / CONFIG_FILE
    with open(path, "w") as f:
        yaml.dump(dataclasses.asdict(config), f, default_flow_style=False)


def exists(cwd: Path) -> bool:
    return (cwd / SECRIN_DIR / CONFIG_FILE).exists()
