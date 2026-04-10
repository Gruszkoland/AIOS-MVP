"""
ADRION 369 - Payments Blueprint: Stripe checkout and webhook routes.

Routes:
  POST /api/arbitrage/checkout
  POST /api/arbitrage/webhook/stripe
  POST /api/arbitrage/mass-generate
  GET  /api/arbitrage/manifest
"""

import json
import logging
import os

from flask import Blueprint, jsonify, request

payments_bp = Blueprint("payments", __name__)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Lazy imports
# ──────────────────────────────────────────────────────────────────────────────

def _payments():
    from arbitrage.payments import (
        create_checkout_session,
        handle_webhook_event,
        verify_webhook_signature,
    )
    return create_checkout_session, verify_webhook_signature, handle_webhook_event


def _mass_generator():
    from arbitrage.mass_generator import MANIFEST_FILE, generate_manifest, run_mass_generation
    return run_mass_generation, generate_manifest, MANIFEST_FILE


def _rate_limiters():
    from arbitrage.rate_limiter import mass_gen_limiter
    return mass_gen_limiter


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@payments_bp.route("/api/arbitrage/checkout", methods=["POST"])
def handle_checkout():
    """POST /api/arbitrage/checkout -- Create Stripe Checkout Session."""
    body = request.get_json(silent=True) or {}
    tier = body.get("tier", "pilot")
    success_url = body.get("success_url", "http://localhost:9000")
    cancel_url = body.get("cancel_url", "http://localhost:9000")
    create_checkout_session, _, _ = _payments()
    result = create_checkout_session(tier, success_url, cancel_url)
    code = 200 if "url" in result else 400
    return jsonify(result), code


@payments_bp.route("/api/arbitrage/webhook/stripe", methods=["POST"])
def handle_webhook():
    """POST /api/arbitrage/webhook/stripe -- Stripe webhook receiver."""
    payload = request.get_data()
    sig = request.headers.get("Stripe-Signature", "")
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    _, verify_webhook_signature, handle_webhook_event = _payments()
    if secret and not verify_webhook_signature(payload, sig, secret):
        return jsonify({"error": "Invalid signature"}), 401

    try:
        event_data = json.loads(payload)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 400

    result = handle_webhook_event(event_data)
    return jsonify(result)


@payments_bp.route("/api/arbitrage/mass-generate", methods=["POST"])
def handle_mass_generate():
    """POST /api/arbitrage/mass-generate -- Run Mass Generator pipeline."""
    mass_gen_limiter = _rate_limiters()
    client_ip = request.remote_addr
    if not mass_gen_limiter.is_allowed(client_ip):
        return jsonify({"error": "Rate limit exceeded", "retry_after": 60}), 429

    body = request.get_json(silent=True) or {}
    channel_filter = body.get("channel_filter")
    min_margin = float(body.get("min_margin", 0.15))
    min_stock = int(body.get("min_stock", 5))
    revalidate = body.get("revalidate", False)
    run_mass, _, _ = _mass_generator()
    result = run_mass(
        channel_filter=channel_filter,
        min_margin=min_margin,
        min_stock=min_stock,
        revalidate=revalidate,
    )
    return jsonify(result)


@payments_bp.route("/api/arbitrage/manifest", methods=["GET"])
def handle_get_manifest():
    """GET /api/arbitrage/manifest -- Return current product manifest."""
    _, _, manifest_file = _mass_generator()
    if manifest_file.exists():
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        return jsonify(manifest)
    else:
        return jsonify({"error": "No manifest generated yet. POST /api/arbitrage/mass-generate first."}), 404
