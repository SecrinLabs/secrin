"""
Secrin Auditor V1 - Documentation Drift Detection

This script detects "Drift" between your code and your documentation
using Gemini 2.0 Flash for intelligent comparison.

Usage:
    python -m packages.auditor.audit ./docs ./src
    
Or via CLI:
    poetry run audit ./docs ./src
"""

import click
import os
import re
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from packages.wiki.llm_services import create_gemini_client, get_gemini_api_key
from google.genai import types  # type: ignore[import-untyped]

# Initialize Rich Console
console = Console()

# Initialize Gemini Client lazily
_client = None

# File extensions to consider as code
CODE_EXTENSIONS = {'.py', '.js', '.ts', '.tsx', '.go', '.rs', '.java', '.rb', '.php', '.jsx', '.vue', '.svelte'}

# Directories to skip when scanning
SKIP_DIRS = {'node_modules', '.git', '__pycache__', 'venv', '.venv', 'dist', 'build', '.next', 'coverage'}


def get_audit_client():
    """Get or initialize the Gemini client for auditing."""
    global _client
    if _client is None:
        try:
            _client = create_gemini_client()
        except Exception as e:
            console.print(
                f"[bold red]Error:[/bold red] Could not initialize Gemini client: {e}\n"
                "Make sure GEMINI_API_KEY is set in your .env file or environment.\n"
                "Get your key from: https://aistudio.google.com/"
            )
            raise SystemExit(1)
    return _client


def get_codebase_summary(repo_root: str, max_files: int = 50) -> str:
    """
    Generate a summary of the codebase structure and key files.
    
    Args:
        repo_root: Root path of the repository
        max_files: Maximum number of files to include in summary
        
    Returns:
        String containing codebase structure and key file contents
    """
    summary_parts = []
    summary_parts.append("=== CODEBASE STRUCTURE ===\n")
    
    # Get directory tree
    tree_lines = []
    for root, dirs, files in os.walk(repo_root):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        level = root.replace(repo_root, '').count(os.sep)
        indent = '  ' * level
        folder_name = os.path.basename(root)
        tree_lines.append(f"{indent}{folder_name}/")
        
        # Only show first 2 levels of depth for tree
        if level < 2:
            sub_indent = '  ' * (level + 1)
            for file in sorted(files)[:10]:  # Limit files per dir
                if Path(file).suffix in CODE_EXTENSIONS or file in ['pyproject.toml', 'package.json', 'README.md']:
                    tree_lines.append(f"{sub_indent}{file}")
    
    summary_parts.append('\n'.join(tree_lines[:100]))  # Limit tree size
    
    # Read key files content
    key_files = []
    priority_patterns = [
        '**/routes/**/*.py', '**/routes/**/*.ts',
        '**/api/**/*.py', '**/api/**/*.ts',
        '**/main.py', '**/app.py', '**/server.py',
        '**/settings.py', '**/config.py',
        'pyproject.toml', 'package.json'
    ]
    
    # Find important files
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel_root = os.path.relpath(root, repo_root)
        
        for file in files:
            if len(key_files) >= max_files:
                break
            
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_root)
            
            # Prioritize route/api files and config files
            is_priority = any(
                'route' in rel_path.lower() or 
                'api' in rel_path.lower() or
                file in ['main.py', 'app.py', 'server.py', 'settings.py', 'pyproject.toml', 'package.json']
                for _ in [1]
            )
            
            if Path(file).suffix in CODE_EXTENSIONS or file in ['pyproject.toml', 'package.json']:
                key_files.append((file_path, rel_path, is_priority))
    
    # Sort by priority
    key_files.sort(key=lambda x: (not x[2], x[1]))
    
    summary_parts.append("\n\n=== KEY FILES CONTENT ===\n")
    
    for file_path, rel_path, _ in key_files[:max_files]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Truncate large files
            if len(content) > 3000:
                content = content[:3000] + "\n... (truncated)"
            summary_parts.append(f"\n--- {rel_path} ---\n{content}\n")
        except (UnicodeDecodeError, IOError):
            continue
    
    return '\n'.join(summary_parts)


def extract_linked_files(doc_content: str, doc_path_obj: Path, repo_root: str) -> list[str]:
    """
    Extract linked code files from documentation.
    
    Strategy 1: Look for explicit CodeWiki tags <!-- codewiki:path/to/file -->
    Strategy 2: Look for implicit match (auth.md -> auth.py)
    
    Args:
        doc_content: The markdown content of the documentation file
        doc_path_obj: Path object of the documentation file
        repo_root: Root path of the repository
        
    Returns:
        List of absolute paths to linked code files
    """
    links = []
    
    # 1. Explicit Tags (Regex scan)
    # Supports: <!-- codewiki:path/to/file.py -->
    matches = re.findall(r'<!--\s*codewiki:\s*([^\s>]+)\s*-->', doc_content)
    for match in matches:
        full_path = os.path.join(repo_root, match.strip())
        if os.path.exists(full_path):
            links.append(full_path)
        else:
            # Try relative to doc location
            rel_path = doc_path_obj.parent / match.strip()
            if rel_path.exists():
                links.append(str(rel_path.resolve()))

    # 2. Implicit Match (if no tags found)
    if not links:
        # Extensions to check
        doc_stem = doc_path_obj.stem  # 'auth' from 'auth.md'
        
        for root, dirs, files in os.walk(repo_root):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            
            for file in files:
                if Path(file).stem.lower() == doc_stem.lower() and Path(file).suffix in CODE_EXTENSIONS:
                    links.append(os.path.join(root, file))
                    break  # Stop after first match for V1 simplicity
            if links:
                break
    
    return links


def audit_with_gemini(doc_text: str, code_text: str, filename: str, is_codebase_context: bool = False) -> str:
    """
    The 'Judge' Function - Compare documentation against code using Gemini.
    
    Args:
        doc_text: The documentation content
        code_text: The source code content or codebase summary
        filename: Name of the documentation file being audited
        is_codebase_context: Whether code_text is a codebase summary vs single file
        
    Returns:
        Audit result string - either "PASS" or a list of issues
    """
    context_type = "CODEBASE CONTEXT" if is_codebase_context else "CODE SPEC"
    
    prompt = f"""
ROLE: You are a Senior Software Architect auditing documentation for accuracy.

TASK: Compare the provided DOCUMENTATION against the actual {context_type}.
Identify FACTUAL inconsistencies including:
- Wrong API endpoints, routes, or URLs
- Incorrect function/method names or signatures
- Missing or incorrect parameters
- Outdated configuration or environment variables
- Logic that doesn't match the implementation
- Features documented but not implemented (or vice versa)

CONTEXT:
- Focus on "Drift" -> where the doc claims X but the code does Y.
- If the doc mentions routes/APIs, verify they exist in the code.
- If doc mentions specific files/modules, verify they exist.
- Ignore minor stylistic differences.

DOCUMENTATION ({filename}):
---
{doc_text[:15000]}
---

{context_type}:
---
{code_text[:50000]}
---

OUTPUT FORMAT:
If there are issues, return a bulleted list like:
• [ISSUE_TYPE] Description of the problem

Issue types: MISSING_ROUTE, WRONG_ENDPOINT, OUTDATED_PARAM, NOT_IMPLEMENTED, WRONG_PATH, CONFIG_DRIFT

If documentation is accurate, return exactly: PASS

Be terse and specific. No explanations.
"""

    try:
        client = get_audit_client()
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=4096,
            )
        )
        return response.text.strip() if response.text else "PASS"
    except Exception as e:
        return f"API Error: {str(e)}"


def run_audit(docs_folder: str, repo_folder: str, verbose: bool = False) -> int:
    """
    Run the documentation audit.
    
    Args:
        docs_folder: Path to the documentation folder
        repo_folder: Path to the repository root
        verbose: Whether to show verbose output
        
    Returns:
        Number of issues found
    """
    console.print(
        Panel.fit(
            "[bold blue]Secrin Auditor V1[/bold blue]\n"
            "[dim]Powered by Gemini 2.0 Flash[/dim]",
            border_style="blue"
        )
    )

    table = Table(title="Audit Results", show_lines=True)
    table.add_column("Document", style="cyan", no_wrap=True)
    table.add_column("Linked Code", style="magenta")
    table.add_column("Status", style="bold")
    table.add_column("AI Feedback", style="white", max_width=80)

    docs_path = Path(docs_folder)
    issues_found = 0
    docs_audited = 0
    
    # Pre-generate codebase summary for orphan docs
    console.print("[dim]Building codebase context...[/dim]")
    codebase_summary = get_codebase_summary(repo_folder)
    
    # Collect all docs to process
    doc_files = [f for f in docs_path.rglob('*.md') 
                 if f.name.lower() not in ['readme.md', 'changelog.md', 'license.md']]
    
    if not doc_files:
        console.print("[yellow]No documentation files found to audit.[/yellow]")
        return 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Auditing docs...", total=len(doc_files))
        
        for doc_file in doc_files:
            progress.update(task, description=f"Auditing [cyan]{doc_file.name}[/cyan]...")
            
            # Read Doc
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    doc_content = f.read()
            except UnicodeDecodeError:
                progress.advance(task)
                continue
            except Exception as e:
                if verbose:
                    console.print(f"[yellow]Warning: Could not read {doc_file}: {e}[/yellow]")
                progress.advance(task)
                continue

            # Skip empty or tiny docs
            if len(doc_content.strip()) < 20:
                table.add_row(
                    doc_file.name,
                    "[dim]N/A[/dim]",
                    "[yellow]SKIPPED[/yellow]",
                    "Doc too small to audit"
                )
                progress.advance(task)
                continue

            # Find Code
            linked_files = extract_linked_files(doc_content, doc_file, repo_folder)
            
            if linked_files:
                # Audit against specific linked file
                code_file_path = linked_files[0]
                rel_code_path = os.path.relpath(code_file_path, repo_folder)
                
                try:
                    with open(code_file_path, 'r', encoding='utf-8') as f:
                        code_content = f.read()
                except Exception as e:
                    table.add_row(
                        doc_file.name,
                        rel_code_path,
                        "[yellow]ERROR[/yellow]",
                        f"Could not read code file: {e}"
                    )
                    progress.advance(task)
                    continue

                result = audit_with_gemini(doc_content, code_content, doc_file.name, is_codebase_context=False)
                code_ref = rel_code_path
            else:
                # No linked file - audit against codebase context
                result = audit_with_gemini(doc_content, codebase_summary, doc_file.name, is_codebase_context=True)
                code_ref = "[dim]codebase[/dim]"
            
            docs_audited += 1

            if "PASS" in result.upper() and len(result) < 20:
                table.add_row(
                    doc_file.name,
                    code_ref,
                    "[green]PASS[/green]",
                    "✅ Accurate"
                )
            else:
                issues_found += 1
                # Format the AI output for the table
                formatted_feedback = result.replace("* ", "• ").replace("- ", "• ").strip()
                # Truncate long feedback for table display
                if len(formatted_feedback) > 300:
                    formatted_feedback = formatted_feedback[:297] + "..."
                table.add_row(
                    doc_file.name,
                    code_ref,
                    "[red]FAIL[/red]",
                    formatted_feedback
                )
            
            progress.advance(task)

    console.print(table)
    
    # Summary
    console.print(f"\n[bold]Summary:[/bold] {docs_audited} docs audited")
    
    if issues_found > 0:
        console.print(
            f"\n[bold red]✖ Audit Failed:[/bold red] "
            f"{issues_found} document(s) have drifted from code."
        )
    else:
        console.print(
            f"\n[bold green]✔ Audit Passed:[/bold green] "
            "All docs are synchronized with code."
        )
    
    return issues_found


@click.command()
@click.argument('docs_folder', type=click.Path(exists=True))
@click.argument('repo_folder', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Show verbose output')
def cli(docs_folder: str, repo_folder: str, verbose: bool):
    """
    Secrin Auditor: AI-powered documentation verification.
    
    DOCS_FOLDER: Path to your documentation folder (e.g., ./docs)
    REPO_FOLDER: Path to your repository root (e.g., ./src or .)
    
    Example:
        secrin-audit ./docs ./src
        python -m packages.auditor.audit ./docs .
    """
    issues = run_audit(docs_folder, repo_folder, verbose)
    raise SystemExit(1 if issues > 0 else 0)


if __name__ == '__main__':
    cli()
