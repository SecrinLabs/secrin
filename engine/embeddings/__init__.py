"""
Embeddings module for DevSecrin Engine

This module provides embedding implementations for the graph-enhanced RAG system.
Sets up the Python path to ensure proper imports from the project root.
"""

import sys
import os

# Add the project root to sys.path to import config and service modules
_current_dir = os.path.dirname(__file__)
_project_root = os.path.join(_current_dir, '..', '..')
_project_root = os.path.abspath(_project_root)

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Clean up module-level variables
del _current_dir, _project_root
