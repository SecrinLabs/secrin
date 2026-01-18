"""
Secrin Auditor - AI-powered documentation drift detection.

Ensure your docs stay in sync with your code using Gemini 2.0 Flash.
"""

from .audit import (
    run_audit,
    audit_with_gemini,
    extract_linked_files,
    get_codebase_summary,
)
from .cli import main

__version__ = "0.1.0"
__all__ = [
    "run_audit",
    "audit_with_gemini", 
    "extract_linked_files",
    "get_codebase_summary",
    "main",
]
