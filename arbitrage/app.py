"""
ADRION 369 - Flask Application Factory.

New entry point for the Arbitrage API using Flask blueprints.
Replaces the monolithic BaseHTTPRequestHandler in arbitrage/api.py.

Usage:
    from arbitrage.app import create_app
    app = create_app()
    app.run(host="0.0.0.0", port=8001)
"""

import logging
import os
import time

from flask import Flask, jsonify, request
from flask_cors import CORS

# ── Structured JSON logging for Loki/Grafana ────────────────────────────────
try:
    from pythonjsonlogger import jsonlogger
    _json_handler = logging.StreamHandler()
    _json_handler.setFormatter(jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    ))
    logging.root.handlers = [_json_handler]
    logging.root.setLevel(logging.INFO)
except ImportError:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

_SERVER_START = time.time()
_CORS_ORIGIN = os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:8003")


def create_app() -> Flask:
    """Create and configure the Flask application with all blueprints."""
    app = Flask(__name__)
    CORS(app, origins=[_CORS_ORIGIN])

    # ── CSRF Origin check ───────────────────────────────────────────────────
    _ALLOWED_ORIGINS = {_CORS_ORIGIN, "http://localhost:8003"}

    @app.before_request
    def _check_csrf():
        if request.method in ("POST", "PUT", "DELETE"):
            origin = request.headers.get("Origin")
            if origin and origin not in _ALLOWED_ORIGINS:
                return jsonify({"error": "Origin not allowed"}), 403

    # ── Register Blueprints ──────────────────────────────────────────────────
    from arbitrage.blueprints.arbitrage_bp import arbitrage_bp
    from arbitrage.blueprints.quantum_bp import quantum_bp
    from arbitrage.blueprints.oracle_bp import oracle_bp
    from arbitrage.blueprints.wholesale_bp import wholesale_bp
    from arbitrage.blueprints.payments_bp import payments_bp

    app.register_blueprint(arbitrage_bp)
    app.register_blueprint(quantum_bp)
    app.register_blueprint(oracle_bp)
    app.register_blueprint(wholesale_bp)
    app.register_blueprint(payments_bp)

    # ── Swagger UI / OpenAPI spec ──────────────────────────────────────────
    _SWAGGER_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>ADRION 369 API Docs</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({
            url: '/api/openapi.json',
            dom_id: '#swagger-ui',
        })
    </script>
</body>
</html>"""

    @app.route("/api/docs")
    def api_docs():
        """Serve Swagger UI for interactive API documentation."""
        return _SWAGGER_HTML, 200, {"Content-Type": "text/html"}

    @app.route("/api/openapi.json")
    def openapi_spec():
        """Serve the OpenAPI 3.1 specification as JSON."""
        import yaml
        spec_path = os.path.join(os.path.dirname(__file__), "..", "docs", "openapi.yaml")
        with open(spec_path, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        return jsonify(spec)

    # ── Prometheus /metrics endpoint ─────────────────────────────────────────
    @app.route("/metrics", methods=["GET"])
    def handle_metrics():
        """GET /metrics -- Prometheus text format metrics endpoint."""
        from arbitrage.metrics import pool_metrics
        snap = pool_metrics.snapshot()
        uptime = time.time() - _SERVER_START

        lines = [
            "# HELP adrion_requests_total Total requests processed per endpoint",
            "# TYPE adrion_requests_total counter",
            "# NOTE: Per-endpoint counters are tracked in-process; "
            "see arbitrage/api.py for the legacy counter implementation.",
            "",
            "# HELP adrion_db_pool_size Total connections in pool",
            "# TYPE adrion_db_pool_size gauge",
            f"adrion_db_pool_size {snap['pool_size']}",
            "",
            "# HELP adrion_db_pool_checked_out Connections currently in use",
            "# TYPE adrion_db_pool_checked_out gauge",
            f"adrion_db_pool_checked_out {snap['checked_out']}",
            "",
            "# HELP adrion_db_pool_checkouts_total Total DB connection checkouts",
            "# TYPE adrion_db_pool_checkouts_total counter",
            f"adrion_db_pool_checkouts_total {snap['total_checkouts']}",
            "",
            "# HELP adrion_db_pool_timeouts_total Total DB connection timeout events",
            "# TYPE adrion_db_pool_timeouts_total counter",
            f"adrion_db_pool_timeouts_total {snap['total_timeouts']}",
            "",
            "# HELP adrion_uptime_seconds Seconds since API server start",
            "# TYPE adrion_uptime_seconds gauge",
            f"adrion_uptime_seconds {uptime:.2f}",
            "",
        ]

        from flask import Response
        return Response(
            "\n".join(lines),
            mimetype="text/plain; version=0.0.4; charset=utf-8",
        )

    # ── Health check ─────────────────────────────────────────────────────────
    def _run_health_checks() -> dict:
        """Run cascade health checks against downstream dependencies."""
        checks: dict = {"uptime": round(time.time() - _SERVER_START, 2)}
        overall = True

        # DB check
        try:
            from arbitrage.database import get_conn
            conn = get_conn()
            conn.execute("SELECT 1")
            checks["db"] = "ok"
        except Exception as e:
            checks["db"] = f"error: {e}"
            overall = False

        # Ollama / LLM check (non-critical — degraded, not failure)
        try:
            import requests as _req
            resp = _req.get("http://localhost:11434/api/tags", timeout=2)
            checks["ollama"] = "ok" if resp.status_code == 200 else "degraded"
        except Exception:
            checks["ollama"] = "unreachable"

        checks["status"] = "healthy" if overall else "degraded"
        return checks

    @app.route("/health", methods=["GET"])
    def health():
        checks = _run_health_checks()
        status_code = 200 if checks["status"] == "healthy" else 503
        return jsonify(checks), status_code

    @app.route("/health/live", methods=["GET"])
    def liveness():
        """Liveness probe — returns 200 if the process is running."""
        return jsonify({"status": "alive"}), 200

    @app.route("/health/ready", methods=["GET"])
    def readiness():
        """Readiness probe — returns 503 if any critical dependency is down."""
        checks = _run_health_checks()
        status_code = 200 if checks["status"] == "healthy" else 503
        return jsonify(checks), status_code

    # ── Graceful shutdown ────────────────────────────────────────────────────
    import atexit
    import signal

    _shutdown_done = False

    def _shutdown():
        nonlocal _shutdown_done
        if _shutdown_done:
            return
        _shutdown_done = True
        try:
            logger.info("Graceful shutdown initiated")
        except Exception:
            pass
        try:
            from arbitrage.database import graceful_drain
            graceful_drain()
            logger.info("DB pool drained successfully")
        except Exception as e:
            try:
                logger.warning("Shutdown cleanup error: %s", e)
            except Exception:
                pass

    atexit.register(_shutdown)
    try:
        signal.signal(signal.SIGTERM, lambda signum, frame: _shutdown())
    except (OSError, AttributeError):
        pass  # SIGTERM not available on Windows

    # ── Error handlers ───────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Internal server error: %s", e)
        return jsonify({"error": "Internal server error"}), 500

    return app


def run_flask_server():
    """Initialise DB and start the Flask arbitrage API server (blocking)."""
    from arbitrage.database import init_db
    init_db()
    app = create_app()
    print(f"Arbitrage Flask API running on http://localhost:8001")
    app.run(host="0.0.0.0", port=8001, debug=False)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_flask_server()
