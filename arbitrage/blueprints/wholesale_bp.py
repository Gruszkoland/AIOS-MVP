"""
ADRION 369 - Wholesale Blueprint: B2B Wholesale routes.

Routes:
  POST /api/arbitrage/wholesale/scout
  POST /api/arbitrage/wholesale/cycle
  GET  /api/arbitrage/wholesale/deals
"""

import logging

from flask import Blueprint, jsonify, request

from arbitrage.blueprints import safe_float, safe_int

wholesale_bp = Blueprint("wholesale", __name__)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Lazy imports
# ──────────────────────────────────────────────────────────────────────────────

def _wholesale():
    from arbitrage.database import get_deals
    from arbitrage.wholesale_scout import scout_wholesale
    return scout_wholesale, get_deals


def _wholesale_cycle():
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    return run_wholesale_cycle


def _rate_limiters():
    from arbitrage.rate_limiter import cycle_limiter
    return cycle_limiter


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@wholesale_bp.route("/api/arbitrage/wholesale/scout", methods=["POST"])
def handle_wholesale_scout():
    """POST /api/arbitrage/wholesale/scout -- B2B Wholesale Scout Bridge."""
    body = request.get_json(silent=True) or {}
    feed_data = body.get("feed_data")
    feed_format = body.get("feed_format", "json")
    channel_filter = body.get("channel_filter")
    min_margin = safe_float(body.get("min_margin", 0.15))
    min_stock = safe_int(body.get("min_stock", 1))
    use_mock = body.get("use_mock", feed_data is None)
    scout_wholesale, _ = _wholesale()
    result = scout_wholesale(feed_data, feed_format, channel_filter,
                             min_margin, min_stock, use_mock)
    return jsonify(result)


@wholesale_bp.route("/api/arbitrage/wholesale/cycle", methods=["POST"])
def handle_wholesale_cycle():
    """POST /api/arbitrage/wholesale/cycle -- Full Singularity Run pipeline."""
    cycle_limiter = _rate_limiters()
    client_ip = request.remote_addr
    if not cycle_limiter.is_allowed(client_ip):
        return jsonify({"error": "Rate limit exceeded", "retry_after": 60}), 429

    body = request.get_json(silent=True) or {}
    channel_filter = body.get("channel_filter")
    min_margin = safe_float(body.get("min_margin", 0.15))
    auto_execute = body.get("auto_execute", False)
    use_mock = body.get("use_mock", True)
    cycle_fn = _wholesale_cycle()
    result = cycle_fn(
        channel_filter=channel_filter,
        min_margin=min_margin,
        auto_execute=auto_execute,
        use_mock=use_mock,
    )
    return jsonify(result)


@wholesale_bp.route("/api/arbitrage/wholesale/deals", methods=["GET"])
def handle_wholesale_deals():
    """GET /api/arbitrage/wholesale/deals -- Query stored deals."""
    channel_id = request.args.get("channel_id")
    status = request.args.get("status")
    min_margin_str = request.args.get("min_margin")
    min_margin = safe_float(min_margin_str) if min_margin_str is not None else None
    limit = safe_int(request.args.get("limit", "50"), default=50)
    _, get_deals = _wholesale()
    deals = get_deals(channel_id, status, min_margin, limit)
    return jsonify({"deals": deals, "count": len(deals)})
