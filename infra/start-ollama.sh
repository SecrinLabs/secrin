#!/bin/sh
set -e

# Start Ollama server in background
ollama serve --host 0.0.0.0 &

# Wait until the server responds
until curl -s http://localhost:11434/health >/dev/null 2>&1; do
  echo "Waiting for Ollama to start..."
  sleep 2
done

# Pull models (idempotent)
echo "Pulling models..."
ollama pull mxbai-embed-large
ollama pull llama3.2:latest

# Keep the server running in foreground
wait
