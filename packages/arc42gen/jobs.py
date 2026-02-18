"""
RQ job function for async documentation generation.

This module contains the main task function that RQ workers execute.
It extracts the full pipeline from api.py and adds:
- Progress tracking via RQ job.meta (with substep granularity)
- GitHub commit step using PyGithub
- Local file writing for fumadocs dev server
"""

import tempfile
import shutil
import time
import json
import logging
import traceback
from pathlib import Path
from typing import Optional

from rq import get_current_job

from packages.config.settings import Settings
from .models.config import Config
from .models.documentation import Arc42Document
from .core.orchestrator import SECTION_NAMES, SECTION_ATTR_NAMES
from .core.analyzer import CodebaseAnalyzer
from .core.generator import Arc42Generator
from .core.formatter import OutputFormatter
from .diagrams import C4Generator
from .diataxis import DiátaxisGenerator
from .citation import FactExtractor
from .publishing import DocumentationPublisher

logger = logging.getLogger(__name__)


def _update_progress(
    step: int,
    total: int,
    message: str,
    status: str = "running",
    substep: Optional[int] = None,
    substep_total: Optional[int] = None,
    substep_message: Optional[str] = None,
):
    """Update RQ job meta with progress info including optional substep details."""
    job = get_current_job()
    if job:
        job.meta["progress"] = int((step / total) * 100)
        job.meta["current_step"] = message
        job.meta["status"] = status
        job.meta["step_number"] = step
        job.meta["total_steps"] = total
        job.meta["substep"] = substep
        job.meta["substep_total"] = substep_total
        job.meta["substep_message"] = substep_message
        job.save_meta()
    if substep_message:
        logger.info("[%d/%d] %s — substep %d/%d: %s", step, total, message, substep, substep_total, substep_message)
    else:
        logger.info("[%d/%d] %s", step, total, message)


def add_mdx_frontmatter(content: str, title: str, description: str = "") -> str:
    """Add MDX frontmatter for Fumadocs compatibility."""
    # Escape double quotes in title and description for YAML safety
    safe_title = title.replace('"', '\\"')
    safe_description = (description or title).replace('"', '\\"')
    frontmatter = f'''---
title: "{safe_title}"
description: "{safe_description}"
---

'''
    return frontmatter + content


def _write_local_files(files: dict[str, str], output_dir: str) -> int:
    """Write generated doc files to a local directory. Returns count of files written."""
    output_path = Path(output_dir)
    count = 0
    for rel_path, content in files.items():
        dest = output_path / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        count += 1
    return count


def _commit_to_github(
    files: dict[str, str],
    github_token: str,
    owner: str,
    repo_name: str,
    source_owner: str,
    source_name: str,
):
    """Commit generated documentation files to GitHub using PyGithub."""
    from github import Github, InputGitTreeElement

    g = Github(github_token)
    repo = g.get_repo(f"{owner}/{repo_name}")

    branch = repo.default_branch
    ref = repo.get_git_ref(f"heads/{branch}")
    latest_commit = repo.get_git_commit(ref.object.sha)

    # Create tree elements for all files (under content/docs/ folder)
    tree_elements = []
    for path, content in files.items():
        blob = repo.create_git_blob(content, "utf-8")
        tree_elements.append(
            InputGitTreeElement(
                path=f"content/docs/{path}",
                mode="100644",
                type="blob",
                sha=blob.sha,
            )
        )

    # Create new tree based on the latest commit's tree
    new_tree = repo.create_git_tree(tree_elements, base_tree=latest_commit.tree)

    # Create commit
    message = f"docs: regenerate from {source_owner}/{source_name}"
    new_commit = repo.create_git_commit(message, new_tree, [latest_commit])

    # Update branch ref
    ref.edit(new_commit.sha)

    logger.info(
        "Committed %d files to %s/%s@%s (%s)",
        len(files), owner, repo_name, branch, new_commit.sha[:7],
    )


# ---------------------------------------------------------------------------
# C4 level names for substep messages
# ---------------------------------------------------------------------------
C4_LEVEL_NAMES = {
    1: "System Context Diagram",
    2: "Container Diagram",
    3: "Component Diagram",
    4: "Code Diagram",
}

DIATAXIS_TYPE_NAMES = {
    1: "Tutorials",
    2: "How-To Guides",
    3: "Reference",
    4: "Explanations",
}


def generate_only(
    repo_url: str,
    config_dict: dict,
    local_output_dir: str = "./docs",
):
    """
    Documentation generation pipeline without GitHub commit.

    Used by the public landing page to generate docs for any repo URL.
    Writes files locally so the fumadocs dev server can serve them.

    Steps:
    1. Analyzing codebase
    2. Generating Arc42 documentation (12 substeps)
    3. Generating C4 diagrams (4 substeps)
    4. Generating Diataxis documentation (4 substeps)
    5. Adding provenance & citations
    6. Finalizing documentation
    7. Writing local docs
    """
    output_dir = tempfile.mkdtemp()
    pipeline_start = time.time()
    total_steps = 7

    logger.info("=" * 60)
    logger.info("JOB START: generate_only")
    logger.info("  repo_url: %s", repo_url)
    logger.info("  local_output_dir: %s", local_output_dir)
    logger.info("=" * 60)

    try:
        config_dict["output"] = {"path": output_dir}
        cfg = Config.from_dict(config_dict)

        files = {}

        # Step 1: Analyze codebase
        _update_progress(1, total_steps, "analyzing")
        t0 = time.time()
        analyzer = CodebaseAnalyzer(cfg)
        analysis = analyzer.analyze(repo_url)
        logger.info(
            "Analysis complete: %d modules, %d files, %d LOC (%.1fs)",
            analysis.statistics.total_modules,
            analysis.statistics.total_files,
            analysis.statistics.total_loc,
            time.time() - t0,
        )

        # Step 2: Generate Arc42 — inline with substep tracking per section
        _update_progress(2, total_steps, "arc42", substep=0, substep_total=12, substep_message="Starting...")
        t0 = time.time()

        arc42_generator = Arc42Generator(config=cfg.llm)
        arc42_formatter = OutputFormatter(cfg)
        doc = Arc42Document()
        sections = list(range(1, 13))

        section_generators = {
            1: arc42_generator.generate_section_1,
            2: arc42_generator.generate_section_2,
            3: arc42_generator.generate_section_3,
            4: arc42_generator.generate_section_4,
            5: arc42_generator.generate_section_5,
            6: arc42_generator.generate_section_6,
            7: arc42_generator.generate_section_7,
            8: arc42_generator.generate_section_8,
            9: arc42_generator.generate_section_9,
            10: arc42_generator.generate_section_10,
            11: arc42_generator.generate_section_11,
            12: arc42_generator.generate_section_12,
        }

        for section_num in sections:
            name = SECTION_NAMES.get(section_num, f"Section {section_num}")
            _update_progress(
                2, total_steps, "arc42",
                substep=section_num, substep_total=12,
                substep_message=f"Section {section_num}: {name}",
            )
            try:
                gen_func = section_generators.get(section_num)
                if gen_func:
                    section_obj = gen_func(analysis)
                    attr_name = SECTION_ATTR_NAMES.get(section_num)
                    if attr_name:
                        setattr(doc, attr_name, section_obj)
            except Exception as e:
                logger.error("Arc42 section %d failed: %s", section_num, e)

        # Write Arc42 output to temp dir, then collect as MDX files
        arc42_formatter.write_arc42_document(doc, output_dir)
        output_path = Path(output_dir)
        for file_path in output_path.rglob("*.md"):
            rel_path = file_path.relative_to(output_path)
            content = file_path.read_text()
            title = rel_path.stem.replace("_", " ").replace("-", " ").title()
            mdx_content = add_mdx_frontmatter(content, title, f"Arc42 - {title}")
            files[f"architecture/{rel_path.stem}.mdx"] = mdx_content

        logger.info("Arc42 done (%.1fs)", time.time() - t0)

        # Step 3: Generate C4 Diagrams — with substep tracking per level
        _update_progress(3, total_steps, "diagrams", substep=0, substep_total=4, substep_message="Starting...")
        t0 = time.time()
        try:
            c4_generator = C4Generator(config=cfg.llm)

            # Level 1: System Context
            _update_progress(3, total_steps, "diagrams", substep=1, substep_total=4, substep_message="Level 1: System Context")
            context = c4_generator.generate_level_1(analysis)
            if context:
                content = context.to_markdown()
                mdx_content = add_mdx_frontmatter(
                    content, "System Context Diagram",
                    "C4 Level 1 - Shows the system in context with external actors and systems",
                )
                files["diagrams/c4-level1-context.mdx"] = mdx_content

            # Level 2: Container
            _update_progress(3, total_steps, "diagrams", substep=2, substep_total=4, substep_message="Level 2: Container Diagram")
            containers = c4_generator.generate_level_2(analysis)
            if containers:
                content = containers.to_markdown()
                mdx_content = add_mdx_frontmatter(
                    content, "Container Diagram",
                    "C4 Level 2 - Shows high-level technology choices",
                )
                files["diagrams/c4-level2-container.mdx"] = mdx_content

            # Level 3: Component
            _update_progress(3, total_steps, "diagrams", substep=3, substep_total=4, substep_message="Level 3: Component Diagrams")
            components = c4_generator.generate_level_3(analysis)
            for i, comp in enumerate(components):
                content = comp.to_markdown()
                name = comp.target_component or f"component-{i+1}"
                safe_name = name.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, f"Component Diagram: {name}",
                    f"C4 Level 3 - Internal components of {name}",
                )
                files[f"diagrams/c4-level3-{safe_name}.mdx"] = mdx_content

            # Level 4: Code
            _update_progress(3, total_steps, "diagrams", substep=4, substep_total=4, substep_message="Level 4: Code Diagrams")
            code_diagrams = c4_generator.generate_level_4(analysis)
            for i, code in enumerate(code_diagrams):
                content = code.to_markdown()
                name = code.target_component or f"code-{i+1}"
                safe_name = name.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, f"Code Diagram: {name}",
                    f"C4 Level 4 - Class/code structure of {name}",
                )
                files[f"diagrams/c4-level4-{safe_name}.mdx"] = mdx_content

            logger.info("C4 diagrams done (%.1fs)", time.time() - t0)
        except Exception as e:
            logger.error("C4 diagram generation failed: %s", e)
            logger.debug(traceback.format_exc())

        # Step 4: Generate Diataxis — with substep tracking per doc type
        _update_progress(4, total_steps, "diataxis", substep=0, substep_total=4, substep_message="Starting...")
        t0 = time.time()
        try:
            diataxis_generator = DiátaxisGenerator(config=cfg.llm)

            # Substep 1: Tutorials
            _update_progress(4, total_steps, "diataxis", substep=1, substep_total=4, substep_message="Generating tutorials")
            try:
                tutorial = diataxis_generator.generate_getting_started_tutorial(analysis)
                if tutorial:
                    safe_name = tutorial.title.lower().replace(" ", "-").replace("_", "-")
                    files[f"tutorials/{safe_name}.mdx"] = add_mdx_frontmatter(
                        tutorial.to_markdown(), f"Tutorial: {tutorial.title}", tutorial.goal,
                    )
            except Exception as e:
                logger.error("Diataxis tutorials failed: %s", e)

            # Substep 2: How-To Guides
            _update_progress(4, total_steps, "diataxis", substep=2, substep_total=4, substep_message="Generating how-to guides")
            try:
                setup_guide = diataxis_generator.generate_setup_howto(analysis)
                if setup_guide:
                    safe_name = setup_guide.title.lower().replace(" ", "-").replace("_", "-")
                    files[f"how-to/{safe_name}.mdx"] = add_mdx_frontmatter(
                        setup_guide.to_markdown(), f"How-To: {setup_guide.title}", setup_guide.problem,
                    )
                troubleshooting = diataxis_generator.generate_troubleshooting_howto(analysis)
                if troubleshooting:
                    safe_name = troubleshooting.title.lower().replace(" ", "-").replace("_", "-")
                    files[f"how-to/{safe_name}.mdx"] = add_mdx_frontmatter(
                        troubleshooting.to_markdown(), f"How-To: {troubleshooting.title}", troubleshooting.problem,
                    )
            except Exception as e:
                logger.error("Diataxis how-to guides failed: %s", e)

            # Substep 3: Reference
            _update_progress(4, total_steps, "diataxis", substep=3, substep_total=4, substep_message="Generating reference docs")
            try:
                ref = diataxis_generator.generate_api_reference(analysis)
                if ref:
                    safe_name = ref.title.lower().replace(" ", "-").replace("_", "-")
                    files[f"reference/{safe_name}.mdx"] = add_mdx_frontmatter(
                        ref.to_markdown(), ref.title,
                        ref.overview[:200] if ref.overview else "Technical reference documentation",
                    )
            except Exception as e:
                logger.error("Diataxis reference failed: %s", e)

            # Substep 4: Explanations
            _update_progress(4, total_steps, "diataxis", substep=4, substep_total=4, substep_message="Generating explanations")
            try:
                exp = diataxis_generator.generate_architecture_explanation(analysis)
                if exp:
                    safe_name = exp.title.lower().replace(" ", "-").replace("_", "-")
                    files[f"explanation/{safe_name}.mdx"] = add_mdx_frontmatter(
                        exp.to_markdown(), f"Explanation: {exp.title}",
                        exp.problem[:200] if exp.problem else "Understanding the architecture",
                    )
            except Exception as e:
                logger.error("Diataxis explanations failed: %s", e)

            logger.info("Diataxis done (%.1fs)", time.time() - t0)
        except Exception as e:
            logger.error("Diataxis generation failed: %s", e)
            logger.debug(traceback.format_exc())

        # Step 5: Provenance and citations
        _update_progress(5, total_steps, "citations")
        t0 = time.time()
        try:
            facts = []
            if cfg.citation.require_citations:
                fact_extractor = FactExtractor(repo_path=analysis.repo_path)
                facts = fact_extractor.extract_all_facts(analysis)

            publisher = DocumentationPublisher(llm_config=cfg.llm)

            source_commit = ""
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=analysis.repo_path,
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    source_commit = result.stdout.strip()
            except Exception:
                pass

            if cfg.maintenance.include_provenance:
                publish_result = publisher.publish_with_provenance(
                    files=files, facts=facts, source_commit=source_commit,
                )
                logger.info("Added provenance to %d files", publish_result.files_published)

            if facts and cfg.citation.require_citations:
                citation_index = publisher.create_citation_index(facts)
                citation_mdx = add_mdx_frontmatter(
                    citation_index, "Citation Index",
                    "Source code references for all documented claims",
                )
                files["reference/citation-index.mdx"] = citation_mdx

            logger.info("Provenance done (%.1fs)", time.time() - t0)
        except Exception as e:
            logger.error("Citation/provenance failed: %s", e)
            logger.debug(traceback.format_exc())

        # Step 6: Generate index page and navigation
        _update_progress(6, total_steps, "finalizing")
        index_content = f"""---
title: Documentation
description: Auto-generated documentation for {analysis.repo_name}
---

# {analysis.repo_name} Documentation

Welcome to the auto-generated documentation for **{analysis.repo_name}**.

## Documentation Structure

### Architecture
Arc42 architecture documentation covering system design, building blocks, and technical decisions.

### Diagrams
C4 model diagrams at all 4 levels.

### Tutorials
Learning-oriented guides to help you get started with the project.

### How-To
Problem-solving guides for common tasks and troubleshooting.

### Reference
Technical reference documentation including API details and configuration.

### Explanation
Deep-dive explanations of architecture decisions and trade-offs.

---

*Generated automatically by [Secrin](https://secrin.dev)*
"""
        files["index.mdx"] = index_content

        meta_content = {
            "title": analysis.repo_name,
            "pages": ["index", "architecture", "diagrams", "tutorials", "how-to", "reference", "explanation"],
        }
        files["meta.json"] = json.dumps(meta_content, indent=2)

        if not files:
            _update_progress(total_steps, total_steps, "No files generated", status="failed")
            return {"success": False, "error": "No documentation generated", "files_count": 0}

        # Step 7: Write local docs for fumadocs dev server
        _update_progress(7, total_steps, "writing_local")
        t0 = time.time()
        local_count = _write_local_files(files, local_output_dir)
        logger.info("Wrote %d files locally to %s (%.1fs)", local_count, local_output_dir, time.time() - t0)

        total_time = time.time() - pipeline_start
        _update_progress(total_steps, total_steps, "complete", status="success")

        logger.info("=" * 60)
        logger.info("JOB COMPLETE (generate_only)")
        logger.info("  Total files: %d", len(files))
        logger.info("  Local output: %s", local_output_dir)
        logger.info("  Total time: %.1fs", total_time)
        logger.info("=" * 60)

        return {
            "success": True,
            "files_count": len(files),
            "total_time": round(total_time, 1),
            "file_names": sorted(files.keys()),
            "local_output_dir": local_output_dir,
        }

    except Exception as e:
        total_time = time.time() - pipeline_start
        logger.error("=" * 60)
        logger.error("JOB FAILED after %.1fs", total_time)
        logger.error("  Error: %s", e)
        logger.error(traceback.format_exc())
        logger.error("=" * 60)

        _update_progress(0, total_steps, str(e), status="failed")

        return {
            "success": False,
            "error": str(e),
            "files_count": 0,
            "total_time": round(total_time, 1),
        }

    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


def generate_and_commit(
    repo_url: str,
    branch: str,
    github_token: str,
    owner: str,
    repo_name: str,
    source_owner: str,
    source_name: str,
    project_id: str,
    config_dict: dict,
    local_output_dir: str = "./docs",
):
    """
    Full documentation generation pipeline + GitHub commit + local file writing.

    This is the function that RQ workers execute. It:
    1. Analyzes the codebase
    2. Generates Arc42 docs (12 sections with substep tracking)
    3. Generates C4 diagrams (4 levels with substep tracking)
    4. Generates Diataxis docs (4 types with substep tracking)
    5. Adds provenance/citations
    6. Generates index + navigation
    7. Commits all files to GitHub
    8. Writes docs locally for fumadocs dev server

    Args:
        repo_url: Git clone URL (with token embedded for private repos)
        branch: Branch to analyze
        github_token: GitHub access token for committing
        owner: GitHub owner of the docs repo
        repo_name: GitHub repo name for docs
        source_owner: Owner of the source repo
        source_name: Name of the source repo
        project_id: Project ID for tracking
        config_dict: Configuration dictionary for arc42gen
        local_output_dir: Local directory to write docs to (default: ./docs)

    Returns:
        dict with success, files count, and metrics
    """
    output_dir = tempfile.mkdtemp()
    pipeline_start = time.time()
    total_steps = 8

    logger.info("=" * 60)
    logger.info("JOB START: generate_and_commit")
    logger.info("  project_id: %s", project_id)
    logger.info("  repo: %s/%s", source_owner, source_name)
    logger.info("  docs_repo: %s/%s", owner, repo_name)
    logger.info("  local_output_dir: %s", local_output_dir)
    logger.info("=" * 60)

    try:
        config_dict["output"] = {"path": output_dir}
        cfg = Config.from_dict(config_dict)

        files = {}

        # Step 1: Analyze codebase
        _update_progress(1, total_steps, "Analyzing codebase...")
        t0 = time.time()
        analyzer = CodebaseAnalyzer(cfg)
        analysis = analyzer.analyze(repo_url)
        logger.info(
            "Analysis complete: %d modules, %d files, %d LOC (%.1fs)",
            analysis.statistics.total_modules,
            analysis.statistics.total_files,
            analysis.statistics.total_loc,
            time.time() - t0,
        )

        # Step 2: Generate Arc42 — inline with substep tracking per section
        _update_progress(2, total_steps, "Generating Arc42 documentation...", substep=0, substep_total=12, substep_message="Starting...")
        t0 = time.time()

        arc42_generator = Arc42Generator(config=cfg.llm)
        arc42_formatter = OutputFormatter(cfg)
        doc = Arc42Document()
        sections = list(range(1, 13))

        section_generators = {
            1: arc42_generator.generate_section_1,
            2: arc42_generator.generate_section_2,
            3: arc42_generator.generate_section_3,
            4: arc42_generator.generate_section_4,
            5: arc42_generator.generate_section_5,
            6: arc42_generator.generate_section_6,
            7: arc42_generator.generate_section_7,
            8: arc42_generator.generate_section_8,
            9: arc42_generator.generate_section_9,
            10: arc42_generator.generate_section_10,
            11: arc42_generator.generate_section_11,
            12: arc42_generator.generate_section_12,
        }

        for section_num in sections:
            name = SECTION_NAMES.get(section_num, f"Section {section_num}")
            _update_progress(
                2, total_steps, "Generating Arc42 documentation...",
                substep=section_num, substep_total=12,
                substep_message=f"Section {section_num}: {name}",
            )
            try:
                gen_func = section_generators.get(section_num)
                if gen_func:
                    section_obj = gen_func(analysis)
                    attr_name = SECTION_ATTR_NAMES.get(section_num)
                    if attr_name:
                        setattr(doc, attr_name, section_obj)
            except Exception as e:
                logger.error("Arc42 section %d failed: %s", section_num, e)

        # Write Arc42 output to temp dir, then collect as MDX files
        arc42_formatter.write_arc42_document(doc, output_dir)
        output_path = Path(output_dir)
        for file_path in output_path.rglob("*.md"):
            rel_path = file_path.relative_to(output_path)
            content = file_path.read_text()
            title = rel_path.stem.replace("_", " ").replace("-", " ").title()
            mdx_content = add_mdx_frontmatter(content, title, f"Arc42 - {title}")
            files[f"architecture/{rel_path.stem}.mdx"] = mdx_content

        logger.info("Arc42 done (%.1fs)", time.time() - t0)

        # Step 3: Generate C4 Diagrams — with substep tracking per level
        _update_progress(3, total_steps, "Generating C4 diagrams...", substep=0, substep_total=4, substep_message="Starting...")
        t0 = time.time()
        try:
            c4_generator = C4Generator(config=cfg.llm)

            # Level 1: System Context
            _update_progress(3, total_steps, "Generating C4 diagrams...", substep=1, substep_total=4, substep_message="Level 1: System Context")
            context = c4_generator.generate_level_1(analysis)
            if context:
                content = context.to_markdown()
                mdx_content = add_mdx_frontmatter(
                    content, "System Context Diagram",
                    "C4 Level 1 - Shows the system in context with external actors and systems",
                )
                files["diagrams/c4-level1-context.mdx"] = mdx_content

            # Level 2: Container
            _update_progress(3, total_steps, "Generating C4 diagrams...", substep=2, substep_total=4, substep_message="Level 2: Container Diagram")
            containers = c4_generator.generate_level_2(analysis)
            if containers:
                content = containers.to_markdown()
                mdx_content = add_mdx_frontmatter(
                    content, "Container Diagram",
                    "C4 Level 2 - Shows high-level technology choices",
                )
                files["diagrams/c4-level2-container.mdx"] = mdx_content

            # Level 3: Component
            _update_progress(3, total_steps, "Generating C4 diagrams...", substep=3, substep_total=4, substep_message="Level 3: Component Diagrams")
            components = c4_generator.generate_level_3(analysis)
            for i, comp in enumerate(components):
                content = comp.to_markdown()
                name = comp.target_component or f"component-{i+1}"
                safe_name = name.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, f"Component Diagram: {name}",
                    f"C4 Level 3 - Internal components of {name}",
                )
                files[f"diagrams/c4-level3-{safe_name}.mdx"] = mdx_content

            # Level 4: Code
            _update_progress(3, total_steps, "Generating C4 diagrams...", substep=4, substep_total=4, substep_message="Level 4: Code Diagrams")
            code_diagrams = c4_generator.generate_level_4(analysis)
            for i, code in enumerate(code_diagrams):
                content = code.to_markdown()
                name = code.target_component or f"code-{i+1}"
                safe_name = name.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, f"Code Diagram: {name}",
                    f"C4 Level 4 - Class/code structure of {name}",
                )
                files[f"diagrams/c4-level4-{safe_name}.mdx"] = mdx_content

            logger.info("C4 diagrams done (%.1fs)", time.time() - t0)
        except Exception as e:
            logger.error("C4 diagram generation failed: %s", e)
            logger.debug(traceback.format_exc())

        # Step 4: Generate Diataxis — with substep tracking per doc type
        _update_progress(4, total_steps, "Generating Diataxis documentation...", substep=0, substep_total=4, substep_message="Starting...")
        t0 = time.time()
        try:
            diataxis_generator = DiátaxisGenerator(config=cfg.llm)

            # Substep 1: Tutorials
            _update_progress(4, total_steps, "Generating Diataxis documentation...", substep=1, substep_total=4, substep_message="Generating tutorials")
            try:
                tutorial = diataxis_generator.generate_getting_started_tutorial(analysis)
                if tutorial:
                    safe_name = tutorial.title.lower().replace(" ", "-").replace("_", "-")
                    files[f"tutorials/{safe_name}.mdx"] = add_mdx_frontmatter(
                        tutorial.to_markdown(), f"Tutorial: {tutorial.title}", tutorial.goal,
                    )
            except Exception as e:
                logger.error("Diataxis tutorials failed: %s", e)

            # Substep 2: How-To Guides
            _update_progress(4, total_steps, "Generating Diataxis documentation...", substep=2, substep_total=4, substep_message="Generating how-to guides")
            try:
                setup_guide = diataxis_generator.generate_setup_howto(analysis)
                if setup_guide:
                    safe_name = setup_guide.title.lower().replace(" ", "-").replace("_", "-")
                    files[f"how-to/{safe_name}.mdx"] = add_mdx_frontmatter(
                        setup_guide.to_markdown(), f"How-To: {setup_guide.title}", setup_guide.problem,
                    )
                troubleshooting = diataxis_generator.generate_troubleshooting_howto(analysis)
                if troubleshooting:
                    safe_name = troubleshooting.title.lower().replace(" ", "-").replace("_", "-")
                    files[f"how-to/{safe_name}.mdx"] = add_mdx_frontmatter(
                        troubleshooting.to_markdown(), f"How-To: {troubleshooting.title}", troubleshooting.problem,
                    )
            except Exception as e:
                logger.error("Diataxis how-to guides failed: %s", e)

            # Substep 3: Reference
            _update_progress(4, total_steps, "Generating Diataxis documentation...", substep=3, substep_total=4, substep_message="Generating reference docs")
            try:
                ref = diataxis_generator.generate_api_reference(analysis)
                if ref:
                    safe_name = ref.title.lower().replace(" ", "-").replace("_", "-")
                    files[f"reference/{safe_name}.mdx"] = add_mdx_frontmatter(
                        ref.to_markdown(), ref.title,
                        ref.overview[:200] if ref.overview else "Technical reference documentation",
                    )
            except Exception as e:
                logger.error("Diataxis reference failed: %s", e)

            # Substep 4: Explanations
            _update_progress(4, total_steps, "Generating Diataxis documentation...", substep=4, substep_total=4, substep_message="Generating explanations")
            try:
                exp = diataxis_generator.generate_architecture_explanation(analysis)
                if exp:
                    safe_name = exp.title.lower().replace(" ", "-").replace("_", "-")
                    files[f"explanation/{safe_name}.mdx"] = add_mdx_frontmatter(
                        exp.to_markdown(), f"Explanation: {exp.title}",
                        exp.problem[:200] if exp.problem else "Understanding the architecture",
                    )
            except Exception as e:
                logger.error("Diataxis explanations failed: %s", e)

            logger.info("Diataxis done (%.1fs)", time.time() - t0)
        except Exception as e:
            logger.error("Diataxis generation failed: %s", e)
            logger.debug(traceback.format_exc())

        # Step 5: Provenance and citations
        _update_progress(5, total_steps, "Adding provenance and citations...")
        t0 = time.time()
        try:
            facts = []
            if cfg.citation.require_citations:
                fact_extractor = FactExtractor(repo_path=analysis.repo_path)
                facts = fact_extractor.extract_all_facts(analysis)

            publisher = DocumentationPublisher(llm_config=cfg.llm)

            source_commit = ""
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=analysis.repo_path,
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    source_commit = result.stdout.strip()
            except Exception:
                pass

            if cfg.maintenance.include_provenance:
                publish_result = publisher.publish_with_provenance(
                    files=files, facts=facts, source_commit=source_commit,
                )
                logger.info("Added provenance to %d files", publish_result.files_published)

            if facts and cfg.citation.require_citations:
                citation_index = publisher.create_citation_index(facts)
                citation_mdx = add_mdx_frontmatter(
                    citation_index, "Citation Index",
                    "Source code references for all documented claims",
                )
                files["reference/citation-index.mdx"] = citation_mdx

            logger.info("Provenance done (%.1fs)", time.time() - t0)
        except Exception as e:
            logger.error("Citation/provenance failed: %s", e)
            logger.debug(traceback.format_exc())

        # Step 6: Generate index page and navigation
        _update_progress(6, total_steps, "Generating index and navigation...")
        index_content = f"""---
title: Documentation
description: Auto-generated documentation for {analysis.repo_name}
---

# {analysis.repo_name} Documentation

Welcome to the auto-generated documentation for **{analysis.repo_name}**.

## Documentation Structure

### Architecture
Arc42 architecture documentation covering system design, building blocks, and technical decisions.

### Diagrams
C4 model diagrams at all 4 levels:
- **Level 1**: System Context - External actors and systems
- **Level 2**: Container - High-level technology choices
- **Level 3**: Component - Internal components
- **Level 4**: Code - Class/code structure

### Tutorials
Learning-oriented guides to help you get started with the project.

### How-To
Problem-solving guides for common tasks and troubleshooting.

### Reference
Technical reference documentation including API details and configuration.

### Explanation
Deep-dive explanations of architecture decisions and trade-offs.

---

*Generated automatically by [Secrin](https://secrin.dev)*
"""
        files["index.mdx"] = index_content

        meta_content = {
            "title": analysis.repo_name,
            "pages": ["index", "architecture", "diagrams", "tutorials", "how-to", "reference", "explanation"],
        }
        files["meta.json"] = json.dumps(meta_content, indent=2)

        if not files:
            _update_progress(total_steps, total_steps, "No files generated", status="failed")
            return {"success": False, "error": "No documentation generated", "files_count": 0}

        # Step 7: Commit to GitHub
        _update_progress(7, total_steps, "Committing files to GitHub...")
        t0 = time.time()
        _commit_to_github(
            files=files,
            github_token=github_token,
            owner=owner,
            repo_name=repo_name,
            source_owner=source_owner,
            source_name=source_name,
        )
        logger.info("GitHub commit done (%.1fs)", time.time() - t0)

        # Step 8: Write local docs for fumadocs dev server
        _update_progress(8, total_steps, "Writing local docs...")
        t0 = time.time()
        local_count = _write_local_files(files, local_output_dir)
        logger.info("Wrote %d files locally to %s (%.1fs)", local_count, local_output_dir, time.time() - t0)

        total_time = time.time() - pipeline_start
        _update_progress(total_steps, total_steps, "Complete", status="success")

        logger.info("=" * 60)
        logger.info("JOB COMPLETE")
        logger.info("  Total files: %d", len(files))
        logger.info("  Local output: %s", local_output_dir)
        logger.info("  Total time: %.1fs", total_time)
        logger.info("=" * 60)

        return {
            "success": True,
            "files_count": len(files),
            "total_time": round(total_time, 1),
            "file_names": sorted(files.keys()),
            "local_output_dir": local_output_dir,
        }

    except Exception as e:
        total_time = time.time() - pipeline_start
        logger.error("=" * 60)
        logger.error("JOB FAILED after %.1fs", total_time)
        logger.error("  Error: %s", e)
        logger.error(traceback.format_exc())
        logger.error("=" * 60)

        _update_progress(0, total_steps, str(e), status="failed")

        return {
            "success": False,
            "error": str(e),
            "files_count": 0,
            "total_time": round(total_time, 1),
        }

    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
