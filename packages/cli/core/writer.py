"""
Wiki generator: takes analysed Module objects and calls an LLM to write
markdown files into wiki_path/.

LLM calls use the arc42gen provider system (anthropic | gemini | ollama).
Temperature is ALWAYS 0.1. No exceptions.

Output files:
  overview.md
  modules/{slug}.md   (one per module)
  decisions.md
  flows.md
  _index.md           (programmatic, no LLM)
"""
from __future__ import annotations

import os
import re
import textwrap
from pathlib import Path

from .analyser import Module
from .parser import ParsedFile, ParsedNode

# ---------------------------------------------------------------------------
# Prompt constants
# ---------------------------------------------------------------------------

OVERVIEW_SYSTEM = textwrap.dedent("""\
    You are a senior software engineer writing the overview page of an internal
    engineering wiki for a software project.
    Be specific, technical, and concise. Use actual names from the code.
    Never write filler like "this project aims to" or "the purpose of this system is".
""")

OVERVIEW_PROMPT = textwrap.dedent("""\
    Based on the codebase structure below, write a clear overview covering:

    1. **What this project does** — one paragraph, specific and technical.
    2. **Tech stack** — bullet list of languages, frameworks, key libraries.
    3. **High-level architecture** — how the main modules connect to each other.
    4. **Entry points** — where execution starts (functions/commands/routes).

    Use actual module names, function names, and file paths from the code.
    No generic filler.

    ---
    {context}
""")

MODULE_SYSTEM = textwrap.dedent("""\
    You are a senior software engineer writing a module wiki page for an
    internal engineering wiki.
    Be specific. Reference actual function names, class names, and file paths.
    Do not pad with generic statements.
""")

MODULE_PROMPT = textwrap.dedent("""\
    Write the wiki page for the **{module_name}** module covering:

    1. **Responsibility** — what this module is responsible for (one paragraph).
    2. **Key functions and classes** — what each does, in plain English (bullet list).
       Do not describe *how* they work line-by-line. Describe *what* they do.
    3. **External dependencies** — what external systems or packages this module relies on.
    4. **Internal dependencies** — what other modules import from this one.
    5. **Business rules** — important constraints or rules visible in the code.

    Reference actual names. No filler.

    ---
    {context}
""")

DECISIONS_SYSTEM = textwrap.dedent("""\
    You are extracting architectural decisions from a codebase.
    Identify deliberate choices, constraints, and patterns that imply decisions.
""")

DECISIONS_PROMPT = textwrap.dedent("""\
    Extract architectural decisions from the code and comments below.

    For each decision, use this format:

    ## Decision: <short title>
    **What:** one sentence describing the decision.
    **Why (from code):** evidence from the code or comments.
    **Location:** file or module name.

    Look for:
    - Explicit NOTE:, WHY:, DECISION:, HACK:, TODO: comments
    - Deliberate patterns (retry logic → reliability decision, caching → performance decision)
    - Technology choices visible in imports (FastAPI, SQLAlchemy, Redis, etc.)
    - Structural decisions (monorepo layout, package boundaries)

    ---
    {context}
""")

FLOWS_SYSTEM = textwrap.dedent("""\
    You are tracing execution flows through a software codebase.
    Be precise. Use actual function names from the code.
""")

FLOWS_PROMPT = textwrap.dedent("""\
    Based on the entry points and call graph below, describe the 3-5 most
    important execution flows in this system.

    For each flow, use this format:

    ## Flow: <name>
    **Trigger:** what starts this flow (CLI command / HTTP request / event / etc.)
    **Path:** step-by-step through the main functions (use actual names)
    **End state:** what is produced or changed as a result

    Look for: CLI command execution, request handling, data generation,
    background job processing, initialisation sequences.

    ---
    {context}
""")

# ---------------------------------------------------------------------------
# LLM client
# ---------------------------------------------------------------------------

TEMPERATURE = 0.1
MAX_TOKENS = 4096


def _llm_call(prompt: str, system: str, provider: str, model: str) -> str:
    """
    Single LLM call. Temperature always 0.1.

    Uses arc42gen's provider system so the same providers are available:
    anthropic, gemini, ollama.
    """
    from packages.arc42gen.providers.factory import create_llm_provider
    from packages.arc42gen.models.config import LLMConfig

    # Resolve the API key from environment
    env_vars = {
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "ollama": "",   # uses base_url instead
    }
    env_var = env_vars.get(provider.lower(), "LLM_API_KEY")
    api_key = os.environ.get(env_var, "") if env_var else ""

    if provider.lower() not in ("ollama",) and not api_key:
        raise ValueError(
            f"API key not set. Export {env_var} before running the writer."
        )

    cfg = LLMConfig(
        provider=provider.lower(),
        model=model,
        api_key=api_key,
        max_tokens=MAX_TOKENS,
        base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
    )
    llm = create_llm_provider(cfg)
    response = llm.generate(
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system_prompt=system,
    )
    return response.content


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------

_MAX_SOURCE_CHARS = 600   # per node
_MAX_NODES_IN_CONTEXT = 10
_MAX_README_CHARS = 3000


def _truncate(text: str, limit: int = _MAX_SOURCE_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [{len(text) - limit} chars truncated]"


def _build_overview_context(
    modules: list[Module],
    parsed_files: list[ParsedFile],
    repo_url: str,
) -> str:
    parts: list[str] = []

    # Repo URL
    parts.append(f"Repository: {repo_url}\n")

    # README
    readme_file = next(
        (pf for pf in parsed_files if Path(pf.path).name.lower() in ("readme.md", "readme.rst", "readme.txt")),
        None,
    )
    if readme_file is None:
        # Try to read README from the parsed file paths
        readme_candidates = [pf for pf in parsed_files if "readme" in pf.path.lower()]
        if readme_candidates:
            readme_file = readme_candidates[0]

    if readme_file:
        # parsed_files don't carry raw text; skip README for now
        pass

    # Module overview
    parts.append("## Modules\n")
    for mod in modules:
        parts.append(
            f"- **{mod.name}**: {len(mod.files)} files, "
            f"{sum(1 for _ in mod.entry_points)} entry points"
            + (f"; imports from {', '.join(mod.imports_from)}" if mod.imports_from else "")
        )

    # Entry points across all modules
    parts.append("\n## Entry Points\n")
    shown = 0
    for mod in modules:
        for ep in mod.entry_points[:5]:
            # Find the source of this entry point
            ep_node = _find_node_by_name(ep, parsed_files)
            if ep_node:
                parts.append(
                    f"### `{ep}` ({mod.name})\n```\n{_truncate(ep_node.source, 400)}\n```\n"
                )
                shown += 1
                if shown >= 8:
                    break
        if shown >= 8:
            break

    # All imports (tech stack signal)
    all_imports: list[str] = []
    for pf in parsed_files:
        all_imports.extend(pf.imports)
    # Deduplicate and take a sample
    unique_imports = sorted(set(all_imports))[:60]
    parts.append("\n## Imports Sample\n```\n" + "\n".join(unique_imports) + "\n```\n")

    return "\n".join(parts)


def _find_node_by_name(name: str, parsed_files: list[ParsedFile]) -> ParsedNode | None:
    for pf in parsed_files:
        for node in pf.functions + pf.classes:
            if node.name == name:
                return node
    return None


def _build_module_context(mod: Module, parsed_files: list[ParsedFile]) -> str:
    parts: list[str] = [
        f"Module: {mod.name}\n",
        f"Files: {', '.join(mod.files[:20])}\n",
        f"Imports from: {', '.join(mod.imports_from) or 'none'}\n",
        f"Exported to: {', '.join(mod.exported_to) or 'none'}\n",
        f"Entry points: {', '.join(mod.entry_points[:15]) or 'none'}\n",
    ]

    if mod.decisions:
        parts.append("\n## Decision Comments\n" + "\n".join(mod.decisions))

    # Module-specific imports (unique)
    mod_files_set = set(mod.files)
    mod_imports = sorted({
        imp
        for pf in parsed_files
        if pf.path in mod_files_set
        for imp in pf.imports
    })
    if mod_imports:
        parts.append("\n## Imports\n```\n" + "\n".join(mod_imports[:30]) + "\n```\n")

    parts.append("\n## Key Functions and Classes\n")
    for node in mod.key_nodes[:_MAX_NODES_IN_CONTEXT]:
        parts.append(
            f"### `{node.name}` ({node.type}, lines {node.start_line}–{node.end_line})\n"
            + (f"*{node.docstring}*\n\n" if node.docstring else "")
            + "```\n"
            + _truncate(node.source)
            + "\n```\n"
        )

    return "\n".join(parts)


def _build_decisions_context(modules: list[Module]) -> str:
    parts: list[str] = []

    all_decisions: list[str] = []
    for mod in modules:
        all_decisions.extend(mod.decisions)

    if all_decisions:
        parts.append("## Explicit Decision Comments\n" + "\n".join(all_decisions))

    parts.append("\n## Module Structure (implies architectural decisions)\n")
    for mod in modules:
        parts.append(
            f"- **{mod.name}**: depends on {', '.join(mod.imports_from) or 'nothing'}; "
            f"used by {', '.join(mod.exported_to) or 'nothing'}"
        )

    parts.append("\n## Entry Points\n")
    for mod in modules:
        if mod.entry_points:
            parts.append(f"- {mod.name}: {', '.join(mod.entry_points[:8])}")

    return "\n".join(parts)


def _build_flows_context(modules: list[Module], parsed_files: list[ParsedFile]) -> str:
    parts: list[str] = ["## Entry Points and Their Call Chains (2 levels)\n"]

    shown = 0
    for mod in modules:
        for ep in mod.entry_points[:4]:
            ep_node = _find_node_by_name(ep, parsed_files)
            if not ep_node:
                continue
            # Level 1: direct calls
            level1 = ep_node.calls[:8]
            # Level 2: calls from level-1 nodes
            level2: list[str] = []
            for call_name in level1[:4]:
                simple = call_name.split(".")[-1]
                callee = _find_node_by_name(simple, parsed_files)
                if callee:
                    level2.extend(f"{call_name} → {c}" for c in callee.calls[:4])

            chain = f"  calls: {', '.join(level1)}" if level1 else "  (no calls)"
            deep = "\n  " + "\n  ".join(level2) if level2 else ""
            parts.append(f"### `{ep}` ({mod.name})\n{chain}{deep}\n")
            shown += 1
            if shown >= 12:
                break
        if shown >= 12:
            break

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Slug helper
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_wiki(
    modules: list[Module],
    parsed_files: list[ParsedFile],
    repo_url: str,
    wiki_path: Path,
    provider: str,
    model: str,
) -> list[Path]:
    """
    Generate all wiki files. Returns list of Path objects created.

    Order:
      1. overview.md
      2. modules/{slug}.md  (one per module)
      3. decisions.md
      4. flows.md
      5. _index.md          (programmatic, no LLM)
    """
    wiki_path.mkdir(parents=True, exist_ok=True)
    (wiki_path / "modules").mkdir(exist_ok=True)

    created: list[Path] = []

    # 1 — overview
    print("  Generating overview...")
    ctx = _build_overview_context(modules, parsed_files, repo_url)
    overview_text = _llm_call(
        prompt=OVERVIEW_PROMPT.format(context=ctx),
        system=OVERVIEW_SYSTEM,
        provider=provider,
        model=model,
    )
    overview_path = wiki_path / "overview.md"
    overview_path.write_text(f"# Overview\n\n{overview_text}\n")
    created.append(overview_path)
    print(f"    → {overview_path.name}")

    # 2 — module wikis
    for mod in modules:
        print(f"  Generating {mod.name} module wiki...")
        ctx = _build_module_context(mod, parsed_files)
        mod_text = _llm_call(
            prompt=MODULE_PROMPT.format(module_name=mod.name, context=ctx),
            system=MODULE_SYSTEM,
            provider=provider,
            model=model,
        )
        slug = _slug(mod.name)
        mod_path = wiki_path / "modules" / f"{slug}.md"
        mod_path.write_text(f"# {mod.name}\n\n{mod_text}\n")
        created.append(mod_path)
        print(f"    → modules/{mod_path.name}")

    # 3 — decisions
    print("  Generating decisions wiki...")
    ctx = _build_decisions_context(modules)
    decisions_text = _llm_call(
        prompt=DECISIONS_PROMPT.format(context=ctx),
        system=DECISIONS_SYSTEM,
        provider=provider,
        model=model,
    )
    decisions_path = wiki_path / "decisions.md"
    decisions_path.write_text(f"# Architectural Decisions\n\n{decisions_text}\n")
    created.append(decisions_path)
    print(f"    → {decisions_path.name}")

    # 4 — flows
    print("  Generating flows wiki...")
    ctx = _build_flows_context(modules, parsed_files)
    flows_text = _llm_call(
        prompt=FLOWS_PROMPT.format(context=ctx),
        system=FLOWS_SYSTEM,
        provider=provider,
        model=model,
    )
    flows_path = wiki_path / "flows.md"
    flows_path.write_text(f"# Execution Flows\n\n{flows_text}\n")
    created.append(flows_path)
    print(f"    → {flows_path.name}")

    # 5 — _index.md (no LLM call)
    print("  Generating index...")
    index_lines: list[str] = [
        f"# Engineering Wiki\n",
        f"Generated from: {repo_url}\n",
        "## Modules\n",
    ]
    for mod in modules:
        slug = _slug(mod.name)
        dep_note = f" — depends on {', '.join(mod.imports_from)}" if mod.imports_from else ""
        index_lines.append(f"- [{mod.name}](modules/{slug}.md){dep_note}")

    index_lines.extend([
        "\n## Reference\n",
        "- [Overview](overview.md)",
        "- [Architectural Decisions](decisions.md)",
        "- [Execution Flows](flows.md)",
    ])
    index_path = wiki_path / "_index.md"
    index_path.write_text("\n".join(index_lines) + "\n")
    created.append(index_path)
    print(f"    → {index_path.name}")

    return created
