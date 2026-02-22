"""
Incremental Neo4j graph update for changed files.

Given a list of changed file paths (from git):
  1. Delete stale nodes for each changed/deleted file
  2. Re-parse changed files (skip deleted ones)
  3. Insert fresh File / Class / Function nodes + Module edge
  4. Re-resolve CALLS, IMPORTS, INHERITS using Neo4j lookup tables
  5. Re-summarize and re-embed nodes that lost their summary (summary IS NULL)

Returns a dict describing what changed so callers can decide which wiki
pages to regenerate.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from packages.cli.core.parser import parse_files, ParsedFile
from packages.cli.graph.builder import _fn_id_for, _extract_py_bases, _import_top_module
from packages.cli.graph.neo4j_client import NeoClient
from packages.cli.agents.summarizer import run_summarizer
from packages.cli.agents.embedder import run_embedder
from packages.config.settings import Settings

# ---------------------------------------------------------------------------
# Delete queries — run in order (deep → shallow)
# ---------------------------------------------------------------------------

_DEL_METHODS = """
MATCH (f:File {path: $path})-[:DEFINES]->(:Class)-[:CONTAINS]->(m:Function)
DETACH DELETE m
"""
_DEL_FNS_CLASSES = """
MATCH (f:File {path: $path})-[:DEFINES]->(n)
DETACH DELETE n
"""
_DEL_FILE = """
MATCH (f:File {path: $path})
DETACH DELETE f
"""

# ---------------------------------------------------------------------------
# Insert queries — single-row MERGE (no UNWIND batch needed for small counts)
# ---------------------------------------------------------------------------

_MERGE_MODULE = """
MERGE (m:Module {id: $id})
SET m.name = $name, m.path = $path
"""
_MERGE_FILE = """
MERGE (f:File {id: $id})
SET f.path = $path, f.name = $name, f.extension = $extension, f.size = $size
"""
_MERGE_CLASS = """
MERGE (c:Class {id: $id})
SET c.name = $name, c.path = $path,
    c.start_line = $start_line, c.end_line = $end_line, c.signature = $signature
"""
_MERGE_FN = """
MERGE (fn:Function {id: $id})
SET fn.name = $name, fn.path = $path,
    fn.start_line = $start_line, fn.end_line = $end_line,
    fn.signature = $signature, fn.type = $type
"""

# ---------------------------------------------------------------------------
# Relationship queries
# ---------------------------------------------------------------------------

_REL_MODULE_FILE  = "MATCH (m:Module {id: $mid})  MATCH (f:File     {id: $fid})  MERGE (m)-[:CONTAINS]->(f)"
_REL_FILE_CLASS   = "MATCH (f:File   {id: $fid})  MATCH (c:Class    {id: $cid})  MERGE (f)-[:DEFINES]->(c)"
_REL_FILE_FN      = "MATCH (f:File   {id: $fid})  MATCH (fn:Function{id: $fnid}) MERGE (f)-[:DEFINES]->(fn)"
_REL_CLASS_METHOD = "MATCH (c:Class  {id: $cid})  MATCH (fn:Function{id: $fnid}) MERGE (c)-[:CONTAINS]->(fn)"
_REL_INHERITS     = "MATCH (c:Class  {id: $cid})  MATCH (b:Class    {id: $bid})  MERGE (c)-[:INHERITS]->(b)"
_REL_CALLS        = "MATCH (a:Function{id: $aid}) MATCH (b:Function {id: $bid})  MERGE (a)-[:CALLS]->(b)"
_REL_IMPORTS      = "MATCH (a:File   {id: $aid})  MATCH (b:File     {id: $bid})  MERGE (a)-[:IMPORTS]->(b)"

# ---------------------------------------------------------------------------
# Lookup queries
# ---------------------------------------------------------------------------

_ALL_FN_IDS    = "MATCH (fn:Function) RETURN fn.name AS name, fn.id AS id"
_ALL_CLASS_IDS = "MATCH (c:Class)     RETURN c.name  AS name, c.id  AS id"
_ALL_FILE_IDS  = "MATCH (f:File)      RETURN f.path  AS path, f.id  AS id"
_MODULE_FOR    = """
MATCH (m:Module)-[:CONTAINS]->(f:File {path: $path})
RETURN m.name AS name LIMIT 1
"""


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def get_changed_files(repo_path: Path) -> tuple[list[str], list[str]]:
    """
    Return (to_update, to_delete) lists of relative file paths from HEAD commit.

    to_update: Added / Modified / Copied / Renamed-to paths → re-parse + re-insert
    to_delete: Deleted / Renamed-from paths → delete nodes only
    """
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "-r", "--name-status", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [], []

    to_update: list[str] = []
    to_delete: list[str] = []

    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0].strip()
        if status.startswith("D"):
            to_delete.append(parts[1].strip())
        elif status.startswith("R") and len(parts) >= 3:
            to_delete.append(parts[1].strip())   # old path
            to_update.append(parts[2].strip())   # new path
        elif status.startswith(("A", "M", "C")):
            to_update.append(parts[1].strip())

    return to_update, to_delete


# ---------------------------------------------------------------------------
# Delete helpers
# ---------------------------------------------------------------------------

def delete_file_nodes(client: NeoClient, rel_path: str) -> None:
    """Delete all Neo4j nodes associated with a file path (deepest first)."""
    client.run(_DEL_METHODS,     path=rel_path)
    client.run(_DEL_FNS_CLASSES, path=rel_path)
    client.run(_DEL_FILE,        path=rel_path)


# ---------------------------------------------------------------------------
# Insert helpers
# ---------------------------------------------------------------------------

def _w(client: NeoClient, cypher: str, **params: Any) -> None:
    """Execute a single write in a transaction."""
    def _tx(tx: Any) -> None:
        tx.run(cypher, **params)
    with client.driver.session() as session:
        session.execute_write(_tx)


def insert_parsed_file(client: NeoClient, pf: ParsedFile, repo_path: Path) -> None:
    """
    Insert File / Module / Class / Function nodes for one ParsedFile.
    Relationships (CALLS, IMPORTS, INHERITS) are resolved separately.
    """
    abs_path = repo_path / pf.path
    try:
        size = abs_path.stat().st_size
    except OSError:
        size = 0

    file_id = f"file::{pf.path}"
    parts = Path(pf.path).parts
    module_name = parts[0] if len(parts) > 1 else "__root__"
    module_id   = f"module::{module_name}"

    # File + Module nodes
    _w(client, _MERGE_MODULE, id=module_id, name=module_name, path=module_name)
    _w(client, _MERGE_FILE,
       id=file_id, path=pf.path,
       name=Path(pf.path).name, extension=Path(pf.path).suffix, size=size)
    _w(client, _REL_MODULE_FILE, mid=module_id, fid=file_id)

    # Class nodes
    class_ranges: list[tuple[int, int, str, str]] = []
    for cls in pf.classes:
        cid = f"class::{pf.path}::{cls.name}"
        _w(client, _MERGE_CLASS,
           id=cid, name=cls.name, path=pf.path,
           start_line=cls.start_line, end_line=cls.end_line,
           signature=cls.source[:200])
        _w(client, _REL_FILE_CLASS, fid=file_id, cid=cid)
        class_ranges.append((cls.start_line, cls.end_line, cid, cls.name))

    # Function / Method nodes
    for fn in pf.functions:
        fn_id = _fn_id_for(pf, fn, pf.classes)
        _w(client, _MERGE_FN,
           id=fn_id, name=fn.name, path=pf.path,
           start_line=fn.start_line, end_line=fn.end_line,
           signature=fn.source[:200], type=fn.type)

        if fn.type == "method":
            parent_cid = next(
                (cid for cstart, cend, cid, _ in class_ranges
                 if cstart <= fn.start_line <= cend),
                None,
            )
            if parent_cid:
                _w(client, _REL_CLASS_METHOD, cid=parent_cid, fnid=fn_id)
        else:
            _w(client, _REL_FILE_FN, fid=file_id, fnid=fn_id)


# ---------------------------------------------------------------------------
# Relationship resolution (against Neo4j lookup tables)
# ---------------------------------------------------------------------------

def _build_lookups(client: NeoClient) -> tuple[
    dict[str, list[str]],   # name  → [fn_id, ...]
    dict[str, list[str]],   # name  → [class_id, ...]
    dict[str, str],          # path  → file_id
]:
    name_to_fn:    dict[str, list[str]] = {}
    name_to_class: dict[str, list[str]] = {}
    path_to_file:  dict[str, str]       = {}

    for row in client.run(_ALL_FN_IDS):
        name_to_fn.setdefault(row["name"], []).append(row["id"])
    for row in client.run(_ALL_CLASS_IDS):
        name_to_class.setdefault(row["name"], []).append(row["id"])
    for row in client.run(_ALL_FILE_IDS):
        path_to_file[row["path"]] = row["id"]

    return name_to_fn, name_to_class, path_to_file


def resolve_file_relations(
    client: NeoClient,
    pf: ParsedFile,
    name_to_fn:    dict[str, list[str]],
    name_to_class: dict[str, list[str]],
    path_to_file:  dict[str, str],
) -> None:
    """Create CALLS, IMPORTS, and INHERITS edges for one ParsedFile."""
    file_id = path_to_file.get(pf.path)
    if not file_id:
        return

    seen_calls:   set[tuple[str, str]] = set()
    seen_imports: set[tuple[str, str]] = set()

    for fn in pf.functions:
        fn_id = _fn_id_for(pf, fn, pf.classes)
        if not fn_id:
            continue

        # CALLS
        for raw_call in fn.calls:
            callee_name = raw_call.split(".")[-1].strip()
            for callee_id in name_to_fn.get(callee_name, []):
                if callee_id != fn_id and (fn_id, callee_id) not in seen_calls:
                    try:
                        _w(client, _REL_CALLS, aid=fn_id, bid=callee_id)
                    except Exception:
                        pass
                    seen_calls.add((fn_id, callee_id))

    # IMPORTS
    for imp_str in pf.imports:
        top = _import_top_module(imp_str, pf.language)
        if not top:
            continue
        for path, fid in path_to_file.items():
            parts = Path(path).parts
            if parts and parts[0] == top and fid != file_id:
                if (file_id, fid) not in seen_imports:
                    try:
                        _w(client, _REL_IMPORTS, aid=file_id, bid=fid)
                    except Exception:
                        pass
                    seen_imports.add((file_id, fid))
                break

    # INHERITS (Python only)
    if pf.language == "python":
        for cls in pf.classes:
            cid = f"class::{pf.path}::{cls.name}"
            for base_name in _extract_py_bases(cls.source):
                for base_id in name_to_class.get(base_name, []):
                    try:
                        _w(client, _REL_INHERITS, cid=cid, bid=base_id)
                    except Exception:
                        pass


# ---------------------------------------------------------------------------
# Affected module lookup
# ---------------------------------------------------------------------------

def get_affected_modules(client: NeoClient, rel_paths: list[str]) -> list[str]:
    """Return module names that contain any of the given file paths."""
    modules: set[str] = set()
    for path in rel_paths:
        rows = client.run(_MODULE_FOR, path=path)
        for row in rows:
            if row.get("name"):
                modules.add(row["name"])
    return sorted(modules)


# ---------------------------------------------------------------------------
# Core orchestrator
# ---------------------------------------------------------------------------

def update_changed_files(
    repo_path: Path,
    to_update: list[str],
    to_delete: list[str],
    client: NeoClient,
    settings: Settings,
    progress_cb: Any = None,
) -> dict:
    """
    Incrementally update Neo4j for a set of changed files.

    Steps:
      1. Delete stale nodes for to_update + to_delete paths
      2. Parse and re-insert nodes for to_update paths
      3. Rebuild CALLS / IMPORTS / INHERITS for changed files
      4. Re-summarize nodes where summary IS NULL
      5. Re-embed newly summarized nodes

    Args:
        repo_path:   Absolute path to the repo root.
        to_update:   Relative paths of added/modified files.
        to_delete:   Relative paths of deleted files (nodes removed only).
        client:      Connected NeoClient.
        settings:    Project settings.
        progress_cb: Optional callable(step: str, detail: str).

    Returns:
        dict with keys: updated_files, deleted_files,
                        affected_modules, summarized, embedded
    """
    def _cb(step: str, detail: str) -> None:
        if progress_cb:
            progress_cb(step, detail)

    all_changed = to_update + to_delete

    # ── 1. Delete stale nodes ─────────────────────────────────────────────────
    _cb("delete", f"Removing stale nodes for {len(all_changed)} path(s)...")
    for path in all_changed:
        delete_file_nodes(client, path)

    # ── 2. Parse and re-insert changed files ──────────────────────────────────
    parsed_files: list[ParsedFile] = []
    if to_update:
        _cb("parse", f"Re-parsing {len(to_update)} file(s)...")
        parsed_files = parse_files(repo_path, to_update)
        _cb("parse", f"  Parsed {len(parsed_files)} supported file(s).")

        for pf in parsed_files:
            insert_parsed_file(client, pf, repo_path)

    # ── 3. Re-resolve relationships ───────────────────────────────────────────
    if parsed_files:
        _cb("relations", "Re-resolving CALLS / IMPORTS / INHERITS...")
        name_to_fn, name_to_class, path_to_file = _build_lookups(client)
        for pf in parsed_files:
            resolve_file_relations(
                client, pf, name_to_fn, name_to_class, path_to_file
            )

    # ── 4. Re-summarize nodes with no summary ─────────────────────────────────
    _cb("summarize", "Re-summarizing new nodes...")
    try:
        sum_counts = run_summarizer(client=client, settings=settings, batch_size=50)
        total_summarized = sum(sum_counts.values())
        _cb("summarize", f"  Summarized {total_summarized} node(s).")
    except Exception as exc:
        _cb("warn", f"Summarization failed: {exc}")
        total_summarized = 0

    # ── 5. Re-embed newly summarized nodes ────────────────────────────────────
    _cb("embed", "Re-embedding summaries...")
    try:
        emb_counts = run_embedder(client=client, settings=settings, batch_size=50)
        total_embedded = sum(emb_counts.values())
        _cb("embed", f"  Embedded {total_embedded} node(s).")
    except Exception as exc:
        _cb("warn", f"Embedding failed: {exc}")
        total_embedded = 0

    # ── 6. Determine affected modules ─────────────────────────────────────────
    affected_modules = get_affected_modules(client, to_update)

    return {
        "updated_files":     len(parsed_files),
        "deleted_files":     len(to_delete),
        "affected_modules":  affected_modules,
        "summarized":        total_summarized,
        "embedded":          total_embedded,
    }
