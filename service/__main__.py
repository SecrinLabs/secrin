#!/usr/bin/env python3
"""
DevSecrin Service Main Entry Point
Run from project root: python3 -m service.main
"""

if __name__ == "__main__":
    import sys
    import os
    from pathlib import Path
    
    # Add project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Import and run the main function
    from service.main import run_all_scrapers
    run_all_scrapers()
