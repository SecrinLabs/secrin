"""
CLI entry point for Secrin Auditor.
"""

import click
from .audit import run_audit


@click.command()
@click.argument('docs_folder', type=click.Path(exists=True))
@click.argument('repo_folder', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Show verbose output')
def main(docs_folder: str, repo_folder: str, verbose: bool):
    """
    Secrin Auditor: AI-powered documentation verification.
    
    Detects "drift" between your documentation and code.
    
    \b
    DOCS_FOLDER: Path to your documentation folder (e.g., ./docs)
    REPO_FOLDER: Path to your repository/codebase (e.g., ./src or .)
    
    \b
    Examples:
        secrin-audit ./docs ./src
        secrin-audit ./documentation .
        secrin-audit /path/to/docs /path/to/code --verbose
    
    \b
    Environment:
        GEMINI_API_KEY: Your Google Gemini API key (required)
                        Get one at: https://aistudio.google.com/
    
    \b
    Exit Codes:
        0: All documentation is accurate
        1: One or more documents have drifted from code
    """
    issues = run_audit(docs_folder, repo_folder, verbose)
    raise SystemExit(1 if issues > 0 else 0)


if __name__ == '__main__':
    main()
