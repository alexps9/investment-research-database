#!/usr/bin/env bash
# Render.com startup script: run DB migrations then start the API server.
set -e

echo "Running database migrations…"
alembic upgrade head

echo "Starting API server on port ${PORT:-8000}…"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
