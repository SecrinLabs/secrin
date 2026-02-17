"""
RQ job function for async documentation generation.

This module contains the main task function that RQ workers execute.
It extracts the full pipeline from api.py and adds:
- Progress tracking via RQ job.meta
- GitHub commit step using PyGithub
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
from .core.orchestrator import Orchestrator
from .core.analyzer import CodebaseAnalyzer
from .diagrams import C4Generator
from .diataxis import DiátaxisGenerator
from .citation import FactExtractor
from .publishing import DocumentationPublisher

logger = logging.getLogger(__name__)


def _update_progress(step: int, total: int, message: str, status: str = "running"):
    """Update RQ job meta with progress info."""
    job = get_current_job()
    if job:
        job.meta["progress"] = int((step / total) * 100)
        job.meta["current_step"] = message
        job.meta["status"] = status
        job.meta["step_number"] = step
        job.meta["total_steps"] = total
        job.save_meta()
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


def generate_only(
    repo_url: str,
    config_dict: dict,
):
    """
    Documentation generation pipeline without GitHub commit.

    Used by the public landing page to generate docs for any repo URL.
    Returns the generated file names and content summary.
    """
    output_dir = tempfile.mkdtemp()
    pipeline_start = time.time()
    total_steps = 6

    logger.info("=" * 60)
    logger.info("JOB START: generate_only")
    logger.info("  repo_url: %s", repo_url)
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

        # Step 2: Generate Arc42
        _update_progress(2, total_steps, "arc42")
        t0 = time.time()
        orchestrator = Orchestrator(cfg, verbose=False)
        success = orchestrator.run(repo_path=repo_url, output_path=output_dir)
        logger.info("Arc42 done (success=%s) (%.1fs)", success, time.time() - t0)

        if success:
            output_path = Path(output_dir)
            for file_path in output_path.rglob("*.md"):
                rel_path = file_path.relative_to(output_path)
                content = file_path.read_text()
                title = rel_path.stem.replace("_", " ").replace("-", " ").title()
                mdx_content = add_mdx_frontmatter(content, title, f"Arc42 - {title}")
                files[f"architecture/{rel_path.stem}.mdx"] = mdx_content

        # Step 3: Generate C4 Diagrams
        _update_progress(3, total_steps, "diagrams")
        t0 = time.time()
        try:
            c4_generator = C4Generator(config=cfg.llm)
            c4_diagrams = c4_generator.generate_all_levels(analysis, levels=[1, 2, 3, 4])

            if c4_diagrams.context:
                content = c4_diagrams.context.to_markdown()
                mdx_content = add_mdx_frontmatter(
                    content, "System Context Diagram",
                    "C4 Level 1 - Shows the system in context with external actors and systems",
                )
                files["diagrams/c4-level1-context.mdx"] = mdx_content

            if c4_diagrams.containers:
                content = c4_diagrams.containers.to_markdown()
                mdx_content = add_mdx_frontmatter(
                    content, "Container Diagram",
                    "C4 Level 2 - Shows high-level technology choices",
                )
                files["diagrams/c4-level2-container.mdx"] = mdx_content

            for i, comp in enumerate(c4_diagrams.components):
                content = comp.to_markdown()
                name = comp.target_component or f"component-{i+1}"
                safe_name = name.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, f"Component Diagram: {name}",
                    f"C4 Level 3 - Internal components of {name}",
                )
                files[f"diagrams/c4-level3-{safe_name}.mdx"] = mdx_content

            for i, code in enumerate(c4_diagrams.code):
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

        # Step 4: Generate Diataxis
        _update_progress(4, total_steps, "diataxis")
        t0 = time.time()
        try:
            diataxis_generator = DiátaxisGenerator(config=cfg.llm)
            diataxis_doc = diataxis_generator.generate_all(analysis)

            for tutorial in diataxis_doc.tutorials:
                content = tutorial.to_markdown()
                safe_name = tutorial.title.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, f"Tutorial: {tutorial.title}", tutorial.goal,
                )
                files[f"tutorials/{safe_name}.mdx"] = mdx_content

            for guide in diataxis_doc.how_to_guides:
                content = guide.to_markdown()
                safe_name = guide.title.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, f"How-To: {guide.title}", guide.problem,
                )
                files[f"how-to/{safe_name}.mdx"] = mdx_content

            for ref in diataxis_doc.references:
                content = ref.to_markdown()
                safe_name = ref.title.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, ref.title,
                    ref.overview[:200] if ref.overview else "Technical reference documentation",
                )
                files[f"reference/{safe_name}.mdx"] = mdx_content

            for exp in diataxis_doc.explanations:
                content = exp.to_markdown()
                safe_name = exp.title.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, f"Explanation: {exp.title}",
                    exp.problem[:200] if exp.problem else "Understanding the architecture",
                )
                files[f"explanation/{safe_name}.mdx"] = mdx_content

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

        total_time = time.time() - pipeline_start
        _update_progress(total_steps, total_steps, "complete", status="success")

        logger.info("=" * 60)
        logger.info("JOB COMPLETE (generate_only)")
        logger.info("  Total files: %d", len(files))
        logger.info("  Total time: %.1fs", total_time)
        logger.info("=" * 60)

        return {
            "success": True,
            "files_count": len(files),
            "total_time": round(total_time, 1),
            "file_names": sorted(files.keys()),
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
):
    """
    Full documentation generation pipeline + GitHub commit.

    This is the function that RQ workers execute. It:
    1. Analyzes the codebase
    2. Generates Arc42 docs
    3. Generates C4 diagrams
    4. Generates Diataxis docs
    5. Adds provenance/citations
    6. Generates index + navigation
    7. Commits all files to GitHub

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

    Returns:
        dict with success, files count, and metrics
    """
    output_dir = tempfile.mkdtemp()
    pipeline_start = time.time()
    total_steps = 7

    logger.info("=" * 60)
    logger.info("JOB START: generate_and_commit")
    logger.info("  project_id: %s", project_id)
    logger.info("  repo: %s/%s", source_owner, source_name)
    logger.info("  docs_repo: %s/%s", owner, repo_name)
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

        # Step 2: Generate Arc42
        _update_progress(2, total_steps, "Generating Arc42 documentation...")
        t0 = time.time()
        orchestrator = Orchestrator(cfg, verbose=False)
        success = orchestrator.run(repo_path=repo_url, output_path=output_dir)
        logger.info("Arc42 done (success=%s) (%.1fs)", success, time.time() - t0)

        if success:
            output_path = Path(output_dir)
            for file_path in output_path.rglob("*.md"):
                rel_path = file_path.relative_to(output_path)
                content = file_path.read_text()
                title = rel_path.stem.replace("_", " ").replace("-", " ").title()
                mdx_content = add_mdx_frontmatter(content, title, f"Arc42 - {title}")
                files[f"architecture/{rel_path.stem}.mdx"] = mdx_content

        # Step 3: Generate C4 Diagrams
        _update_progress(3, total_steps, "Generating C4 diagrams...")
        t0 = time.time()
        try:
            c4_generator = C4Generator(config=cfg.llm)
            c4_diagrams = c4_generator.generate_all_levels(analysis, levels=[1, 2, 3, 4])

            if c4_diagrams.context:
                content = c4_diagrams.context.to_markdown()
                mdx_content = add_mdx_frontmatter(
                    content, "System Context Diagram",
                    "C4 Level 1 - Shows the system in context with external actors and systems",
                )
                files["diagrams/c4-level1-context.mdx"] = mdx_content

            if c4_diagrams.containers:
                content = c4_diagrams.containers.to_markdown()
                mdx_content = add_mdx_frontmatter(
                    content, "Container Diagram",
                    "C4 Level 2 - Shows high-level technology choices",
                )
                files["diagrams/c4-level2-container.mdx"] = mdx_content

            for i, comp in enumerate(c4_diagrams.components):
                content = comp.to_markdown()
                name = comp.target_component or f"component-{i+1}"
                safe_name = name.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, f"Component Diagram: {name}",
                    f"C4 Level 3 - Internal components of {name}",
                )
                files[f"diagrams/c4-level3-{safe_name}.mdx"] = mdx_content

            for i, code in enumerate(c4_diagrams.code):
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

        # Step 4: Generate Diataxis
        _update_progress(4, total_steps, "Generating Diataxis documentation...")
        t0 = time.time()
        try:
            diataxis_generator = DiátaxisGenerator(config=cfg.llm)
            diataxis_doc = diataxis_generator.generate_all(analysis)

            for tutorial in diataxis_doc.tutorials:
                content = tutorial.to_markdown()
                safe_name = tutorial.title.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, f"Tutorial: {tutorial.title}", tutorial.goal,
                )
                files[f"tutorials/{safe_name}.mdx"] = mdx_content

            for guide in diataxis_doc.how_to_guides:
                content = guide.to_markdown()
                safe_name = guide.title.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, f"How-To: {guide.title}", guide.problem,
                )
                files[f"how-to/{safe_name}.mdx"] = mdx_content

            for ref in diataxis_doc.references:
                content = ref.to_markdown()
                safe_name = ref.title.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, ref.title,
                    ref.overview[:200] if ref.overview else "Technical reference documentation",
                )
                files[f"reference/{safe_name}.mdx"] = mdx_content

            for exp in diataxis_doc.explanations:
                content = exp.to_markdown()
                safe_name = exp.title.lower().replace(" ", "-").replace("_", "-")
                mdx_content = add_mdx_frontmatter(
                    content, f"Explanation: {exp.title}",
                    exp.problem[:200] if exp.problem else "Understanding the architecture",
                )
                files[f"explanation/{safe_name}.mdx"] = mdx_content

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

        total_time = time.time() - pipeline_start
        _update_progress(total_steps, total_steps, "Complete", status="success")

        logger.info("=" * 60)
        logger.info("JOB COMPLETE")
        logger.info("  Total files: %d", len(files))
        logger.info("  Total time: %.1fs", total_time)
        logger.info("=" * 60)

        return {
            "success": True,
            "files_count": len(files),
            "total_time": round(total_time, 1),
            "file_names": sorted(files.keys()),
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
