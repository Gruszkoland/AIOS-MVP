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

from flask import Flask, jsonify
from flask_cors import CORS

logger = logging.getLogger(__name__)

_SERVER_START = time.time()
_CORS_ORIGIN = os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:8003")


def create_app() -> Flask:
    """Create and configure the Flask application with all blueprints."""
    app = Flask(__name__)
    CORS(app, origins=[_CORS_ORIGIN])

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
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "uptime": time.time() - _SERVER_START})

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
