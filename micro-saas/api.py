"""
ADRION 369 — micro-saas REST API
Port: 8003 (standalone) or mounted as /saas on UAP

Endpoints:
  GET  /saas/plans            — List all pricing tiers
  GET  /saas/products         — List products from product-manifest.json
  POST /saas/subscribe        — Create/upgrade subscription
  GET  /saas/quota/<user_id>  — Check bid quota for user
  GET  /saas/health           — Health probe

Auth: X-API-Key header (same UAP_API_KEY env var).
"""
from __future__ import annotations

import hmac
import json
import logging
import os
import sys
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import Blueprint, Flask, jsonify, request

# micro-saas folder has a hyphen so it cannot be imported as a normal package.
# Add its directory to sys.path so local imports inside billing.py resolve.
_SAAS_DIR = Path(__file__).parent
if str(_SAAS_DIR) not in sys.path:
    sys.path.insert(0, str(_SAAS_DIR))

from billing import (  # noqa: E402 — path manipulation above
    TIERS,
    check_bid_quota,
    consume_bid,
    create_subscription,
    get_subscription,
    init_saas_db,
)
from metrics import record_bid, record_bid_consumed, record_subscribe, prometheus_wsgi_app  # noqa: E402
from key_provider import get_api_key, register_sighup_handler  # noqa: E402

# ── Backend selection: SQLite (default) vs PostgreSQL ─────────────────────
_DB_DRIVER = os.getenv("SAAS_DB_DRIVER", "sqlite").lower()
if _DB_DRIVER == "postgres":
    from billing_pg import (  # type: ignore[assignment]  # noqa: E402
        check_bid_quota,
        consume_bid,
        create_subscription,
        get_subscription,
        init_saas_db,
    )
    logger_tmp = logging.getLogger("adrion.micro_saas.api")
    logger_tmp.info("billing backend: PostgreSQL (DATABASE_URL set)")

logger = logging.getLogger("adrion.micro_saas.api")

MANIFEST_PATH = Path(__file__).parent / "data" / "product-manifest.json"

saas_bp = Blueprint("saas", __name__, url_prefix="/saas")


# ── Auth decorator ────────────────────────────────────────────────────────

def require_api_key(f):
    @wraps(f)
    def _inner(*args, **kwargs):
        api_key = get_api_key()  # lazy — reads env on every request
        if not api_key:
            return jsonify({"error": "Server misconfigured: API key not set"}), 500
        key = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(key, api_key):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return _inner


# ── Endpoints ─────────────────────────────────────────────────────────────

@saas_bp.route("/plans", methods=["GET"])
def list_plans():
    """Public — no auth required. Returns all pricing tiers."""
    return jsonify({
        "plans": list(TIERS.values()),
        "currency": "EUR",
        "billing": "monthly",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@saas_bp.route("/products", methods=["GET"])
def list_products():
    """Public — returns product catalogue from product-manifest.json."""
    if not MANIFEST_PATH.exists():
        return jsonify({"error": "Product manifest not found"}), 404

    try:
        with MANIFEST_PATH.open(encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to load product manifest: %s", exc)
        return jsonify({"error": "Could not load product catalogue"}), 500

    channel = request.args.get("channel", "").upper()
    products = manifest.get("products", [])
    if channel:
        products = [p for p in products if p.get("channel") == channel]

    return jsonify({
        "total": len(products),
        "channels": manifest.get("channels", {}),
        "products": products,
        "generated_at": manifest.get("generated_at"),
    })


@saas_bp.route("/subscribe", methods=["POST"])
@require_api_key
def subscribe():
    """Create or upgrade a subscription.

    Body: {"user_id": "...", "tier": "free|pro|elite"}
    """
    body = request.get_json(silent=True) or {}
    user_id = (body.get("user_id") or "").strip()
    tier = (body.get("tier") or "free").strip().lower()

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    if tier not in TIERS:
        return jsonify({"error": f"Invalid tier. Valid: {list(TIERS)}"}), 400

    try:
        sub = create_subscription(user_id, tier)
        record_subscribe(tier)
    except Exception as exc:
        logger.error("Subscription creation failed: %s", exc)
        return jsonify({"error": "Subscription failed"}), 500

    tier_cfg = TIERS[tier]
    return jsonify({
        "success": True,
        "subscription": {
            "sub_id": sub.sub_id,
            "user_id": sub.user_id,
            "tier": sub.tier,
            "status": sub.status,
            "created_at": sub.created_at,
            "bids_per_day": tier_cfg["bids_per_day"],
            "rag_enabled": tier_cfg["rag_enabled"],
            "oracle_enabled": tier_cfg["oracle_enabled"],
        },
    }), 201


@saas_bp.route("/quota/<user_id>", methods=["GET"])
@require_api_key
def quota(user_id: str):
    """Check remaining bid quota for a user today."""
    if not user_id or len(user_id) > 128:
        return jsonify({"error": "Invalid user_id"}), 400

    allowed, reason = check_bid_quota(user_id)
    record_bid(allowed)
    sub = get_subscription(user_id)
    tier = sub.tier if sub else "none"

    return jsonify({
        "user_id": user_id,
        "tier": tier,
        "allowed": allowed,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@saas_bp.route("/health", methods=["GET"])
def health():
    """SaaS health probe."""
    return jsonify({
        "status": "ok",
        "service": "adrion-micro-saas",
        "version": "1.2.0",
        "manifest_present": MANIFEST_PATH.exists(),
    })


# ── Standalone app factory ─────────────────────────────────────────────────

def create_saas_app() -> Flask:
    """Create standalone SaaS Flask app (port 8003)."""
    from dotenv import load_dotenv
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    load_dotenv()

    app = Flask(__name__)
    app.register_blueprint(saas_bp)
    init_saas_db()

    # Mount Prometheus /metrics endpoint (no-op if prometheus_client not installed)
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": prometheus_wsgi_app()})  # type: ignore[method-assign]

    # Register SIGHUP handler for zero-downtime key rotation (POSIX only)
    register_sighup_handler()

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal(e):
        return jsonify({"error": "Internal server error"}), 500

    return app


if __name__ == "__main__":
    saas_app = create_saas_app()
    port = int(os.getenv("SAAS_PORT", "8003"))
    logger.info("Starting micro-saas on port %s", port)
    saas_app.run(host="0.0.0.0", port=port)
