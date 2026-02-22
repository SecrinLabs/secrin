"""
Analyses list[ParsedFile] and groups them into semantic Module objects.

Steps:
  1. Group files by top-level directory (or filename prefix for flat structures).
  2. Merge modules that are too small (< 2 files AND < 5 nodes) into __misc__.
  3. For each module: find entry points, key nodes, decisions, cross-module deps.
  4. Topological sort: least-dependent modules first.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path

from .parser import ParsedFile, ParsedNode

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

DECISION_KEYWORDS = frozenset(["NOTE:", "WHY:", "DECISION:", "HACK:", "TODO:", "FIXME:"])


@dataclass
class Module:
    name: str                    # Human-readable: "Arc42gen", "CLI", "Config"
    files: list[str]             # Relative file paths belonging to this module
    key_nodes: list[ParsedNode]  # Top 10 most-called nodes
    imports_from: list[str]      # Display names of modules this one imports from
    exported_to: list[str]       # Display names of modules that import from this one
    entry_points: list[str]      # Function/class names with no callers in this module
    decisions: list[str]         # Decision-relevant top-level comments


# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------

_DISPLAY_OVERRIDES: dict[str, str] = {
    "cli": "CLI",
    "api": "API",
}


def _display_name(folder_key: str) -> str:
    """
    'arc42gen'   → 'Arc42gen'
    'cli'        → 'CLI'
    '__misc__'   → 'Misc'
    '__root__'   → 'Root'
    """
    stripped = folder_key.strip("_")
    if not stripped:
        return "Root"
    lower = stripped.lower()
    if lower in _DISPLAY_OVERRIDES:
        return _DISPLAY_OVERRIDES[lower]
    return stripped.replace("_", " ").replace("-", " ").title()


# ---------------------------------------------------------------------------
# Step 1 — grouping
# ---------------------------------------------------------------------------

def _group_by_first_dir(parsed_files: list[ParsedFile]) -> dict[str, list[ParsedFile]]:
    groups: dict[str, list[ParsedFile]] = defaultdict(list)
    for pf in parsed_files:
        parts = Path(pf.path).parts
        if len(parts) > 1:
            key = parts[0]
        else:
            stem = Path(pf.path).stem
            # Use prefix before first separator as a pseudo-module key
            for sep in ("_", "-"):
                if sep in stem:
                    key = stem.split(sep)[0]
                    break
            else:
                key = "__root__" if stem in ("__init__", "main", "setup", "conftest", "manage") else stem
        groups[key].append(pf)
    return dict(groups)


def _merge_small_modules(groups: dict[str, list[ParsedFile]]) -> dict[str, list[ParsedFile]]:
    """Merge modules with < 2 files AND < 5 total nodes into __misc__."""
    small: list[str] = [
        k for k, files in groups.items()
        if len(files) < 2 and sum(len(f.functions) + len(f.classes) for f in files) < 5
    ]
    if not small:
        return groups

    result = {k: v for k, v in groups.items() if k not in small}
    misc: list[ParsedFile] = []
    for k in small:
        misc.extend(groups[k])

    if misc:
        result.setdefault("__misc__", []).extend(misc)
    return result


# ---------------------------------------------------------------------------
# Step 2 — per-module analysis
# ---------------------------------------------------------------------------

def _all_nodes(files: list[ParsedFile]) -> list[ParsedNode]:
    nodes: list[ParsedNode] = []
    for pf in files:
        nodes.extend(pf.functions)
        nodes.extend(pf.classes)
    return nodes


_DUNDER_SKIP = frozenset({
    "__init__", "__new__", "__repr__", "__str__", "__eq__",
    "__hash__", "__len__", "__iter__", "<anonymous>",
})


def _find_entry_points(files: list[ParsedFile]) -> list[str]:
    """
    Entry points = functions/classes defined in the module but never called
    by any other function/class within the same module.
    """
    all_names: set[str] = {
        node.name
        for pf in files
        for node in pf.functions + pf.classes
        if node.name and node.name not in _DUNDER_SKIP
    }

    called: set[str] = set()
    for pf in files:
        for node in pf.functions + pf.classes:
            for call in node.calls:
                called.add(call)
                called.add(call.split(".")[-1])

    return sorted(all_names - called - _DUNDER_SKIP)


def _find_key_nodes(files: list[ParsedFile]) -> list[ParsedNode]:
    """Top 10 nodes sorted by how many times they appear in other nodes' call lists."""
    freq: dict[str, int] = defaultdict(int)
    for pf in files:
        for node in pf.functions + pf.classes:
            for call in node.calls:
                freq[call] += 1
                freq[call.split(".")[-1]] += 1

    all_n = _all_nodes(files)
    all_n.sort(key=lambda n: freq.get(n.name, 0), reverse=True)
    return all_n[:10]


def _extract_decisions(files: list[ParsedFile]) -> list[str]:
    """Decision-relevant top-level comments (NOTE:, WHY:, DECISION:, HACK:, TODO:)."""
    result: list[str] = []
    for pf in files:
        for comment in pf.top_level_comments:
            if any(kw in comment.upper() for kw in DECISION_KEYWORDS):
                result.append(f"[{pf.path}] {comment.strip()}")
    return result


def _find_imports_from(
    files: list[ParsedFile], all_keys: set[str], self_key: str
) -> list[str]:
    """
    Which other folder-keys does this module import from?
    Matches import path segments against known module folder keys.
    Self-imports are excluded.
    """
    referenced: set[str] = set()
    for pf in files:
        for imp in pf.imports:
            tokens = imp.split()
            if not tokens:
                continue
            module_path = ""
            if tokens[0] == "from" and len(tokens) > 1:
                module_path = tokens[1]
            elif tokens[0] == "import" and len(tokens) > 1:
                module_path = tokens[1]

            if not module_path or module_path.startswith("."):
                continue

            for part in module_path.split("."):
                if part in all_keys and part != self_key:
                    referenced.add(part)
    return sorted(referenced)


# ---------------------------------------------------------------------------
# Step 3 — topological sort
# ---------------------------------------------------------------------------

def _topological_sort(keys: list[str], deps: dict[str, list[str]]) -> list[str]:
    """Kahn's algorithm. Modules with fewest dependencies come first."""
    in_degree: dict[str, int] = {k: 0 for k in keys}
    out_edges: dict[str, set[str]] = {k: set() for k in keys}

    for module, module_deps in deps.items():
        for dep in module_deps:
            if dep in out_edges and dep != module:  # skip self-loops
                out_edges[dep].add(module)
                in_degree[module] += 1

    queue = deque(sorted(k for k, d in in_degree.items() if d == 0))
    result: list[str] = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in sorted(out_edges[node]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Append any remaining (handles cycles)
    result.extend(k for k in sorted(keys) if k not in result)
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyse(parsed_files: list[ParsedFile]) -> list[Module]:
    """
    Group parsed files into Modules and enrich each with structural metadata.

    Returns list[Module] sorted least-dependent-first (dependencies before
    the modules that depend on them).
    """
    # Step 1
    groups = _group_by_first_dir(parsed_files)
    groups = _merge_small_modules(groups)

    all_keys = set(groups.keys())
    name_to_key = {_display_name(k): k for k in all_keys}

    # Step 2 — build raw modules
    raw: dict[str, Module] = {}
    for key, files in groups.items():
        imp_keys = _find_imports_from(files, all_keys, self_key=key)
        raw[key] = Module(
            name=_display_name(key),
            files=[pf.path for pf in files],
            key_nodes=_find_key_nodes(files),
            imports_from=[_display_name(k) for k in imp_keys],
            exported_to=[],
            entry_points=_find_entry_points(files),
            decisions=_extract_decisions(files),
        )

    # Fill exported_to (reverse lookup)
    for key, mod in raw.items():
        for dep_name in mod.imports_from:
            dep_key = name_to_key.get(dep_name)
            if dep_key and dep_key in raw:
                dep_mod = raw[dep_key]
                if mod.name not in dep_mod.exported_to:
                    dep_mod.exported_to.append(mod.name)

    # Step 3 — topological sort
    deps_by_key: dict[str, list[str]] = {
        key: [name_to_key[name] for name in mod.imports_from if name in name_to_key]
        for key, mod in raw.items()
    }
    sorted_keys = _topological_sort(list(groups.keys()), deps_by_key)
    return [raw[k] for k in sorted_keys if k in raw]
