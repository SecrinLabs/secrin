"""
Clone a GitHub repo to a temp directory.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


def clone(repo_url: str) -> Path:
    """
    Clone repo_url to /tmp/secrin-{repo-name}-{8-char-hash}/.

    Reuses the existing clone if the destination already exists.
    Raises ValueError with a clear message if the clone fails.
    """
    repo_name = repo_url.rstrip("/").split("/")[-1].removesuffix(".git")
    url_hash = hashlib.md5(repo_url.encode()).hexdigest()[:8]
    dest = Path(f"/tmp/secrin-{repo_name}-{url_hash}")

    if dest.exists():
        print(f"  Using existing clone at {dest}")
        return dest

    print(f"  Cloning {repo_url}...")
    result = subprocess.run(
        ["git", "clone", repo_url, str(dest)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise ValueError(
            f"Failed to clone {repo_url}.\n"
            f"Git error: {stderr}\n"
            "Check that the URL is correct and you have network access / auth configured."
        )

    return dest
