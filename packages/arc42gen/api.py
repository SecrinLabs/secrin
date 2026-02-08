import tempfile
import shutil
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Use unified config from packages/config
from packages.config.settings import Settings

from .models.config import Config
from .core.orchestrator import Orchestrator
from .core.analyzer import CodebaseAnalyzer
from .diagrams import C4Generator
from .diataxis import DiátaxisGenerator
from .citation import FactExtractor
from .publishing import DocumentationPublisher

logger = logging.getLogger(__name__)

# Load settings from unified config
settings = Settings()

app = FastAPI(title="Arc42gen API", version="0.1.0")

# Allow CORS for the web app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    """Request to generate docs for a repository."""
    source_repo_url: str  # GitHub URL like https://github.com/owner/repo
    branch: str = "main"
    github_token: Optional[str] = None  # Token for private repos


class GenerateResponse(BaseModel):
    """Response with generated documentation."""
    success: bool
    files: dict[str, str]  # filename -> content
    error: Optional[str] = None


def add_mdx_frontmatter(content: str, title: str, description: str = "") -> str:
    """Add MDX frontmatter for Fumadocs compatibility."""
    frontmatter = f"""---
title: {title}
description: {description or title}
---

"""
    return frontmatter + content


@app.post("/generate", response_model=GenerateResponse)
async def generate_docs(request: GenerateRequest) -> GenerateResponse:
    # Create temp directory for output
    output_dir = tempfile.mkdtemp()

    try:
        # Build the repo URL with authentication if token provided
        repo_url = request.source_repo_url

        # If we have a token, embed it in the URL for git clone
        if request.github_token:
            if repo_url.startswith("https://github.com/"):
                repo_url = repo_url.replace(
                    "https://github.com/",
                    f"https://x-access-token:{request.github_token}@github.com/"
                )

        if not repo_url.endswith(".git"):
            repo_url = f"{repo_url}.git"

        # Get API key from unified config based on provider
        provider = settings.ARC42GEN_LLM_PROVIDER
        if provider == "gemini":
            api_key = settings.GEMINI_API_KEY
        else:
            api_key = settings.OPENAI_API_KEY  # Using OPENAI for anthropic fallback

        if not api_key:
            raise HTTPException(
                status_code=500,
                detail=f"No API key configured for {provider}. Set GEMINI_API_KEY in your .env file"
            )

        # Create arc42gen config from unified settings
        config_dict = {
            'llm': {
                'provider': settings.ARC42GEN_LLM_PROVIDER,
                'model': settings.ARC42GEN_LLM_MODEL,
                'api_key': api_key,
                'max_tokens': settings.ARC42GEN_MAX_TOKENS,
            },
            'repository': {
                'include': settings.ARC42GEN_INCLUDE_PATTERNS,
                'exclude': settings.ARC42GEN_EXCLUDE_PATTERNS,
            },
            'arc42': {
                'sections': settings.ARC42GEN_SECTIONS,
                'diagram_style': settings.ARC42GEN_DIAGRAM_STYLE,
                'output_format': settings.ARC42GEN_OUTPUT_FORMAT,
            },
            'decomposition': {
                'max_module_size': settings.ARC42GEN_MAX_MODULE_SIZE,
                'max_depth': settings.ARC42GEN_MAX_DEPTH,
            },
            'output': {'path': output_dir},
        }

        cfg = Config.from_dict(config_dict)

        # Initialize all files dict
        files = {}

        # =====================================================================
        # Step 1: Analyze codebase (shared by all generators)
        # =====================================================================
        logger.info(f"Analyzing codebase: {repo_url}")
        analyzer = CodebaseAnalyzer(cfg)
        analysis = analyzer.analyze(repo_url)

        # =====================================================================
        # Step 2: Generate Arc42 documentation
        # =====================================================================
        logger.info("Generating Arc42 documentation...")
        orchestrator = Orchestrator(cfg)
        success = orchestrator.run(
            repo_path=repo_url,
            output_path=output_dir,
        )

        if success:
            # Read Arc42 generated files
            output_path = Path(output_dir)
            for file_path in output_path.rglob("*.md"):
                rel_path = file_path.relative_to(output_path)
                content = file_path.read_text()
                # Convert to MDX with frontmatter
                title = rel_path.stem.replace('_', ' ').replace('-', ' ').title()
                mdx_content = add_mdx_frontmatter(content, title, f"Arc42 - {title}")
                files[f"architecture/{rel_path.stem}.mdx"] = mdx_content

        # =====================================================================
        # Step 3: Generate C4 Diagrams
        # =====================================================================
        logger.info("Generating C4 diagrams...")
        try:
            c4_generator = C4Generator(config=cfg.llm)
            c4_diagrams = c4_generator.generate_all_levels(analysis, levels=[1, 2, 3, 4])

            # Level 1: System Context
            if c4_diagrams.context:
                content = c4_diagrams.context.to_markdown()
                mdx_content = add_mdx_frontmatter(
                    content,
                    "System Context Diagram",
                    "C4 Level 1 - Shows the system in context with external actors and systems"
                )
                files["diagrams/c4-level1-context.mdx"] = mdx_content

            # Level 2: Container
            if c4_diagrams.containers:
                content = c4_diagrams.containers.to_markdown()
                mdx_content = add_mdx_frontmatter(
                    content,
                    "Container Diagram",
                    "C4 Level 2 - Shows high-level technology choices"
                )
                files["diagrams/c4-level2-container.mdx"] = mdx_content

            # Level 3: Component diagrams
            for i, comp in enumerate(c4_diagrams.components):
                content = comp.to_markdown()
                name = comp.target_component or f"component-{i+1}"
                safe_name = name.lower().replace(' ', '-').replace('_', '-')
                mdx_content = add_mdx_frontmatter(
                    content,
                    f"Component Diagram: {name}",
                    f"C4 Level 3 - Internal components of {name}"
                )
                files[f"diagrams/c4-level3-{safe_name}.mdx"] = mdx_content

            # Level 4: Code diagrams
            for i, code in enumerate(c4_diagrams.code):
                content = code.to_markdown()
                name = code.target_component or f"code-{i+1}"
                safe_name = name.lower().replace(' ', '-').replace('_', '-')
                mdx_content = add_mdx_frontmatter(
                    content,
                    f"Code Diagram: {name}",
                    f"C4 Level 4 - Class/code structure of {name}"
                )
                files[f"diagrams/c4-level4-{safe_name}.mdx"] = mdx_content

        except Exception as e:
            logger.error(f"C4 diagram generation failed: {e}")

        # =====================================================================
        # Step 4: Generate Diataxis Documentation
        # =====================================================================
        logger.info("Generating Diataxis documentation...")
        try:
            diataxis_generator = DiátaxisGenerator(config=cfg.llm)
            diataxis_doc = diataxis_generator.generate_all(analysis)

            # Tutorials
            for tutorial in diataxis_doc.tutorials:
                content = tutorial.to_markdown()
                safe_name = tutorial.title.lower().replace(' ', '-').replace('_', '-')
                mdx_content = add_mdx_frontmatter(
                    content,
                    f"Tutorial: {tutorial.title}",
                    tutorial.goal
                )
                files[f"tutorials/{safe_name}.mdx"] = mdx_content

            # How-To Guides
            for guide in diataxis_doc.how_to_guides:
                content = guide.to_markdown()
                safe_name = guide.title.lower().replace(' ', '-').replace('_', '-')
                mdx_content = add_mdx_frontmatter(
                    content,
                    f"How-To: {guide.title}",
                    guide.problem
                )
                files[f"how-to/{safe_name}.mdx"] = mdx_content

            # Reference
            for ref in diataxis_doc.references:
                content = ref.to_markdown()
                safe_name = ref.title.lower().replace(' ', '-').replace('_', '-')
                mdx_content = add_mdx_frontmatter(
                    content,
                    ref.title,
                    ref.overview[:200] if ref.overview else "Technical reference documentation"
                )
                files[f"reference/{safe_name}.mdx"] = mdx_content

            # Explanation
            for exp in diataxis_doc.explanations:
                content = exp.to_markdown()
                safe_name = exp.title.lower().replace(' ', '-').replace('_', '-')
                mdx_content = add_mdx_frontmatter(
                    content,
                    f"Explanation: {exp.title}",
                    exp.problem[:200] if exp.problem else "Understanding the architecture"
                )
                files[f"explanation/{safe_name}.mdx"] = mdx_content

        except Exception as e:
            logger.error(f"Diataxis documentation generation failed: {e}")

        # =====================================================================
        # Step 4.5: Extract facts and add provenance (if citation enabled)
        # =====================================================================
        facts = []
        try:
            if cfg.citation.require_citations:
                logger.info("Extracting codebase facts for citation...")
                fact_extractor = FactExtractor(repo_path=analysis.repo_path)
                facts = fact_extractor.extract_all_facts(analysis)
                logger.info(f"Extracted {len(facts)} facts")

            # Always add provenance
            publisher = DocumentationPublisher(llm_config=cfg.llm)

            # Get source commit if available
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
                    files=files,
                    facts=facts,
                    source_commit=source_commit,
                )
                logger.info(f"Added provenance to {publish_result.files_published} files")

            # Add citation index if facts were extracted
            if facts and cfg.citation.require_citations:
                citation_index = publisher.create_citation_index(facts)
                citation_mdx = add_mdx_frontmatter(
                    citation_index,
                    "Citation Index",
                    "Source code references for all documented claims"
                )
                files["reference/citation-index.mdx"] = citation_mdx

        except Exception as e:
            logger.error(f"Citation/provenance generation failed: {e}")

        # =====================================================================
        # Step 5: Generate index page
        # =====================================================================
        index_content = f"""---
title: Documentation
description: Auto-generated documentation for {analysis.repo_name}
---

# {analysis.repo_name} Documentation

Welcome to the auto-generated documentation for **{analysis.repo_name}**.

## Documentation Structure

### 📐 Architecture
Arc42 architecture documentation covering system design, building blocks, and technical decisions.

### 📊 Diagrams
C4 model diagrams at all 4 levels:
- **Level 1**: System Context - External actors and systems
- **Level 2**: Container - High-level technology choices
- **Level 3**: Component - Internal components
- **Level 4**: Code - Class/code structure

### 📚 Tutorials
Learning-oriented guides to help you get started with the project.

### 🔧 How-To
Problem-solving guides for common tasks and troubleshooting.

### 📖 Reference
Technical reference documentation including API details and configuration.

### 💡 Explanation
Deep-dive explanations of architecture decisions and trade-offs.

---

*Generated automatically by [Secrin](https://secrin.dev)*
"""
        files["index.mdx"] = index_content

        # =====================================================================
        # Step 6: Generate meta.json for navigation
        # =====================================================================
        import json
        meta_content = {
            "title": analysis.repo_name,
            "pages": ["index", "architecture", "diagrams", "tutorials", "how-to", "reference", "explanation"]
        }
        files["meta.json"] = json.dumps(meta_content, indent=2)

        if not files:
            return GenerateResponse(success=False, files={}, error="No documentation generated")

        logger.info(f"Generated {len(files)} documentation files")
        return GenerateResponse(success=True, files=files)

    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        return GenerateResponse(success=False, files={}, error=str(e))

    finally:
        # Cleanup temp directory
        shutil.rmtree(output_dir, ignore_errors=True)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "provider": settings.ARC42GEN_LLM_PROVIDER,
        "model": settings.ARC42GEN_LLM_MODEL,
    }
