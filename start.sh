#!/bin/bash
echo "🚀 Starting DevSecrin Developer Context Engine..."
echo

echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "🚀 Starting the application..."
pnpm run devsecrin
