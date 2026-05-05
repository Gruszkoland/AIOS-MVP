# ============================================================
# ADRION 369 — Multi-stage Dockerfile
# Entry point: wsgi.py -> arbitrage.app.create_app()
# ============================================================

# Stage 1: Builder — install Python dependencies into a prefix
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements-arbitrage.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements-arbitrage.txt

# Stage 2: Runtime — minimal image with only what the app needs
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1

WORKDIR /app

# Install dependencies from builder stage
COPY --from=builder /install /usr/local

# Create non-root user
RUN groupadd --system adrion && useradd --system --gid adrion --no-create-home adrion

# Copy application code
COPY arbitrage/ arbitrage/
COPY wsgi.py .

# Copy database migrations (needed for schema setup)
COPY db/migrations/ db/migrations/

# Copy runtime docs (openapi.yaml loaded by app.py, canonical laws reference)
COPY docs/openapi.yaml docs/openapi.yaml
COPY docs/GUARDIAN_LAWS_CANONICAL.json docs/GUARDIAN_LAWS_CANONICAL.json

# Set ownership and switch to non-root user
RUN chown -R adrion:adrion /app
USER adrion

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')" || exit 1

CMD ["python", "wsgi.py"]
