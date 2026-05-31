#!/bin/bash
# OddsIQ local dev startup
# Run this from the OddsIQ root: ./start.sh

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "▶ Starting Postgres + Redis..."
docker compose up postgres redis -d

echo "▶ Waiting for healthy containers..."
sleep 3

echo "▶ Running DB migrations..."
cd "$ROOT/backend"
uv run alembic upgrade head

echo "▶ Starting backend on :8000..."
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
sleep 3

echo "▶ Fetching initial live odds..."
curl -s -X POST http://localhost:8000/api/v1/admin/poll > /dev/null
echo "  Odds polled."

echo "▶ Starting frontend on :3000..."
cd "$ROOT/frontend"
pnpm dev &
FRONTEND_PID=$!

echo ""
echo "✅ OddsIQ is running:"
echo "   Frontend → http://localhost:3000"
echo "   Backend  → http://localhost:8000"
echo "   API docs → http://localhost:8000/docs"
echo ""
echo "To stop: kill $BACKEND_PID $FRONTEND_PID && docker compose stop"
wait
