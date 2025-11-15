from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, List, Dict, Any

from git import Repo

from packages.memory.memory import Memory
from packages.ingest.edges import Edge
from packages.parser.utils import extract_repo_info


@dataclass
class CommitInfo:
    sha: str
    message: str
    author_name: str
    author_email: str
    committed_datetime: datetime
    files_changed: List[str]
    insertions: int
    deletions: int


def _summarize_commit(commit) -> CommitInfo:
    stats = commit.stats.total or {}
    files = list((commit.stats.files or {}).keys())
    return CommitInfo(
        sha=commit.hexsha,
        message=(commit.message or "").strip(),
        author_name=getattr(commit.author, "name", "") or "",
        author_email=getattr(commit.author, "email", "") or "",
        committed_datetime=getattr(commit, "committed_datetime", datetime.utcnow()),
        files_changed=files,
        insertions=int(stats.get("insertions", 0)),
        deletions=int(stats.get("deletions", 0)),
    )


def _decision_doc(repo_url: str, info: CommitInfo) -> str:
    dt = info.committed_datetime.isoformat()
    file_list = "\n".join(f"  - {p}" for p in info.files_changed[:50])  # cap list for brevity
    return (
        f"Commit: {info.sha}\n"
        f"Author: {info.author_name} <{info.author_email}>\n"
        f"Date:   {dt}\n"
        f"Repo:   {repo_url}\n"
        f"\n"
        f"Message:\n{info.message}\n\n"
        f"Scope:\n"
        f"  Files changed: {len(info.files_changed)}\n"
        f"  Insertions:    {info.insertions}\n"
        f"  Deletions:     {info.deletions}\n"
        f"\n"
        f"Files:\n{file_list if file_list else '  (no file stats available)'}\n"
    )


def _upsert_repo(memory: Memory, repo_url: str) -> str:
    info = extract_repo_info(repo_url)
    repo_id = f"repo:{info['full_name']}"
    match = {"url": info["url"]}
    props = {
        "id": repo_id,
        "url": info["url"],
        "owner": info.get("owner", "unknown"),
        "name": info.get("name", "unknown"),
        "full_name": info.get("full_name", "unknown"),
        "content": info.get("full_name", "unknown"),
    }
    return memory.upsert_node("Repository", match, props)


def _upsert_person(memory: Memory, name: str, email: str) -> str:
    email_norm = (email or "").strip().lower()
    name_norm = (name or "").strip()
    if email_norm:
        match = {"email": email_norm}
        pid = f"person:{email_norm}"
    else:
        match = {"name": name_norm}
        pid = f"person:{name_norm.lower().replace(' ', '_')}"
    props = {"id": pid, "name": name_norm, "email": email_norm}
    return memory.upsert_node("Person", match, props)


def _upsert_commit(memory: Memory, repo_url: str, info: CommitInfo, content: str) -> str:
    cid = f"commit:{info.sha}"
    match = {"sha": info.sha}
    props = {
        "id": cid,
        "sha": info.sha,
        "content": content,
        "author_name": info.author_name,
        "author_email": info.author_email,
        "committed_at": info.committed_datetime.isoformat(),
        "insertions": info.insertions,
        "deletions": info.deletions,
        "files_changed": info.files_changed,
        "repo_url": repo_url,
    }
    return memory.upsert_node("Commit", match, props)


def process_repository(repo_url: str, branch: Optional[str] = None, max_commits: Optional[int] = None) -> Dict[str, Any]:
    memory = Memory()
    commit_nodes: List[str] = []
    author_nodes: List[str] = []

    # Create/merge repository node once
    repo_node_id = _upsert_repo(memory, repo_url)

    # Support local path or remote URL
    path: Optional[Path] = None
    cleanup = False

    tmp: Optional[TemporaryDirectory] = None

    if Path(repo_url).exists():
        # Local repository
        path = Path(repo_url)
        repo = Repo(path)
    else:
        # Remote repository -> clone into temp dir
        tmp = TemporaryDirectory()
        cleanup = True
        path = Path(tmp.name)
        repo = Repo.clone_from(repo_url, path)

    try:
        # Checkout branch if provided
        if branch:
            repo.git.checkout(branch)

        # Iterate commits, newest first
        commits = list(repo.iter_commits(max_count=max_commits)) if max_commits else list(repo.iter_commits())
        print(f"[commit_ingest] repo={repo_url} branch={branch or 'HEAD'} total_commits_found={len(commits)} max_commits_limit={max_commits}")
        if commits:
            sample = [c.hexsha[:8] for c in commits[:10]]
            print(f"[commit_ingest] sample_shas={sample}")
        else:
            print("[commit_ingest] WARNING: No commits found. Possible empty repo, wrong branch, or shallow clone issue.")

        for c in commits:
            info = _summarize_commit(c)
            doc = _decision_doc(repo_url, info)

            commit_id = _upsert_commit(memory, repo_url, info, doc)
            print(f"[commit_ingest] created commit node sha={info.sha} node_id={commit_id}")
            commit_nodes.append(commit_id)

            # Author node
            author_id = _upsert_person(memory, info.author_name, info.author_email)
            author_nodes.append(author_id)

            # Link commit to repo & author
            memory.link(commit_id, Edge.BELONGS_TO, repo_node_id)
            memory.link(commit_id, Edge.AUTHORED_BY, author_id)
            print(f"[commit_ingest] linked commit -> repo ({Edge.BELONGS_TO.value}), commit -> author ({Edge.AUTHORED_BY.value})")

            # (File nodes intentionally omitted per current requirements)

        return {
            "repo_node": repo_node_id,
            "commit_nodes": commit_nodes,
            "author_nodes": list(set(author_nodes)),
            "counts": {
                "commits": len(commit_nodes),
                "authors": len(set(author_nodes)),
            },
        }
    finally:
        # Best-effort cleanup for clones
        if cleanup:
            try:
                repo.close()
            except Exception:
                pass
            # TemporaryDirectory object will clean itself when GC'ed; ensure context end
            try:
                if tmp is not None:
                    tmp.cleanup()
            except Exception:
                pass


__all__ = [
    "process_repository",
]
