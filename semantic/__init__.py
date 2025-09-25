"""
Service package initialization.
Sets up the Python path to allow imports from the root project directory.
"""
import sys
import os

# Add root directory to sys.path for config imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# This allows all modules in the service package to import from config
