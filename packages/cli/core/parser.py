"""
AST parser for Python, TypeScript, and JavaScript source files.

Uses tree-sitter 0.25 API:
  - Language(binding.language())
  - Parser(language)
  - QueryCursor(Query(language, pattern)).captures(node) -> dict[str, list[Node]]
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python as tspython
import tree_sitter_typescript as tstype
import tree_sitter_javascript as tsjs

# ---------------------------------------------------------------------------
# Language singletons (created once)
# ---------------------------------------------------------------------------

_PY_LANGUAGE = Language(tspython.language())
_TS_LANGUAGE = Language(tstype.language_typescript())
_TSX_LANGUAGE = Language(tstype.language_tsx())
_JS_LANGUAGE = Language(tsjs.language())

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "dist", "build",
    "venv", ".venv", ".secrin", ".mypy_cache", ".pytest_cache",
    "coverage", ".tox", "eggs", ".eggs",
}

SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "jsx",
}


@dataclass
class ParsedNode:
    name: str
    type: str                    # "function" | "class" | "method"
    start_line: int              # 1-based
    end_line: int                # 1-based
    docstring: Optional[str]
    calls: list[str]
    source: str


@dataclass
class ParsedFile:
    path: str                    # relative to repo root
    language: str
    functions: list[ParsedNode]
    classes: list[ParsedNode]
    imports: list[str]
    top_level_comments: list[str]


# ---------------------------------------------------------------------------
# Helpers — shared
# ---------------------------------------------------------------------------

def _decode(b: bytes) -> str:
    return b.decode("utf-8", errors="replace")


def _node_source(node, src: bytes) -> str:
    return _decode(src[node.start_byte : node.end_byte])


# ---------------------------------------------------------------------------
# Python parsing
# ---------------------------------------------------------------------------

def _py_docstring(node, src: bytes) -> Optional[str]:
    """Return the docstring of a function_definition or class_definition node."""
    body = node.child_by_field_name("body")
    if not body:
        return None
    for child in body.children:
        if child.type == "expression_statement":
            # Check if the only child is a string literal
            expr_children = [c for c in child.children if c.type != "comment"]
            if len(expr_children) == 1 and expr_children[0].type == "string":
                raw = _node_source(expr_children[0], src)
                try:
                    return ast.literal_eval(raw)
                except Exception:
                    # Strip quotes manually as fallback
                    for q in ('"""', "'''", '"', "'"):
                        if raw.startswith(q) and raw.endswith(q) and len(raw) > len(q) * 2:
                            return raw[len(q) : -len(q)].strip()
                    return raw.strip()
        elif child.type not in ("comment",):
            # First real statement isn't a string — no docstring
            break
    return None


def _collect_calls_py(node, src: bytes, _depth: int = 0) -> list[str]:
    """Walk node tree collecting call names, skipping nested function/class defs."""
    calls: list[str] = []
    if node.type == "call":
        func_field = node.child_by_field_name("function")
        if func_field:
            calls.append(_node_source(func_field, src))
    for child in node.children:
        # Don't descend into nested function/class definitions
        if child.type in ("function_definition", "class_definition", "decorated_definition"):
            continue
        calls.extend(_collect_calls_py(child, src))
    # Deduplicate while preserving first-occurrence order
    seen: set[str] = set()
    result: list[str] = []
    for c in calls:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


def _py_function_node(node, src: bytes, node_type: str) -> ParsedNode:
    """
    Build a ParsedNode for a function_definition (or decorated_definition
    wrapping one).  node_type is 'function' or 'method'.
    """
    actual = node
    if node.type == "decorated_definition":
        actual = node.child_by_field_name("definition")

    name_node = actual.child_by_field_name("name")
    name = _decode(name_node.text) if name_node else "<anonymous>"

    return ParsedNode(
        name=name,
        type=node_type,
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
        docstring=_py_docstring(actual, src),
        calls=_collect_calls_py(actual, src),
        source=_node_source(node, src),
    )


def _py_class_node(node, src: bytes) -> tuple[ParsedNode, list[ParsedNode]]:
    """
    Build a ParsedNode for a class_definition and extract its methods.
    Returns (class_node, [method_node, ...]).
    """
    actual = node
    if node.type == "decorated_definition":
        actual = node.child_by_field_name("definition")

    name_node = actual.child_by_field_name("name")
    name = _decode(name_node.text) if name_node else "<anonymous>"

    class_node = ParsedNode(
        name=name,
        type="class",
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
        docstring=_py_docstring(actual, src),
        calls=_collect_calls_py(actual, src),
        source=_node_source(node, src),
    )

    methods: list[ParsedNode] = []
    body = actual.child_by_field_name("body")
    if body:
        for child in body.children:
            if child.type == "function_definition":
                methods.append(_py_function_node(child, src, "method"))
            elif child.type == "decorated_definition":
                defn = child.child_by_field_name("definition")
                if defn and defn.type == "function_definition":
                    methods.append(_py_function_node(child, src, "method"))

    return class_node, methods


def _parse_python(rel_path: str, src: bytes) -> ParsedFile:
    parser = Parser(_PY_LANGUAGE)
    tree = parser.parse(src)
    root = tree.root_node

    imports: list[str] = []
    top_level_comments: list[str] = []
    functions: list[ParsedNode] = []
    classes: list[ParsedNode] = []

    for child in root.children:
        t = child.type
        if t in ("import_statement", "import_from_statement"):
            imports.append(_node_source(child, src))
        elif t == "comment":
            top_level_comments.append(_node_source(child, src))
        elif t == "function_definition":
            functions.append(_py_function_node(child, src, "function"))
        elif t == "class_definition":
            cls, methods = _py_class_node(child, src)
            classes.append(cls)
            functions.extend(methods)  # methods also queryable as functions
        elif t == "decorated_definition":
            defn = child.child_by_field_name("definition")
            if defn:
                if defn.type == "function_definition":
                    functions.append(_py_function_node(child, src, "function"))
                elif defn.type == "class_definition":
                    cls, methods = _py_class_node(child, src)
                    classes.append(cls)
                    functions.extend(methods)

    return ParsedFile(
        path=rel_path,
        language="python",
        functions=functions,
        classes=classes,
        imports=imports,
        top_level_comments=top_level_comments,
    )


# ---------------------------------------------------------------------------
# TypeScript / JavaScript parsing
# ---------------------------------------------------------------------------

def _collect_calls_js(node, src: bytes) -> list[str]:
    """Walk node collecting call_expression names, skipping nested fn/class defs."""
    calls: list[str] = []
    if node.type == "call_expression":
        func_field = node.child_by_field_name("function")
        if func_field:
            calls.append(_node_source(func_field, src))
    for child in node.children:
        if child.type in (
            "function_declaration", "class_declaration",
            "arrow_function", "function_expression",
            "function",  # some grammars use this
        ):
            continue
        calls.extend(_collect_calls_js(child, src))
    seen: set[str] = set()
    result: list[str] = []
    for c in calls:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


def _js_function_from_node(node, src: bytes, name: str, node_type: str) -> ParsedNode:
    return ParsedNode(
        name=name,
        type=node_type,
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
        docstring=None,  # JS/TS uses JSDoc which we skip for now
        calls=_collect_calls_js(node, src),
        source=_node_source(node, src),
    )


def _js_class_from_node(node, src: bytes, name: str) -> tuple[ParsedNode, list[ParsedNode]]:
    class_node = ParsedNode(
        name=name,
        type="class",
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
        docstring=None,
        calls=_collect_calls_js(node, src),
        source=_node_source(node, src),
    )

    methods: list[ParsedNode] = []
    body = node.child_by_field_name("body")
    if body:
        for child in body.children:
            if child.type == "method_definition":
                method_name_node = child.child_by_field_name("name")
                method_name = _decode(method_name_node.text) if method_name_node else "<anonymous>"
                methods.append(_js_function_from_node(child, src, method_name, "method"))

    return class_node, methods


def _unwrap_export(node):
    """If node is an export_statement, return its declaration child."""
    if node.type == "export_statement":
        decl = node.child_by_field_name("declaration")
        return decl if decl else node
    return node


def _parse_js_ts(rel_path: str, src: bytes, language: Language, lang_name: str) -> ParsedFile:
    parser = Parser(language)
    tree = parser.parse(src)
    root = tree.root_node

    imports: list[str] = []
    top_level_comments: list[str] = []
    functions: list[ParsedNode] = []
    classes: list[ParsedNode] = []

    for child in root.children:
        inner = _unwrap_export(child)
        t = inner.type

        if t == "import_statement":
            imports.append(_node_source(inner, src))
        elif t in ("comment", "line_comment", "block_comment"):
            top_level_comments.append(_node_source(inner, src))

        elif t == "function_declaration":
            name_node = inner.child_by_field_name("name")
            name = _decode(name_node.text) if name_node else "<anonymous>"
            functions.append(_js_function_from_node(
                child, src, name, "function"  # use outer (with export) for source
            ))

        elif t == "class_declaration":
            name_node = inner.child_by_field_name("name")
            name = _decode(name_node.text) if name_node else "<anonymous>"
            cls, methods = _js_class_from_node(inner, src, name)
            # Patch source to include export keyword if present
            cls = ParsedNode(
                name=cls.name, type=cls.type,
                start_line=child.start_point[0] + 1,
                end_line=child.end_point[0] + 1,
                docstring=cls.docstring,
                calls=cls.calls,
                source=_node_source(child, src),
            )
            classes.append(cls)
            functions.extend(methods)

        elif t == "lexical_declaration":
            # const foo = () => ... or const foo = function() {}
            for decl_child in inner.children:
                if decl_child.type == "variable_declarator":
                    vname_node = decl_child.child_by_field_name("name")
                    vval_node = decl_child.child_by_field_name("value")
                    if vname_node and vval_node and vval_node.type in (
                        "arrow_function", "function_expression"
                    ):
                        vname = _decode(vname_node.text)
                        functions.append(_js_function_from_node(
                            child, src, vname, "function"
                        ))

    return ParsedFile(
        path=rel_path,
        language=lang_name,
        functions=functions,
        classes=classes,
        imports=imports,
        top_level_comments=top_level_comments,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_repo(repo_path: Path) -> list[ParsedFile]:
    """
    Walk repo_path, parse every supported source file with tree-sitter.

    Skips: node_modules, .git, __pycache__, dist, build, venv, .secrin.
    Supported: .py, .ts, .tsx, .js, .jsx

    Prints progress: "  Parsing {relative_path}... {n}/{total}"
    Returns list[ParsedFile].
    """
    # Collect all files first so we know the total
    all_files: list[Path] = []
    for f in sorted(repo_path.rglob("*")):
        if not f.is_file():
            continue
        # Skip blacklisted directories
        parts = set(f.relative_to(repo_path).parts[:-1])
        if parts & SKIP_DIRS:
            continue
        if f.suffix in SUPPORTED_EXTENSIONS:
            all_files.append(f)

    total = len(all_files)
    results: list[ParsedFile] = []

    for n, file_path in enumerate(all_files, start=1):
        rel = str(file_path.relative_to(repo_path))
        suffix = file_path.suffix
        lang = SUPPORTED_EXTENSIONS[suffix]

        print(f"  Parsing {rel}... {n}/{total}")

        try:
            src = file_path.read_bytes()
        except OSError:
            continue

        try:
            if lang == "python":
                pf = _parse_python(rel, src)
            elif lang == "typescript":
                pf = _parse_js_ts(rel, src, _TS_LANGUAGE, "typescript")
            elif lang == "tsx":
                pf = _parse_js_ts(rel, src, _TSX_LANGUAGE, "tsx")
            elif lang in ("javascript", "jsx"):
                pf = _parse_js_ts(rel, src, _JS_LANGUAGE, lang)
            else:
                continue
        except Exception as exc:
            print(f"    [warn] Failed to parse {rel}: {exc}")
            continue

        results.append(pf)

    return results
