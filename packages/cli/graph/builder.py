"""
Neo4j graph builder.

Orchestrates: parse_repo → build node/edge lists → batch-MERGE into Neo4j.

Node IDs:
    file::{path}                         relative path from repo root
    module::{name}                       first directory component (or __root__)
    class::{path}::{name}               file-path + class name
    function::{path}::{name}            top-level functions
    function::{path}::{ClassName}.{name} methods (disambiguates same-name methods)
"""
from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Any

from packages.cli.core.parser import parse_repo, ParsedFile, ParsedNode
from packages.cli.graph.neo4j_client import NeoClient

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BATCH_SIZE = 500


# ---------------------------------------------------------------------------
# Cypher templates — UNWIND-based batch upserts
# ---------------------------------------------------------------------------

_MERGE_FILES = """
UNWIND $rows AS row
MERGE (f:File {id: row.id})
SET f.path = row.path,
    f.name = row.name,
    f.extension = row.extension,
    f.size = row.size
"""

_MERGE_MODULES = """
UNWIND $rows AS row
MERGE (m:Module {id: row.id})
SET m.name = row.name, m.path = row.path
"""

_MERGE_CLASSES = """
UNWIND $rows AS row
MERGE (c:Class {id: row.id})
SET c.name = row.name,
    c.path = row.path,
    c.start_line = row.start_line,
    c.end_line = row.end_line,
    c.signature = row.signature
"""

_MERGE_FUNCTIONS = """
UNWIND $rows AS row
MERGE (fn:Function {id: row.id})
SET fn.name = row.name,
    fn.path = row.path,
    fn.start_line = row.start_line,
    fn.end_line = row.end_line,
    fn.signature = row.signature,
    fn.type = row.type
"""

_REL_MODULE_CONTAINS_FILE = """
UNWIND $rows AS row
MATCH (m:Module {id: row.module_id})
MATCH (f:File   {id: row.file_id})
MERGE (m)-[:CONTAINS]->(f)
"""

_REL_FILE_DEFINES_CLASS = """
UNWIND $rows AS row
MATCH (f:File  {id: row.file_id})
MATCH (c:Class {id: row.class_id})
MERGE (f)-[:DEFINES]->(c)
"""

_REL_FILE_DEFINES_FN = """
UNWIND $rows AS row
MATCH (f:File     {id: row.file_id})
MATCH (fn:Function {id: row.fn_id})
MERGE (f)-[:DEFINES]->(fn)
"""

_REL_CLASS_CONTAINS_METHOD = """
UNWIND $rows AS row
MATCH (c:Class    {id: row.class_id})
MATCH (fn:Function {id: row.fn_id})
MERGE (c)-[:CONTAINS]->(fn)
"""

_REL_CLASS_INHERITS = """
UNWIND $rows AS row
MATCH (c:Class    {id: row.class_id})
MATCH (b:Class    {id: row.base_id})
MERGE (c)-[:INHERITS]->(b)
"""

_REL_FN_CALLS_FN = """
UNWIND $rows AS row
MATCH (a:Function {id: row.caller_id})
MATCH (b:Function {id: row.callee_id})
MERGE (a)-[:CALLS]->(b)
"""

_REL_FILE_IMPORTS_FILE = """
UNWIND $rows AS row
MATCH (a:File {id: row.from_id})
MATCH (b:File {id: row.to_id})
MERGE (a)-[:IMPORTS]->(b)
"""


# ---------------------------------------------------------------------------
# Batch write helper
# ---------------------------------------------------------------------------

def _batch_write(client: NeoClient, cypher: str, rows: list[dict]) -> None:
    """Execute a Cypher statement for each chunk of rows."""
    if not rows:
        return

    def _write(tx: Any, batch: list[dict]) -> None:
        tx.run(cypher, rows=batch)

    with client.driver.session() as session:
        for i in range(0, len(rows), _BATCH_SIZE):
            batch = rows[i : i + _BATCH_SIZE]
            session.execute_write(_write, batch)


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _extract_py_bases(source: str) -> list[str]:
    """Return base-class short names from a Python class source snippet."""
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                names: list[str] = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        names.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        names.append(base.attr)
                return names
    except Exception:
        pass
    return []


def _import_top_module(import_str: str, language: str) -> str | None:
    """
    Extract the top-level module name from a raw import string.
    Python: 'from foo.bar import baz' → 'foo'
            'import foo.bar'          → 'foo'
    JS/TS:  "import ... from './foo'" → 'foo' (strip ./ ../ and extension)
            "import ... from 'react'" → 'react'
    """
    if language == "python":
        m = re.match(r"from\s+([\w.]+)\s+import", import_str)
        if m:
            return m.group(1).split(".")[0]
        m = re.match(r"import\s+([\w.]+)", import_str)
        if m:
            return m.group(1).split(".")[0]
    else:
        # JS/TS: look for the quoted module path
        m = re.search(r"""from\s+['"]([^'"]+)['"]""", import_str)
        if m:
            raw = m.group(1)
            # Strip leading ./ ../
            raw = re.sub(r"^(\.\.?/)+", "", raw)
            # Strip extension
            raw = re.sub(r"\.[jt]sx?$", "", raw)
            return raw.split("/")[0] if raw else None
    return None


# ---------------------------------------------------------------------------
# Core build function
# ---------------------------------------------------------------------------

def build_graph(repo_path: Path, client: NeoClient) -> dict:
    """
    Parse repo_path and populate the connected Neo4j instance.

    Steps:
      1. Parse all source files with tree-sitter
      2. Collect node dicts and edge tuples
      3. Batch-MERGE nodes into Neo4j
      4. Batch-MERGE relationships into Neo4j

    Returns a summary dict (same as build_graph_summary).
    """
    print("  Parsing source files...")
    parsed = parse_repo(repo_path)
    print(f"  Parsed {len(parsed)} files\n")

    # -----------------------------------------------------------------------
    # Accumulators
    # -----------------------------------------------------------------------
    file_nodes:     list[dict] = []
    module_nodes:   list[dict] = []
    class_nodes:    list[dict] = []
    function_nodes: list[dict] = []

    module_contains_file:  list[dict] = []
    file_defines_class:    list[dict] = []
    file_defines_fn:       list[dict] = []
    class_contains_method: list[dict] = []
    class_inherits_class:  list[dict] = []
    fn_calls_fn:           list[dict] = []
    file_imports_file:     list[dict] = []

    # Lookup structures for relationship resolution
    name_to_fn_ids:    dict[str, list[str]] = {}   # fn/method name  → [fn_id]
    name_to_class_ids: dict[str, list[str]] = {}   # class name      → [class_id]
    path_to_file_id:   dict[str, str] = {}          # rel path        → file_id

    seen_modules: set[str] = set()

    # -----------------------------------------------------------------------
    # Pass 1 — collect nodes
    # -----------------------------------------------------------------------
    for pf in parsed:
        # ── File ──────────────────────────────────────────────────────────
        file_id = f"file::{pf.path}"
        path_to_file_id[pf.path] = file_id

        abs_path = repo_path / pf.path
        try:
            size = abs_path.stat().st_size
        except OSError:
            size = 0

        file_nodes.append({
            "id":        file_id,
            "path":      pf.path,
            "name":      Path(pf.path).name,
            "extension": Path(pf.path).suffix,
            "size":      size,
        })

        # ── Module ────────────────────────────────────────────────────────
        parts = Path(pf.path).parts
        module_name = parts[0] if len(parts) > 1 else "__root__"
        module_id   = f"module::{module_name}"

        if module_name not in seen_modules:
            seen_modules.add(module_name)
            module_nodes.append({
                "id":   module_id,
                "name": module_name,
                "path": module_name,
            })

        module_contains_file.append({"module_id": module_id, "file_id": file_id})

        # ── Classes ───────────────────────────────────────────────────────
        # Build (start_line, end_line, class_id, class_name) for method resolution
        class_ranges: list[tuple[int, int, str, str]] = []

        for cls in pf.classes:
            class_id = f"class::{pf.path}::{cls.name}"
            class_nodes.append({
                "id":         class_id,
                "name":       cls.name,
                "path":       pf.path,
                "start_line": cls.start_line,
                "end_line":   cls.end_line,
                "signature":  cls.source[:200],
            })
            name_to_class_ids.setdefault(cls.name, []).append(class_id)
            file_defines_class.append({"file_id": file_id, "class_id": class_id})
            class_ranges.append((cls.start_line, cls.end_line, class_id, cls.name))

        # ── Functions / Methods ───────────────────────────────────────────
        for fn in pf.functions:
            if fn.type == "method":
                # Identify parent class by line-range containment
                parent_class_id   = None
                parent_class_name = None
                for cstart, cend, cid, cname in class_ranges:
                    if cstart <= fn.start_line and fn.end_line <= cend:
                        parent_class_id   = cid
                        parent_class_name = cname
                        break

                if parent_class_name:
                    fn_id = f"function::{pf.path}::{parent_class_name}.{fn.name}"
                else:
                    fn_id = f"function::{pf.path}::{fn.name}"

                if parent_class_id:
                    class_contains_method.append({
                        "class_id": parent_class_id,
                        "fn_id":    fn_id,
                    })
            else:
                fn_id = f"function::{pf.path}::{fn.name}"
                file_defines_fn.append({"file_id": file_id, "fn_id": fn_id})

            function_nodes.append({
                "id":         fn_id,
                "name":       fn.name,
                "path":       pf.path,
                "start_line": fn.start_line,
                "end_line":   fn.end_line,
                "signature":  fn.source[:200],
                "type":       fn.type,
            })
            name_to_fn_ids.setdefault(fn.name, []).append(fn_id)

    # -----------------------------------------------------------------------
    # Pass 2 — resolve relationships
    # -----------------------------------------------------------------------

    # INHERITS: Python only (TS/JS class inheritance not parsed)
    for pf in parsed:
        if pf.language != "python":
            continue
        for cls in pf.classes:
            class_id = f"class::{pf.path}::{cls.name}"
            for base_name in _extract_py_bases(cls.source):
                for base_id in name_to_class_ids.get(base_name, []):
                    class_inherits_class.append({
                        "class_id": class_id,
                        "base_id":  base_id,
                    })

    # CALLS: best-effort name resolution (last dotted component)
    seen_calls: set[tuple[str, str]] = set()
    for pf in parsed:
        for fn in pf.functions:
            fn_id = _fn_id_for(pf, fn, pf.classes)
            for raw_call in fn.calls:
                callee_name = raw_call.split(".")[-1].strip()
                if not callee_name:
                    continue
                for callee_id in name_to_fn_ids.get(callee_name, []):
                    if callee_id == fn_id:
                        continue  # no self-loops
                    edge = (fn_id, callee_id)
                    if edge not in seen_calls:
                        seen_calls.add(edge)
                        fn_calls_fn.append({
                            "caller_id": fn_id,
                            "callee_id": callee_id,
                        })

    # IMPORTS: match first path component of import against file paths
    seen_imports: set[tuple[str, str]] = set()
    for pf in parsed:
        file_id = f"file::{pf.path}"
        for imp_str in pf.imports:
            top = _import_top_module(imp_str, pf.language)
            if not top:
                continue
            for candidate_path, candidate_id in path_to_file_id.items():
                cparts = Path(candidate_path).parts
                if cparts and cparts[0] == top and candidate_id != file_id:
                    edge = (file_id, candidate_id)
                    if edge not in seen_imports:
                        seen_imports.add(edge)
                        file_imports_file.append({
                            "from_id": file_id,
                            "to_id":   candidate_id,
                        })
                    break  # one match per import statement is enough

    # -----------------------------------------------------------------------
    # Insert into Neo4j
    # -----------------------------------------------------------------------
    print("  Inserting nodes...")
    _batch_write(client, _MERGE_FILES,     file_nodes)
    _batch_write(client, _MERGE_MODULES,   module_nodes)
    _batch_write(client, _MERGE_CLASSES,   class_nodes)
    _batch_write(client, _MERGE_FUNCTIONS, function_nodes)

    print("  Inserting relationships...")
    _batch_write(client, _REL_MODULE_CONTAINS_FILE,  module_contains_file)
    _batch_write(client, _REL_FILE_DEFINES_CLASS,    file_defines_class)
    _batch_write(client, _REL_FILE_DEFINES_FN,       file_defines_fn)
    _batch_write(client, _REL_CLASS_CONTAINS_METHOD, class_contains_method)
    _batch_write(client, _REL_CLASS_INHERITS,        class_inherits_class)
    _batch_write(client, _REL_FN_CALLS_FN,           fn_calls_fn)
    _batch_write(client, _REL_FILE_IMPORTS_FILE,     file_imports_file)

    return build_graph_summary(client)


# ---------------------------------------------------------------------------
# Helper — reconstruct fn_id the same way as Pass 1
# ---------------------------------------------------------------------------

def _fn_id_for(pf: ParsedFile, fn: ParsedNode, classes: list[ParsedNode]) -> str:
    """Return the node ID that Pass 1 would have assigned to this function."""
    if fn.type != "method":
        return f"function::{pf.path}::{fn.name}"

    for cls in classes:
        if cls.start_line <= fn.start_line and fn.end_line <= cls.end_line:
            return f"function::{pf.path}::{cls.name}.{fn.name}"

    return f"function::{pf.path}::{fn.name}"


# ---------------------------------------------------------------------------
# Summary query
# ---------------------------------------------------------------------------

def build_graph_summary(client: NeoClient) -> dict:
    """Return a dict with node and relationship counts."""
    node_rows = client.run(
        "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY label"
    )
    rel_rows = client.run(
        "MATCH ()-[r]->() RETURN type(r) AS rel_type, count(r) AS cnt ORDER BY rel_type"
    )
    return {
        "nodes": {row["label"]: row["cnt"] for row in node_rows},
        "relationships": {row["rel_type"]: row["cnt"] for row in rel_rows},
    }
