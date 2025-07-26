#!/bin/bash

# Script to run the service/main.py with proper Python path and virtual environment

# Change to the project root directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH to include the current directory for proper module resolution
export PYTHONPATH=.

# Run the service
python service/main.py
