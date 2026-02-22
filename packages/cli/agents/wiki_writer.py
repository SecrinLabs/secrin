"""
Wiki Writer Agent.

Queries Neo4j (Modules, Files, Functions, Classes, DomainEntities) and
generates a structured Markdown wiki under a configurable output directory.

File layout:
    <output>/
    ├── README.md
    ├── architecture.md
    ├── domains/<slug>.md   (one per DomainEntity — skipped if none exist)
    └── modules/<slug>.md   (one per Module)

Config from packages.config.settings.Settings:
    LLM_PROVIDER / LLM_MODEL_OLLAMA / ANTHROPIC_API_KEY / GEMINI_API_KEY
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.arc42gen.models.config import LLMConfig
from packages.arc42gen.providers.factory import create_llm_provider
from packages.cli.graph.neo4j_client import NeoClient
from packages.config.settings import Settings

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_PROMPTS = Path(__file__).parent / "prompts"
_MODULE_PROMPT = (_PROMPTS / "module_summary.txt").read_text(encoding="utf-8")
_ARCH_PROMPT   = (_PROMPTS / "arch_overview.txt").read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Cypher queries
# ---------------------------------------------------------------------------

_Q_ALL_MODULES = "MATCH (m:Module) RETURN m.name AS name ORDER BY m.name"

_Q_MODULE_FILES = """
MATCH (m:Module {name: $mn})-[:CONTAINS]->(f:File)
RETURN f.name AS name, f.path AS path, f.summary AS summary
ORDER BY f.path
"""

_Q_MODULE_CLASSES = """
MATCH (m:Module {name: $mn})-[:CONTAINS]->(f:File)-[:DEFINES]->(c:Class)
RETURN c.id AS id, c.name AS name, c.path AS path,
       c.summary AS summary, c.start_line AS start_line
ORDER BY c.path, c.start_line
"""

_Q_MODULE_FUNCTIONS = """
MATCH (m:Module {name: $mn})-[:CONTAINS]->(f:File)-[:DEFINES]->(fn:Function)
RETURN fn.name AS name, fn.path AS path,
       fn.summary AS summary, fn.start_line AS start_line
ORDER BY fn.path, fn.start_line
"""

_Q_MODULE_METHODS = """
MATCH (m:Module {name: $mn})-[:CONTAINS]->(f:File)
      -[:DEFINES]->(c:Class)-[:CONTAINS]->(fn:Function)
RETURN fn.name AS name, fn.start_line AS start_line, c.name AS class_name
ORDER BY fn.path, fn.start_line
"""

_Q_MODULE_DOMAINS = """
MATCH (m:Module {name: $mn})-[:CONTAINS]->(f:File)
      -[:IMPLEMENTS_DOMAIN]->(d:DomainEntity)
RETURN d.id AS id, d.name AS name, d.subdomain AS subdomain
UNION
MATCH (m:Module {name: $mn})-[:CONTAINS]->(f:File)
      -[:DEFINES]->(n)-[:IMPLEMENTS_DOMAIN]->(d:DomainEntity)
RETURN d.id AS id, d.name AS name, d.subdomain AS subdomain
UNION
MATCH (m:Module {name: $mn})-[:CONTAINS]->(f:File)
      -[:DEFINES]->(c:Class)-[:CONTAINS]->(n)-[:IMPLEMENTS_DOMAIN]->(d:DomainEntity)
RETURN d.id AS id, d.name AS name, d.subdomain AS subdomain
"""

_Q_MODULE_IMPORTS = """
MATCH (m:Module {name: $mn})-[:CONTAINS]->(f:File)-[:IMPORTS]->(dep:File)
MATCH (dep_mod:Module)-[:CONTAINS]->(dep)
WHERE dep_mod.name <> $mn
RETURN DISTINCT dep_mod.name AS module_name
ORDER BY dep_mod.name
"""

_Q_MODULE_IMPORTED_BY = """
MATCH (m:Module {name: $mn})-[:CONTAINS]->(f:File)
MATCH (importer:File)-[:IMPORTS]->(f)
MATCH (imp_mod:Module)-[:CONTAINS]->(importer)
WHERE imp_mod.name <> $mn
RETURN DISTINCT imp_mod.name AS module_name
ORDER BY imp_mod.name
"""

_Q_MODULE_CALL_GRAPH = """
MATCH (m:Module {name: $mn})-[:CONTAINS]->(f:File)
      -[:DEFINES]->(caller:Function)-[:CALLS]->(callee:Function)
RETURN DISTINCT caller.name AS caller, callee.name AS callee
"""

_Q_ALL_DOMAINS = """
MATCH (d:DomainEntity)
RETURN d.id AS id, d.name AS name,
       d.description AS description, d.subdomain AS subdomain
ORDER BY d.subdomain, d.name
"""

_Q_DOMAIN_IMPLEMENTORS = """
MATCH (n)-[:IMPLEMENTS_DOMAIN]->(d:DomainEntity {id: $domain_id})
RETURN n.name AS name, n.path AS path,
       n.summary AS summary, labels(n)[0] AS label
ORDER BY label, n.path, n.name
"""

_Q_IMPORT_GRAPH = """
MATCH (ma:Module)-[:CONTAINS]->(fa:File)-[:IMPORTS]->(fb:File)
MATCH (mb:Module)-[:CONTAINS]->(fb)
WHERE ma.name <> mb.name
RETURN DISTINCT ma.name AS source, mb.name AS target
ORDER BY source, target
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GEN_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "unnamed"


def _mermaid_id(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

def _build_llm(settings: Settings) -> Any:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "ollama":
        cfg = LLMConfig(
            provider="ollama", model=settings.LLM_MODEL_OLLAMA,
            api_key="", base_url=settings.OLLAMA_BASE_URL, max_tokens=500,
        )
    elif provider == "anthropic":
        cfg = LLMConfig(
            provider="anthropic", model=LLMConfig.DEFAULT_MODELS["anthropic"],
            api_key=settings.ANTHROPIC_API_KEY, max_tokens=500,
        )
    elif provider == "gemini":
        cfg = LLMConfig(
            provider="gemini", model=LLMConfig.DEFAULT_MODELS["gemini"],
            api_key=settings.GEMINI_API_KEY, max_tokens=500,
        )
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER '{provider}'")
    return create_llm_provider(cfg)


def _llm_call(llm: Any, template: str, **kwargs: str) -> str:
    """Substitute {placeholders} via str.replace() then call LLM."""
    prompt = template
    for key, val in kwargs.items():
        prompt = prompt.replace("{" + key + "}", val)
    try:
        return llm.generate(prompt=prompt, temperature=0.2).content.strip()
    except Exception as exc:
        return f"*(summary unavailable: {exc})*"


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def _fetch_module(client: NeoClient, module_name: str) -> dict:
    files     = client.run(_Q_MODULE_FILES,      mn=module_name)
    classes   = client.run(_Q_MODULE_CLASSES,    mn=module_name)
    functions = client.run(_Q_MODULE_FUNCTIONS,  mn=module_name)
    raw_methods  = client.run(_Q_MODULE_METHODS, mn=module_name)
    domains   = client.run(_Q_MODULE_DOMAINS,    mn=module_name)
    imports   = client.run(_Q_MODULE_IMPORTS,    mn=module_name)
    imp_by    = client.run(_Q_MODULE_IMPORTED_BY, mn=module_name)
    call_graph = client.run(_Q_MODULE_CALL_GRAPH, mn=module_name)

    # Deduplicate domain rows (UNION is already distinct, but be safe)
    seen: dict[str, dict] = {}
    for d in domains:
        if d.get("id") and d["id"] not in seen:
            seen[d["id"]] = d

    # Group method names by class
    methods_by_class: dict[str, list[str]] = {}
    for m in raw_methods:
        methods_by_class.setdefault(m["class_name"], []).append(m["name"])

    return {
        "name":             module_name,
        "files":            files,
        "classes":          classes,
        "functions":        functions,
        "methods_by_class": methods_by_class,
        "domains":          list(seen.values()),
        "imports_from":     [r["module_name"] for r in imports],
        "imported_by":      [r["module_name"] for r in imp_by],
        "call_graph":       call_graph[:25],
    }


# ---------------------------------------------------------------------------
# Mermaid helpers
# ---------------------------------------------------------------------------

def _mermaid_calls(call_graph: list[dict]) -> str:
    if not call_graph:
        return ""
    lines = ["```mermaid", "flowchart LR"]
    seen: set[tuple[str, str]] = set()
    for edge in call_graph:
        src, dst = _mermaid_id(edge["caller"]), _mermaid_id(edge["callee"])
        if (src, dst) not in seen:
            lines.append(f"    {src} --> {dst}")
            seen.add((src, dst))
    lines.append("```")
    return "\n".join(lines)


def _mermaid_imports(import_graph: list[dict]) -> str:
    if not import_graph:
        return "_No cross-module import relationships found._"
    lines = ["```mermaid", "flowchart LR"]
    seen: set[tuple[str, str]] = set()
    for edge in import_graph:
        src = _mermaid_id(edge["source"])
        dst = _mermaid_id(edge["target"])
        if (src, dst) not in seen:
            lines.append(
                f'    {src}["{edge["source"]}"] --> {dst}["{edge["target"]}"]'
            )
            seen.add((src, dst))
    lines.append("```")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Markdown renderers
# ---------------------------------------------------------------------------

def _render_module_md(data: dict, summary: str) -> str:
    name = data["name"]
    out: list[str] = []

    out.append(f"# Module: `{name}`\n")
    out.append(f"> Auto-generated by Secrin · {_GEN_DATE}\n")
    out.append(f"{summary}\n")

    # Domain concepts
    if data["domains"]:
        out.append("## Domain Concepts\n")
        for d in data["domains"]:
            d_slug = _slug(d["name"])
            out.append(
                f"- [{d['name']}](../domains/{d_slug}.md)"
                f" *(_{d.get('subdomain', '?')}_)*"
            )
        out.append("")

    # Dependencies
    if data["imports_from"] or data["imported_by"]:
        out.append("## Dependencies\n")
        if data["imports_from"]:
            links = [f"[{m}](../modules/{_slug(m)}.md)" for m in data["imports_from"]]
            out.append(f"**Imports from:** {', '.join(links)}\n")
        if data["imported_by"]:
            links = [f"[{m}](../modules/{_slug(m)}.md)" for m in data["imported_by"]]
            out.append(f"**Imported by:** {', '.join(links)}\n")

    # Classes
    if data["classes"]:
        out.append("## Classes\n")
        for cls in data["classes"]:
            loc = (
                f"{cls['path']}:{cls['start_line']}"
                if cls.get("start_line")
                else cls.get("path", "")
            )
            out.append(f"### `{cls['name']}` — `{loc}`\n")
            if cls.get("summary"):
                out.append(f"{cls['summary']}\n")
            methods = data["methods_by_class"].get(cls["name"], [])
            if methods:
                names = ", ".join(f"`{m}`" for m in methods[:8])
                suffix = f" *(+{len(methods) - 8} more)*" if len(methods) > 8 else ""
                out.append(f"**Methods:** {names}{suffix}\n")

    # Functions
    if data["functions"]:
        out.append("## Functions\n")
        for fn in data["functions"][:30]:
            loc = (
                f"{fn['path']}:{fn['start_line']}"
                if fn.get("start_line")
                else fn.get("path", "")
            )
            summary_text = (fn.get("summary") or "*(no summary)*").replace("\n", " ")
            out.append(f"- **`{fn['name']}`** — `{loc}` — {summary_text}")
        if len(data["functions"]) > 30:
            out.append(f"\n*({len(data['functions']) - 30} more functions not shown)*")
        out.append("")

    # Call graph
    mermaid = _mermaid_calls(data["call_graph"])
    if mermaid:
        out.append("## Call Graph\n")
        out.append(mermaid)
        out.append("")

    return "\n".join(out)


def _render_domain_md(domain: dict, implementors: list[dict]) -> str:
    name = domain["name"]
    out: list[str] = []

    out.append(f"# Domain: {name}\n")
    out.append(f"> Auto-generated by Secrin · {_GEN_DATE}\n")
    out.append(f"**Subdomain:** {domain.get('subdomain', '?')}\n")
    if domain.get("description"):
        out.append(f"{domain['description']}\n")

    if not implementors:
        out.append("_No implementing code nodes linked yet._\n")
        out.append(
            "_Run `secrin domains` to link code nodes to domain entities._\n"
        )
        return "\n".join(out)

    by_label: dict[str, list[dict]] = {}
    for node in implementors:
        by_label.setdefault(node["label"], []).append(node)

    for label in ("Function", "Class", "File"):
        nodes = by_label.get(label, [])
        if not nodes:
            continue
        out.append(f"## {label}s\n")
        for n in nodes:
            path = n.get("path", "")
            parts = Path(path).parts if path else ()
            module_name = parts[0] if parts else ""
            if module_name:
                link = f"[`{path}`](../modules/{_slug(module_name)}.md)"
            else:
                link = f"`{path}`" if path else "*(unknown)*"
            summary_text = (n.get("summary") or "").replace("\n", " ")
            out.append(f"- **`{n['name']}`** — {link}")
            if summary_text:
                out.append(f"  _{summary_text}_")
        out.append("")

    return "\n".join(out)


def _render_architecture_md(
    modules_data: list[dict],
    domains: list[dict],
    import_graph: list[dict],
    overview: str,
) -> str:
    out: list[str] = []

    out.append("# Architecture Overview\n")
    out.append(f"> Auto-generated by Secrin · {_GEN_DATE}\n")
    out.append(f"{overview}\n")

    # Module dependency diagram
    out.append("## Module Dependency Graph\n")
    out.append(_mermaid_imports(import_graph))
    out.append("")

    # Domain map table
    if domains:
        out.append("## Domain Map\n")
        out.append("| Domain | Subdomain | Modules |")
        out.append("|--------|-----------|---------|")

        # Build domain_id → module names from fetched module data
        domain_modules: dict[str, set[str]] = {}
        for mod in modules_data:
            for d in mod.get("domains", []):
                domain_modules.setdefault(d["id"], set()).add(mod["name"])

        for d in domains:
            module_names = sorted(domain_modules.get(d["id"], set()))
            links = [f"[{m}](modules/{_slug(m)}.md)" for m in module_names]
            d_slug = _slug(d["name"])
            out.append(
                f"| [{d['name']}](domains/{d_slug}.md)"
                f" | {d.get('subdomain', '?')}"
                f" | {', '.join(links) or '—'} |"
            )
        out.append("")

    # Module list
    out.append("## Modules\n")
    for mod in sorted(modules_data, key=lambda m: m["name"]):
        slug = _slug(mod["name"])
        out.append(
            f"- [`{mod['name']}`](modules/{slug}.md)"
            f" — {len(mod['files'])} file(s),"
            f" {len(mod['functions'])} function(s),"
            f" {len(mod['classes'])} class(es)"
        )
    out.append("")

    return "\n".join(out)


def _render_readme(modules_data: list[dict], domains: list[dict]) -> str:
    out: list[str] = []

    out.append("# Codebase Wiki\n")
    out.append(f"> Auto-generated by Secrin · {_GEN_DATE}\n")
    out.append(
        "This wiki is generated from the live code graph. "
        "Start with [architecture.md](architecture.md) for the system overview.\n"
    )

    out.append("## Modules\n")
    for mod in sorted(modules_data, key=lambda m: m["name"]):
        slug = _slug(mod["name"])
        domain_tags = " · ".join(
            f"_{d['name']}_" for d in mod.get("domains", [])[:3]
        )
        out.append(
            f"- [`{mod['name']}`](modules/{slug}.md)"
            + (f" — {domain_tags}" if domain_tags else "")
        )
    out.append("")

    if domains:
        out.append("## Domain Concepts\n")
        for d in domains:
            slug = _slug(d["name"])
            desc = f" — {d['description']}" if d.get("description") else ""
            out.append(
                f"- [{d['name']}](domains/{slug}.md)"
                f" *(_{d.get('subdomain', '?')}_)*{desc}"
            )
        out.append("")

    out.append("---\n")
    out.append(
        "_[Architecture Overview](architecture.md)"
        " · Generated by `secrin generate`_\n"
    )

    return "\n".join(out)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_wiki_writer(
    client: NeoClient,
    settings: Settings,
    output_dir: Path,
    skip_llm: bool = False,
    progress_cb: Any = None,
) -> dict:
    """
    Generate a full Markdown wiki from the Neo4j knowledge graph.

    Args:
        client:      Connected NeoClient.
        settings:    Project settings (LLM + Neo4j config).
        output_dir:  Directory to write wiki files into (created if needed).
        skip_llm:    Skip LLM narrative summaries; use raw node summaries only.
        progress_cb: Optional callable(step: str, detail: str).

    Returns:
        dict with keys: files_written, modules, domains, output_dir
    """
    def _cb(step: str, detail: str) -> None:
        if progress_cb:
            progress_cb(step, detail)

    output_dir = Path(output_dir)
    (output_dir / "modules").mkdir(parents=True, exist_ok=True)
    (output_dir / "domains").mkdir(parents=True, exist_ok=True)

    llm = None if skip_llm else _build_llm(settings)

    # ── 1. Modules ─────────────────────────────────────────────────────────────
    module_rows = client.run(_Q_ALL_MODULES)
    if not module_rows:
        raise ValueError("No modules found. Run `secrin graph build` first.")

    _cb("fetch", f"Found {len(module_rows)} modules.")
    modules_data: list[dict] = []

    for row in module_rows:
        mn = row["name"]
        _cb("module", f"  {mn}")
        data = _fetch_module(client, mn)

        # Build LLM module summary
        if llm and (data["classes"] or data["functions"]):
            snippets: list[str] = []
            for cls in data["classes"][:8]:
                if cls.get("summary"):
                    snippets.append(f"Class {cls['name']}: {cls['summary']}")
            for fn in data["functions"][:10]:
                if fn.get("summary"):
                    snippets.append(f"Function {fn['name']}: {fn['summary']}")
            if snippets:
                summary = _llm_call(
                    llm, _MODULE_PROMPT,
                    module_name=mn,
                    file_count=str(len(data["files"])),
                    node_summaries="\n".join(snippets[:15]),
                )
            else:
                summary = f"*The `{mn}` module contains {len(data['files'])} file(s).*"
        else:
            summary = f"*The `{mn}` module contains {len(data['files'])} file(s).*"

        data["summary"] = summary
        modules_data.append(data)

        md = _render_module_md(data, summary)
        (output_dir / "modules" / f"{_slug(mn)}.md").write_text(md, encoding="utf-8")

    # ── 2. Domains ─────────────────────────────────────────────────────────────
    domains = client.run(_Q_ALL_DOMAINS)
    _cb("fetch", f"Found {len(domains)} domain entities.")

    for d in domains:
        implementors = client.run(_Q_DOMAIN_IMPLEMENTORS, domain_id=d["id"])
        md = _render_domain_md(d, implementors)
        (output_dir / "domains" / f"{_slug(d['name'])}.md").write_text(
            md, encoding="utf-8"
        )

    # ── 3. Architecture overview ────────────────────────────────────────────────
    import_graph = client.run(_Q_IMPORT_GRAPH)
    _cb("fetch", f"Import graph: {len(import_graph)} cross-module edges.")

    if llm and domains:
        domain_descs = "\n".join(
            f"- {d['name']} ({d.get('subdomain', '?')}): {d.get('description', '')}"
            for d in domains
        )
        overview = _llm_call(llm, _ARCH_PROMPT, domain_descriptions=domain_descs)
    else:
        names = ", ".join(m["name"] for m in modules_data[:8])
        overflow = f" and {len(modules_data) - 8} more" if len(modules_data) > 8 else ""
        overview = (
            f"This codebase is organized into {len(modules_data)} module(s): "
            f"{names}{overflow}."
        )

    arch_md = _render_architecture_md(modules_data, domains, import_graph, overview)
    (output_dir / "architecture.md").write_text(arch_md, encoding="utf-8")

    # ── 4. README ──────────────────────────────────────────────────────────────
    readme_md = _render_readme(modules_data, domains)
    (output_dir / "README.md").write_text(readme_md, encoding="utf-8")

    files_written = len(modules_data) + len(domains) + 2  # +architecture +README
    _cb("done", f"Wrote {files_written} files to {output_dir}/")

    return {
        "files_written": files_written,
        "modules":       len(modules_data),
        "domains":       len(domains),
        "output_dir":    str(output_dir.resolve()),
    }
