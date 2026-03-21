#!/usr/bin/env bash
# Prometheus iQ — Start the live agent server
# Usage: bash start.sh [port]
set -euo pipefail

PORT="${1:-8000}"
ROOT="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$ROOT/.env" ]; then
  echo "ERROR: .env not found. Copy .env.example and fill in your keys:"
  echo "  cp .env.example .env"
  exit 1
fi

echo "=== Prometheus iQ Agent Server ==="
echo "Port:    $PORT"
echo "Docs:    http://localhost:$PORT/docs"
echo "Health:  http://localhost:$PORT/health"
echo ""
echo "To expose publicly:  ngrok http $PORT"
echo "  Then paste the ngrok URL into your ClickUp Automation webhook."
echo "=================================="

cd "$ROOT"
pip install -r requirements.txt --quiet

uvicorn src.server:app --host 0.0.0.0 --port "$PORT" --reload
