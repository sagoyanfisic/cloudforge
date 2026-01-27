#!/bin/bash

# Start both CloudForge API and UI
# Usage: ./scripts/start_all.sh

set -e

cd "$(dirname "$0")/.."

echo "🔥 Starting CloudForge (API + UI)..."
echo ""

# Start API in background
echo "📡 Starting API on http://localhost:8000..."
./scripts/start_api.sh &
API_PID=$!

# Wait for API to start
sleep 3

# Start UI in foreground
echo "🎨 Starting UI on http://localhost:8501..."
./scripts/start_ui.sh

# Cleanup on exit
trap "kill $API_PID" EXIT

