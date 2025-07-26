#!/bin/bash
# DevSecrin Service Runner
# Sets up the environment and runs the service

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get the project root directory (one level up from script directory)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Set PYTHONPATH to include the project root
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Run the service
python3 "$PROJECT_ROOT/service/main.py" "$@"
