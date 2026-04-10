"""
ADRION 369 - Oracle Blueprint: Vortex Oracle routes.

Routes:
  POST /api/arbitrage/oracle/predict
  POST /api/arbitrage/oracle/scan
"""

import logging

from flask import Blueprint, jsonify, request

oracle_bp = Blueprint("oracle", __name__)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Lazy imports
# ──────────────────────────────────────────────────────────────────────────────

def _oracle():
    from arbitrage.oracle import oracle_predict, oracle_scan_products
    return oracle_predict, oracle_scan_products


def _rate_limiters():
    from arbitrage.rate_limiter import oracle_limiter
    return oracle_limiter


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@oracle_bp.route("/api/arbitrage/oracle/predict", methods=["POST"])
def handle_oracle_predict():
    """POST /api/arbitrage/oracle/predict -- Vortex Oracle single prediction."""
    oracle_limiter = _rate_limiters()
    client_ip = request.remote_addr
    if not oracle_limiter.is_allowed(client_ip):
        return jsonify({"error": "Rate limit exceeded", "retry_after": 60}), 429

    body = request.get_json(silent=True) or {}
    wholesale_price = float(body.get("wholesale_price", 0))
    retail_price = float(body.get("retail_price", 0))
    price_history = body.get("price_history", [])
    channel_id = body.get("channel_id", "AUDIO_PREMIUM")
    oracle_predict, _ = _oracle()
    prediction = oracle_predict(wholesale_price, retail_price, price_history, channel_id)
    return jsonify(prediction.to_dict())


@oracle_bp.route("/api/arbitrage/oracle/scan", methods=["POST"])
def handle_oracle_scan():
    """POST /api/arbitrage/oracle/scan -- Oracle batch product scan."""
    oracle_limiter = _rate_limiters()
    client_ip = request.remote_addr
    if not oracle_limiter.is_allowed(client_ip):
        return jsonify({"error": "Rate limit exceeded", "retry_after": 60}), 429

    body = request.get_json(silent=True) or {}
    products = body.get("products", [])
    channel_id = body.get("channel_id", "AUDIO_PREMIUM")
    _, oracle_scan_products = _oracle()
    result = oracle_scan_products(products, channel_id)
    return jsonify(result)
