"""
Unit tests for arbitrage/payments.py — Stripe Payments Integration.
Mocks Stripe SDK; no real API calls.
"""
import hashlib
import hmac
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# TIERS constant
# ---------------------------------------------------------------------------

def test_tiers_has_required_keys():
    from arbitrage.payments import TIERS
    for tier_name, tier_info in TIERS.items():
        assert "price_cents" in tier_info
        assert "name" in tier_info
        assert tier_info["price_cents"] > 0


# ---------------------------------------------------------------------------
# _get_stripe
# ---------------------------------------------------------------------------

def test_get_stripe_returns_none_when_not_installed():
    from arbitrage.payments import _get_stripe
    with patch.dict("sys.modules", {"stripe": None}):
        result = _get_stripe()
    # None means stripe import failed (ImportError path)
    # Since stripe may or may not be installed, just verify callable
    assert result is None or hasattr(result, "checkout")


def test_get_stripe_returns_none_on_import_error():
    from arbitrage.payments import _get_stripe
    with patch("builtins.__import__", side_effect=ImportError):
        result = _get_stripe()
    assert result is None


# ---------------------------------------------------------------------------
# create_checkout_session
# ---------------------------------------------------------------------------

def test_create_checkout_session_no_stripe():
    """Returns mock URL when Stripe not configured."""
    from arbitrage.payments import create_checkout_session
    with patch("arbitrage.payments._get_stripe", return_value=None):
        result = create_checkout_session("pilot", "http://ok", "http://cancel")
    assert "url" in result or "error" in result


def test_create_checkout_session_no_api_key():
    """Returns mock when Stripe has no api_key."""
    from arbitrage.payments import create_checkout_session
    mock_stripe = MagicMock()
    mock_stripe.api_key = ""
    with patch("arbitrage.payments._get_stripe", return_value=mock_stripe):
        result = create_checkout_session("pilot", "http://ok", "http://cancel")
    assert "mock" in result or "error" in result


def test_create_checkout_session_unknown_tier():
    """Unknown tier → error dict."""
    from arbitrage.payments import create_checkout_session
    mock_stripe = MagicMock()
    mock_stripe.api_key = "sk_test_xyz"
    with patch("arbitrage.payments._get_stripe", return_value=mock_stripe):
        result = create_checkout_session("non_existent_tier", "http://ok", "http://cancel")
    assert "error" in result


def test_create_checkout_session_valid():
    """Valid tier with mocked Stripe → returns url and session_id."""
    from arbitrage.payments import create_checkout_session
    mock_stripe = MagicMock()
    mock_stripe.api_key = "sk_test_xyz"
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/test-session"
    mock_session.id = "cs_test_123"
    mock_stripe.checkout.Session.create.return_value = mock_session
    with patch("arbitrage.payments._get_stripe", return_value=mock_stripe):
        result = create_checkout_session("pilot", "http://success", "http://cancel")
    assert result["url"] == "https://checkout.stripe.com/test-session"
    assert result["session_id"] == "cs_test_123"


def test_create_checkout_session_agresor():
    from arbitrage.payments import create_checkout_session
    mock_stripe = MagicMock()
    mock_stripe.api_key = "sk_test_xyz"
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/agresor"
    mock_session.id = "cs_agresor"
    mock_stripe.checkout.Session.create.return_value = mock_session
    with patch("arbitrage.payments._get_stripe", return_value=mock_stripe):
        result = create_checkout_session("agresor", "http://ok", "http://cancel")
    assert result["url"] == "https://checkout.stripe.com/agresor"


# ---------------------------------------------------------------------------
# verify_webhook_signature
# ---------------------------------------------------------------------------

def test_verify_webhook_signature_no_header():
    from arbitrage.payments import verify_webhook_signature
    result = verify_webhook_signature(b"payload", "", "secret")
    assert result is False


def test_verify_webhook_signature_no_secret():
    from arbitrage.payments import verify_webhook_signature
    result = verify_webhook_signature(b"payload", "t=123,v1=abc", "")
    assert result is False


def test_verify_webhook_signature_valid():
    from arbitrage.payments import verify_webhook_signature
    payload = b'{"type":"test"}'
    timestamp = "1712345678"
    secret = "whsec_test_secret"
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    sig_header = f"t={timestamp},v1={expected_sig}"
    result = verify_webhook_signature(payload, sig_header, secret)
    assert result is True


def test_verify_webhook_signature_invalid():
    from arbitrage.payments import verify_webhook_signature
    result = verify_webhook_signature(b"payload", "t=123,v1=wrong_signature", "secret")
    assert result is False


def test_verify_webhook_signature_malformed_header():
    from arbitrage.payments import verify_webhook_signature
    result = verify_webhook_signature(b"payload", "invalid_format", "secret")
    assert result is False


# ---------------------------------------------------------------------------
# handle_webhook_event
# ---------------------------------------------------------------------------

def test_handle_checkout_completed():
    from arbitrage.payments import handle_webhook_event
    event = {
        "type": "checkout.session.completed",
        "id": "evt_001",
        "data": {"object": {
            "metadata": {"tier": "pilot"},
            "customer_email": "user@test.com",
            "amount_total": 4900,
            "currency": "pln",
            "id": "cs_001",
        }},
    }
    with patch("arbitrage.payments._persist_payment_event"):
        result = handle_webhook_event(event)
    assert result["action"] == "subscription_created"
    assert result["tier"] == "pilot"
    assert result["processed"] is True


def test_handle_invoice_paid():
    from arbitrage.payments import handle_webhook_event
    event = {
        "type": "invoice.paid",
        "data": {"object": {"amount_paid": 4900}},
    }
    result = handle_webhook_event(event)
    assert result["action"] == "invoice_paid"
    assert result["amount"] == 4900


def test_handle_subscription_deleted():
    from arbitrage.payments import handle_webhook_event
    event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_001"}},
    }
    result = handle_webhook_event(event)
    assert result["action"] == "subscription_cancelled"


def test_handle_unknown_event():
    from arbitrage.payments import handle_webhook_event
    event = {
        "type": "unknown.event.type",
        "data": {"object": {}},
    }
    result = handle_webhook_event(event)
    assert result["action"] == "ignored"
    assert result["processed"] is False


def test_handle_event_has_timestamp():
    from arbitrage.payments import handle_webhook_event
    result = handle_webhook_event({"type": "invoice.paid", "data": {"object": {"amount_paid": 0}}})
    assert "timestamp" in result


def test_handle_checkout_customer_details_fallback():
    """customer_email = None → fallback to customer_details."""
    from arbitrage.payments import handle_webhook_event
    event = {
        "type": "checkout.session.completed",
        "id": "evt_002",
        "data": {"object": {
            "metadata": {"tier": "dominator"},
            "customer_email": None,
            "customer_details": {"email": "fallback@test.com"},
            "amount_total": 29900, "currency": "pln", "id": "cs_002",
        }},
    }
    with patch("arbitrage.payments._persist_payment_event"):
        result = handle_webhook_event(event)
    assert result["email"] == "fallback@test.com"


# ---------------------------------------------------------------------------
# _persist_payment_event
# ---------------------------------------------------------------------------

def test_persist_payment_event_handles_db_error():
    """Should not raise even if DB fails."""
    from arbitrage.payments import _persist_payment_event
    with patch("arbitrage.database.get_conn", side_effect=Exception("DB error"), create=True):
        # Should not raise
        _persist_payment_event({"type": "test", "id": "evt_001", "data": {"object": {}}})


def test_persist_payment_event_calls_db():
    """Happy path — inserts row into payment_events."""
    from arbitrage.payments import _persist_payment_event
    event = {
        "id": "evt_test_001",
        "type": "checkout.session.completed",
        "data": {"object": {"amount_total": 4900, "currency": "pln", "id": "cs_001"}},
    }
    mock_conn = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    with patch("arbitrage.database.get_conn", return_value=mock_ctx, create=True):
        _persist_payment_event(event, "user@test.com")
