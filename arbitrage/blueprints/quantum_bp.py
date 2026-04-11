"""
ADRION 369 - Quantum Blueprint: Kwantowy Modul Decyzyjny routes.

Routes:
  POST /api/arbitrage/quantum/decide
  GET  /api/arbitrage/quantum/status
  POST /api/arbitrage/quantum/scan
"""

import logging

from flask import Blueprint, jsonify, request

from arbitrage.blueprints import safe_float

quantum_bp = Blueprint("quantum", __name__)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Lazy imports
# ──────────────────────────────────────────────────────────────────────────────

def _quantum():
    from arbitrage.quantum import (
        entangle_markets,
        get_autopojeza_status,
        quantum_decide,
        run_quantum_scan,
    )
    return quantum_decide, entangle_markets, get_autopojeza_status, run_quantum_scan


def _rate_limiters():
    from arbitrage.rate_limiter import quantum_limiter
    return quantum_limiter


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@quantum_bp.route("/api/arbitrage/quantum/decide", methods=["POST"])
def handle_quantum_decide():
    """POST /api/arbitrage/quantum/decide -- Kwantowy Modul Decyzyjny."""
    quantum_limiter = _rate_limiters()
    client_ip = request.remote_addr
    if not quantum_limiter.is_allowed(client_ip):
        return jsonify({"error": "Rate limit exceeded", "retry_after": 60}), 429

    body = request.get_json(silent=True) or {}
    price_source = safe_float(body.get("price_source", 0))
    price_target = safe_float(body.get("price_target", 0))
    channel_id = body.get("channel_id", "AUDIO_PREMIUM")

    if price_source <= 0 or price_target <= 0:
        return jsonify({"error": "price_source and price_target must be > 0"}), 400

    quantum_decide, _, _, _ = _quantum()
    decision = quantum_decide(price_source, price_target, channel_id)
    return jsonify(decision.to_dict())


@quantum_bp.route("/api/arbitrage/quantum/status", methods=["GET"])
def handle_quantum_status():
    """GET /api/arbitrage/quantum/status -- Autopojeza status."""
    _, _, get_autopojeza_status, _ = _quantum()
    return jsonify(get_autopojeza_status())


@quantum_bp.route("/api/arbitrage/quantum/scan", methods=["POST"])
def handle_quantum_scan():
    """POST /api/arbitrage/quantum/scan -- Skan wszystkich kanalow."""
    quantum_limiter = _rate_limiters()
    client_ip = request.remote_addr
    if not quantum_limiter.is_allowed(client_ip):
        return jsonify({"error": "Rate limit exceeded", "retry_after": 60}), 429

    body = request.get_json(silent=True) or {}
    all_deals = body.get("deals", {})
    _, _, _, run_quantum_scan = _quantum()
    result = run_quantum_scan(all_deals)
    return jsonify(result)
