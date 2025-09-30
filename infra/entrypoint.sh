#!/bin/sh
# Simple entrypoint for devsecrin API container
# - run migrations if present
# - ensure chroma/gemini store directories exist
# - then start uvicorn

set -e

APP_DIR=/app
LOG_DIR=${APP_DIR}/logs
GEMINI_DIR=${APP_DIR}/gemini_store
CHROMA_DIR=${APP_DIR}/chroma_store

echo "[entrypoint] ensuring directories..."
mkdir -p "$LOG_DIR" "$GEMINI_DIR" "$CHROMA_DIR"

if [ -d "$APP_DIR/migration" ]; then
  echo "[entrypoint] running migrations (if any)..."
  # If you have a migration runner script provide it via migration/runner.py
  if command -v python >/dev/null 2>&1; then
    python -c "import migration.runner as r; r.run()" 2>/dev/null || true
  fi
fi

echo "[entrypoint] starting uvicorn"
exec uvicorn api.index:app --host 0.0.0.0 --port ${API_PORT:-8000}
