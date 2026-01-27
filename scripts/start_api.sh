#!/bin/bash

# Start CloudForge FastAPI server
# Usage: ./scripts/start_api.sh

set -e

cd "$(dirname "$0")/.."

echo "🔥 Starting CloudForge API..."
echo "📡 API will listen on http://0.0.0.0:8000"
echo ""

# Use venv python if available
if [ -d ".venv" ]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python"
fi

export GOOGLE_API_KEY="${GOOGLE_API_KEY:-}"

$PYTHON -m uvicorn src.api:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload

