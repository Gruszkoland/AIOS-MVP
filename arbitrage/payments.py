"""
ADRION 369 — Stripe Payments Integration (PROGRAMATOR #8)
Webhook handler + checkout session creator for wholesale arbitrage SaaS.

Endpoints added to ArbitrageHandler:
  POST /api/arbitrage/checkout   — Create Stripe Checkout Session
  POST /api/arbitrage/webhook    — Stripe webhook receiver

Requires: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET in .env
"""
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime

logger = logging.getLogger("adrion.payments")

# ── Tier pricing (PLN, gross) ────────────────────────────────────────────────
TIERS = {
    "pilot":     {"price_cents": 4900,  "name": "Pilot",     "max_alerts": 3,  "channels": 1},
    "agresor":   {"price_cents": 14900, "name": "Agresor",   "max_alerts": 15, "channels": 3},
    "dominator": {"price_cents": 29900, "name": "Dominator", "max_alerts": 99, "channels": 5},
}


def _get_stripe():
    """Lazy import stripe to avoid hard dependency."""
    try:
        import os

        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
        return stripe
    except ImportError:
        logger.warning("stripe package not installed — payments disabled")
        return None


def create_checkout_session(tier: str, success_url: str, cancel_url: str) -> dict:
    """Create a Stripe Checkout Session for the given tier."""
    stripe = _get_stripe()
    if not stripe or not stripe.api_key:
        return {"error": "Stripe not configured", "mock": True, "url": success_url}

    tier_info = TIERS.get(tier)
    if not tier_info:
        return {"error": f"Unknown tier: {tier}"}

    session = stripe.checkout.Session.create(
        payment_method_types=["card", "blik", "p24"],
        line_items=[{
            "price_data": {
                "currency": "pln",
                "product_data": {"name": f"ADRION 369 — {tier_info['name']}"},
                "unit_amount": tier_info["price_cents"],
                "recurring": {"interval": "month"},
            },
            "quantity": 1,
        }],
        mode="subscription",
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
        metadata={"tier": tier},
    )
    return {"url": session.url, "session_id": session.id}


def verify_webhook_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """Verify Stripe webhook signature (v1)."""
    if not sig_header or not secret:
        return False
    try:
        elements = dict(item.split("=", 1) for item in sig_header.split(","))
        timestamp = elements.get("t", "")
        signature = elements.get("v1", "")
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        expected = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception as e:
        logger.warning("Webhook signature verification failed: %s", e)
        return False


def handle_webhook_event(event_data: dict) -> dict:
    """Process a verified Stripe webhook event."""
    event_type = event_data.get("type", "")
    obj = event_data.get("data", {}).get("object", {})

    result = {
        "event_type": event_type,
        "processed": True,
        "timestamp": datetime.now().isoformat(),
    }

    if event_type == "checkout.session.completed":
        tier = obj.get("metadata", {}).get("tier", "pilot")
        email = obj.get("customer_email") or obj.get("customer_details", {}).get("email")
        result["action"] = "subscription_created"
        result["tier"] = tier
        result["email"] = email
        _persist_payment_event(event_data, email)
        logger.info("Checkout completed: tier=%s email=%s", tier, email)

    elif event_type == "invoice.paid":
        result["action"] = "invoice_paid"
        result["amount"] = obj.get("amount_paid", 0)
        logger.info("Invoice paid: %s cents", obj.get("amount_paid", 0))

    elif event_type == "customer.subscription.deleted":
        result["action"] = "subscription_cancelled"
        logger.info("Subscription cancelled: %s", obj.get("id"))

    else:
        result["action"] = "ignored"
        result["processed"] = False

    return result


def _persist_payment_event(event_data: dict, email: str = None):
    """Log payment event to database."""
    try:
        from arbitrage.database import get_conn
        obj = event_data.get("data", {}).get("object", {})
        with get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO payment_events "
                "(stripe_event_id, event_type, amount_cents, currency, customer_email, meta_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    event_data.get("id", f"evt_{int(time.time())}"),
                    event_data.get("type", "unknown"),
                    obj.get("amount_total", 0),
                    obj.get("currency", "pln"),
                    email,
                    json.dumps({"session_id": obj.get("id")}, ensure_ascii=False),
                ),
            )
    except Exception as e:
        logger.warning("Failed to persist payment event: %s", e)
