#!/bin/bash

# Start CloudForge Streamlit UI
# Usage: ./scripts/start_ui.sh

set -e

cd "$(dirname "$0")/.."

echo "🎨 Starting CloudForge UI..."
echo "🌐 UI will open at http://localhost:8501"
echo ""

# Use venv python if available
if [ -d ".venv" ]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python"
fi

export CLOUDFORGE_API_URL="${CLOUDFORGE_API_URL:-http://localhost:8000}"

$PYTHON -m streamlit run ui/app.py \
    --server.port 8501 \
    --server.address localhost

