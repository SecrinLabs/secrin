"""
Secrin Auditor - AI-powered documentation verification tool.

This module provides tools to audit documentation against source code,
detecting drift and inconsistencies using Gemini 2.0 Flash.
"""

from .audit import run_audit, extract_linked_files, audit_with_gemini, cli

__all__ = ["run_audit", "extract_linked_files", "audit_with_gemini", "cli"]
