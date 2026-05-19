#!/bin/sh
# ADRION 369 — micro-saas entrypoint
# 1. Run Alembic migrations (idempotent — safe to run on every startup)
# 2. Start Gunicorn WSGI server

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[entrypoint] Running Alembic migrations..."
cd "${SCRIPT_DIR}"
alembic -c alembic.ini upgrade head
echo "[entrypoint] Migrations complete."

echo "[entrypoint] Starting Gunicorn on port ${MCP_PORT:-8003}..."
exec gunicorn \
    --bind "0.0.0.0:${MCP_PORT:-8003}" \
    --workers 2 \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    "api:create_saas_app()"
