"""
Tests for arbitrage/app.py (Flask application factory) and all 5 blueprints.

Covers:
  - App factory (create_app) configuration
  - Blueprint registration (5 blueprints)
  - /health and /metrics root endpoints
  - 404 JSON error handler
  - Each blueprint: happy path + error/edge cases

All external dependencies (database, scout, analyzer, payments, rate limiters,
quantum, oracle, wholesale) are mocked so tests require no infrastructure.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from arbitrage.app import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app():
    """Create a Flask app instance configured for testing."""
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    """Flask test client bound to the testing app."""
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Shared mock helpers
# ---------------------------------------------------------------------------

def _allow_all_rate_limiter():
    """Return a MagicMock rate limiter that always allows requests."""
    limiter = MagicMock()
    limiter.is_allowed.return_value = True
    return limiter


def _deny_all_rate_limiter():
    """Return a MagicMock rate limiter that always denies requests."""
    limiter = MagicMock()
    limiter.is_allowed.return_value = False
    return limiter


def _mock_pool_metrics_snapshot():
    """Return a dict matching PoolMetrics.snapshot() shape."""
    return {
        "pool_size": 10,
        "checked_out": 2,
        "peak_checked_out": 5,
        "total_checkouts": 100,
        "total_timeouts": 0,
        "utilization_pct": 20.0,
    }


# ═══════════════════════════════════════════════════════════════════════════
# TASK 1: App Factory Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestCSRFOriginCheck:
    """Tests for the _check_csrf before_request hook (Origin/Referer validation)."""

    def test_post_with_bad_origin_returns_403(self, client):
        """POST from an untrusted Origin must be rejected with 403."""
        resp = client.post(
            "/health",
            headers={"Origin": "https://evil.example.com"},
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"] == "Origin not allowed"

    def test_post_with_bad_referer_returns_403(self, client):
        """POST with no Origin but an untrusted Referer must be rejected with 403."""
        resp = client.post(
            "/health",
            headers={"Referer": "https://evil.example.com/page"},
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"] == "Referer not allowed"

    def test_post_with_allowed_origin_passes(self, client):
        """POST from the allowed Origin should not be blocked by CSRF check."""
        resp = client.post(
            "/health",
            headers={"Origin": "http://localhost:8003"},
        )
        # Should not be 403 -- the endpoint itself may return 405 or 200
        assert resp.status_code != 403

    def test_post_without_origin_or_referer_passes(self, client):
        """Non-browser API requests (no Origin/Referer) should be allowed."""
        resp = client.post("/health")
        assert resp.status_code != 403

    def test_get_with_bad_origin_passes(self, client):
        """GET requests are exempt from CSRF check regardless of Origin."""
        resp = client.get(
            "/health",
            headers={"Origin": "https://evil.example.com"},
        )
        assert resp.status_code != 403

    def test_put_with_bad_origin_returns_403(self, client):
        """PUT from an untrusted Origin must also be rejected."""
        resp = client.put(
            "/health",
            headers={"Origin": "https://evil.example.com"},
        )
        assert resp.status_code == 403

    def test_delete_with_bad_origin_returns_403(self, client):
        """DELETE from an untrusted Origin must also be rejected."""
        resp = client.delete(
            "/health",
            headers={"Origin": "https://evil.example.com"},
        )
        assert resp.status_code == 403

    def test_patch_with_bad_origin_returns_403(self, client):
        """PATCH from an untrusted Origin must also be rejected."""
        resp = client.patch(
            "/health",
            headers={"Origin": "https://evil.example.com"},
        )
        assert resp.status_code == 403


class TestCreateApp:
    """Tests for create_app() and core Flask configuration."""

    def test_create_app_returns_flask_instance(self, app):
        from flask import Flask
        assert isinstance(app, Flask)

    def test_app_has_five_blueprints(self, app):
        expected = {"arbitrage", "quantum", "oracle", "wholesale", "payments"}
        registered = set(app.blueprints.keys())
        assert expected.issubset(registered), (
            f"Missing blueprints: {expected - registered}"
        )

    def test_app_has_exactly_five_blueprints(self, app):
        # The 5 user blueprints -- Flask may internally register others
        user_bps = {"arbitrage", "quantum", "oracle", "wholesale", "payments"}
        assert user_bps == set(app.blueprints.keys()) & user_bps

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "status" in data
        assert data["status"] in ("ok", "healthy", "degraded")

    def test_health_contains_uptime(self, client):
        resp = client.get("/health")
        data = resp.get_json()
        assert "uptime" in data
        assert isinstance(data["uptime"], (int, float))

    def test_metrics_returns_200(self, client):
        # pool_metrics is imported lazily inside handle_metrics via
        # ``from arbitrage.metrics import pool_metrics``
        mock_pm = MagicMock()
        mock_pm.snapshot.return_value = _mock_pool_metrics_snapshot()
        with patch("arbitrage.metrics.pool_metrics", mock_pm):
            resp = client.get("/metrics")
        assert resp.status_code == 200
        text = resp.get_data(as_text=True)
        assert "adrion_uptime_seconds" in text
        assert "adrion_db_pool_size" in text

    def test_metrics_content_type_is_prometheus(self, client):
        with patch("arbitrage.metrics.pool_metrics") as mock_pm:
            mock_pm.snapshot.return_value = _mock_pool_metrics_snapshot()
            resp = client.get("/metrics")
        assert "text/plain" in resp.content_type

    def test_unknown_route_returns_404_json(self, client):
        resp = client.get("/api/nonexistent/route")
        assert resp.status_code == 404
        data = resp.get_json()
        assert "error" in data

    def test_404_error_message(self, client):
        resp = client.get("/does/not/exist")
        data = resp.get_json()
        assert data["error"] == "Not found"


# ═══════════════════════════════════════════════════════════════════════════
# TASK 2: Arbitrage Blueprint Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestArbitrageBP:
    """Tests for arbitrage_bp endpoints."""

    @patch("arbitrage.blueprints.arbitrage_bp._db")
    @patch("arbitrage.blueprints.arbitrage_bp._config")
    def test_status_returns_200(self, mock_config, mock_db, client):
        mock_config.return_value = (50, 6.0, lambda: "ollama")
        mock_db.return_value = (
            MagicMock(),  # get_jobs
            MagicMock(return_value=[]),  # get_pending_bids
            MagicMock(),  # approve_bid
            MagicMock(return_value={"total_jobs": 10, "bids_sent": 3}),  # get_totals
            MagicMock(),  # init_db
        )
        resp = client.get("/api/arbitrage/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_jobs"] == 10
        assert data["bids_sent"] == 3
        assert "timestamp" in data
        assert "llm_backend" in data

    @patch("arbitrage.blueprints.arbitrage_bp._db")
    def test_kpis_returns_200_with_totals(self, mock_db, client):
        mock_db.return_value = (
            MagicMock(), MagicMock(), MagicMock(),
            MagicMock(return_value={"total_jobs": 5, "bids_sent": 2, "revenue": 120}),
            MagicMock(),
        )
        resp = client.get("/api/arbitrage/kpis")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "timestamp" in data
        assert data["total_jobs"] == 5

    @patch("arbitrage.blueprints.arbitrage_bp._db")
    def test_jobs_returns_list(self, mock_db, client):
        mock_db.return_value = (
            MagicMock(return_value=[{"id": "j1"}, {"id": "j2"}]),
            MagicMock(), MagicMock(), MagicMock(), MagicMock(),
        )
        resp = client.get("/api/arbitrage/jobs")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 2
        assert len(data["jobs"]) == 2

    @patch("arbitrage.blueprints.arbitrage_bp._db")
    def test_bids_pending_returns_list(self, mock_db, client):
        mock_db.return_value = (
            MagicMock(),
            MagicMock(return_value=[{"id": 1, "status": "pending"}]),
            MagicMock(), MagicMock(), MagicMock(),
        )
        resp = client.get("/api/arbitrage/bids/pending")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 1

    @patch("arbitrage.blueprints.arbitrage_bp._db")
    def test_bid_approve_calls_approve_bid(self, mock_db, client):
        approve_mock = MagicMock()
        mock_db.return_value = (
            MagicMock(), MagicMock(), approve_mock, MagicMock(), MagicMock(),
        )
        resp = client.post(
            "/api/arbitrage/bids/42/approve",
            json={"approved": True},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["bid_id"] == 42
        approve_mock.assert_called_once_with(42, True)

    @patch("arbitrage.blueprints.arbitrage_bp._rate_limiters")
    @patch("arbitrage.blueprints.arbitrage_bp._scout_fn")
    def test_scout_returns_200(self, mock_scout_fn, mock_rl, client):
        mock_rl.return_value = (_allow_all_rate_limiter(), MagicMock(), MagicMock())
        mock_scout_fn.return_value = MagicMock(return_value={"jobs_found": 5})
        resp = client.post("/api/arbitrage/scout")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["jobs_found"] == 5

    @patch("arbitrage.blueprints.arbitrage_bp._rate_limiters")
    def test_scout_rate_limited(self, mock_rl, client):
        mock_rl.return_value = (_deny_all_rate_limiter(), MagicMock(), MagicMock())
        resp = client.post("/api/arbitrage/scout")
        assert resp.status_code == 429
        data = resp.get_json()
        assert "Rate limit" in data["error"]

    @patch("arbitrage.blueprints.arbitrage_bp._rate_limiters")
    @patch("arbitrage.blueprints.arbitrage_bp._config")
    @patch("arbitrage.blueprints.arbitrage_bp._analyzer")
    @patch("arbitrage.blueprints.arbitrage_bp._db")
    def test_analyze_batch_returns_counts(
        self, mock_db, mock_analyzer, mock_config, mock_rl, client
    ):
        mock_rl.return_value = (MagicMock(), _allow_all_rate_limiter(), MagicMock())
        mock_config.return_value = (10, 6.0, MagicMock())
        jobs = [{"id": "j1"}, {"id": "j2"}]
        mock_db.return_value = (
            MagicMock(return_value=jobs),
            MagicMock(), MagicMock(), MagicMock(), MagicMock(),
        )
        mock_analyzer.return_value = (
            MagicMock(return_value={"score": 8}),  # analyze_job
            MagicMock(return_value=True),           # filter_worthy
            MagicMock(),                            # create_bid
        )
        resp = client.post("/api/arbitrage/analyze-batch")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["analyzed"] == 2
        assert data["bids_created"] == 2

    @patch("arbitrage.blueprints.arbitrage_bp._rate_limiters")
    def test_cycle_returns_ok(self, mock_rl, client):
        mock_rl.return_value = (MagicMock(), MagicMock(), _allow_all_rate_limiter())
        # cycle runs in a background thread -- we just verify the immediate response
        with patch("arbitrage.blueprints.arbitrage_bp._scout_fn"), \
             patch("arbitrage.blueprints.arbitrage_bp._db"), \
             patch("arbitrage.blueprints.arbitrage_bp._analyzer"), \
             patch("arbitrage.blueprints.arbitrage_bp._config"):
            resp = client.post("/api/arbitrage/cycle")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True

    @patch("arbitrage.blueprints.arbitrage_bp._rate_limiters")
    def test_cycle_rate_limited(self, mock_rl, client):
        mock_rl.return_value = (MagicMock(), MagicMock(), _deny_all_rate_limiter())
        resp = client.post("/api/arbitrage/cycle")
        assert resp.status_code == 429


# ═══════════════════════════════════════════════════════════════════════════
# TASK 3: Quantum Blueprint Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestQuantumBP:
    """Tests for quantum_bp endpoints."""

    @patch("arbitrage.blueprints.quantum_bp._rate_limiters")
    @patch("arbitrage.blueprints.quantum_bp._quantum")
    def test_decide_valid_body(self, mock_quantum, mock_rl, client):
        mock_rl.return_value = _allow_all_rate_limiter()
        decision = MagicMock()
        decision.to_dict.return_value = {
            "decision": "EXECUTE",
            "margin": 0.15,
            "channel_id": "AUDIO_PREMIUM",
        }
        mock_quantum.return_value = (
            MagicMock(return_value=decision),  # quantum_decide
            MagicMock(),  # entangle_markets
            MagicMock(),  # get_autopojeza_status
            MagicMock(),  # run_quantum_scan
        )
        resp = client.post(
            "/api/arbitrage/quantum/decide",
            json={"price_source": 10.0, "price_target": 15.0},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["decision"] == "EXECUTE"

    @patch("arbitrage.blueprints.quantum_bp._rate_limiters")
    def test_decide_empty_body_returns_400(self, mock_rl, client):
        mock_rl.return_value = _allow_all_rate_limiter()
        resp = client.post(
            "/api/arbitrage/quantum/decide",
            json={},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    @patch("arbitrage.blueprints.quantum_bp._rate_limiters")
    def test_decide_negative_prices_returns_400(self, mock_rl, client):
        mock_rl.return_value = _allow_all_rate_limiter()
        resp = client.post(
            "/api/arbitrage/quantum/decide",
            json={"price_source": -5.0, "price_target": 10.0},
        )
        assert resp.status_code == 400

    @patch("arbitrage.blueprints.quantum_bp._rate_limiters")
    def test_decide_rate_limited(self, mock_rl, client):
        mock_rl.return_value = _deny_all_rate_limiter()
        resp = client.post(
            "/api/arbitrage/quantum/decide",
            json={"price_source": 10.0, "price_target": 15.0},
        )
        assert resp.status_code == 429

    @patch("arbitrage.blueprints.quantum_bp._quantum")
    def test_quantum_status_returns_200(self, mock_quantum, client):
        mock_quantum.return_value = (
            MagicMock(),
            MagicMock(),
            MagicMock(return_value={"autopojeza": "stable", "resonance": 0.9}),
            MagicMock(),
        )
        resp = client.get("/api/arbitrage/quantum/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "autopojeza" in data

    @patch("arbitrage.blueprints.quantum_bp._rate_limiters")
    @patch("arbitrage.blueprints.quantum_bp._quantum")
    def test_quantum_scan_returns_200(self, mock_quantum, mock_rl, client):
        mock_rl.return_value = _allow_all_rate_limiter()
        mock_quantum.return_value = (
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(return_value={"scanned": 3, "opportunities": []}),
        )
        resp = client.post(
            "/api/arbitrage/quantum/scan",
            json={"deals": {"AUDIO_PREMIUM": []}},
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# TASK 4: Oracle Blueprint Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestOracleBP:
    """Tests for oracle_bp endpoints."""

    @patch("arbitrage.blueprints.oracle_bp._rate_limiters")
    @patch("arbitrage.blueprints.oracle_bp._oracle")
    def test_predict_valid_body(self, mock_oracle, mock_rl, client):
        mock_rl.return_value = _allow_all_rate_limiter()
        prediction = MagicMock()
        prediction.to_dict.return_value = {
            "predicted_price": 12.50,
            "confidence": 0.85,
        }
        mock_oracle.return_value = (
            MagicMock(return_value=prediction),  # oracle_predict
            MagicMock(),  # oracle_scan_products
        )
        resp = client.post(
            "/api/arbitrage/oracle/predict",
            json={
                "wholesale_price": 8.0,
                "retail_price": 15.0,
                "price_history": [7.5, 8.0, 8.2],
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["predicted_price"] == 12.50

    @patch("arbitrage.blueprints.oracle_bp._rate_limiters")
    @patch("arbitrage.blueprints.oracle_bp._oracle")
    def test_predict_missing_fields_uses_defaults(self, mock_oracle, mock_rl, client):
        """When wholesale_price and retail_price are missing, they default to 0."""
        mock_rl.return_value = _allow_all_rate_limiter()
        prediction = MagicMock()
        prediction.to_dict.return_value = {"predicted_price": 0, "confidence": 0}
        oracle_predict_mock = MagicMock(return_value=prediction)
        mock_oracle.return_value = (oracle_predict_mock, MagicMock())
        resp = client.post("/api/arbitrage/oracle/predict", json={})
        assert resp.status_code == 200
        # Verify the function was called with default values (0, 0, [], channel)
        oracle_predict_mock.assert_called_once_with(0.0, 0.0, [], "AUDIO_PREMIUM")

    @patch("arbitrage.blueprints.oracle_bp._rate_limiters")
    def test_predict_rate_limited(self, mock_rl, client):
        mock_rl.return_value = _deny_all_rate_limiter()
        resp = client.post(
            "/api/arbitrage/oracle/predict",
            json={"wholesale_price": 8.0, "retail_price": 15.0},
        )
        assert resp.status_code == 429

    @patch("arbitrage.blueprints.oracle_bp._rate_limiters")
    @patch("arbitrage.blueprints.oracle_bp._oracle")
    def test_scan_returns_200(self, mock_oracle, mock_rl, client):
        mock_rl.return_value = _allow_all_rate_limiter()
        mock_oracle.return_value = (
            MagicMock(),
            MagicMock(return_value={"products_scanned": 2, "results": []}),
        )
        resp = client.post(
            "/api/arbitrage/oracle/scan",
            json={"products": [{"name": "Widget A"}, {"name": "Widget B"}]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["products_scanned"] == 2

    @patch("arbitrage.blueprints.oracle_bp._rate_limiters")
    @patch("arbitrage.blueprints.oracle_bp._oracle")
    def test_scan_empty_products(self, mock_oracle, mock_rl, client):
        mock_rl.return_value = _allow_all_rate_limiter()
        scan_mock = MagicMock(return_value={"products_scanned": 0, "results": []})
        mock_oracle.return_value = (MagicMock(), scan_mock)
        resp = client.post("/api/arbitrage/oracle/scan", json={})
        assert resp.status_code == 200
        scan_mock.assert_called_once_with([], "AUDIO_PREMIUM")


# ═══════════════════════════════════════════════════════════════════════════
# TASK 5: Wholesale Blueprint Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestWholesaleBP:
    """Tests for wholesale_bp endpoints."""

    @patch("arbitrage.blueprints.wholesale_bp._wholesale")
    def test_scout_returns_200(self, mock_wholesale, client):
        mock_wholesale.return_value = (
            MagicMock(return_value={"deals_found": 3, "deals": []}),  # scout_wholesale
            MagicMock(),  # get_deals
        )
        resp = client.post("/api/arbitrage/wholesale/scout", json={})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["deals_found"] == 3

    @patch("arbitrage.blueprints.wholesale_bp._wholesale")
    def test_scout_with_params(self, mock_wholesale, client):
        scout_mock = MagicMock(return_value={"deals_found": 1})
        mock_wholesale.return_value = (scout_mock, MagicMock())
        resp = client.post(
            "/api/arbitrage/wholesale/scout",
            json={
                "feed_format": "csv",
                "channel_filter": "AUDIO_PREMIUM",
                "min_margin": 0.25,
                "min_stock": 10,
                "use_mock": True,
            },
        )
        assert resp.status_code == 200
        # Verify params passed through correctly
        call_args = scout_mock.call_args
        assert call_args[0][1] == "csv"  # feed_format
        assert call_args[0][2] == "AUDIO_PREMIUM"  # channel_filter
        assert call_args[0][3] == 0.25  # min_margin
        assert call_args[0][4] == 10  # min_stock

    @patch("arbitrage.blueprints.wholesale_bp._wholesale")
    def test_deals_returns_200(self, mock_wholesale, client):
        mock_wholesale.return_value = (
            MagicMock(),
            MagicMock(return_value=[{"id": "d1", "margin": 0.2}]),
        )
        resp = client.get("/api/arbitrage/wholesale/deals")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 1
        assert len(data["deals"]) == 1

    @patch("arbitrage.blueprints.wholesale_bp._wholesale")
    def test_deals_with_query_params(self, mock_wholesale, client):
        get_deals_mock = MagicMock(return_value=[])
        mock_wholesale.return_value = (MagicMock(), get_deals_mock)
        resp = client.get(
            "/api/arbitrage/wholesale/deals?channel_id=AUDIO&status=active&min_margin=0.1&limit=10"
        )
        assert resp.status_code == 200
        get_deals_mock.assert_called_once_with("AUDIO", "active", 0.1, 10)

    @patch("arbitrage.blueprints.wholesale_bp._rate_limiters")
    @patch("arbitrage.blueprints.wholesale_bp._wholesale_cycle")
    def test_cycle_returns_200(self, mock_cycle_fn, mock_rl, client):
        mock_rl.return_value = _allow_all_rate_limiter()
        mock_cycle_fn.return_value = MagicMock(
            return_value={"stage": "complete", "deals_processed": 5}
        )
        resp = client.post("/api/arbitrage/wholesale/cycle", json={"use_mock": True})
        assert resp.status_code == 200

    @patch("arbitrage.blueprints.wholesale_bp._rate_limiters")
    def test_cycle_rate_limited(self, mock_rl, client):
        mock_rl.return_value = _deny_all_rate_limiter()
        resp = client.post("/api/arbitrage/wholesale/cycle", json={})
        assert resp.status_code == 429


# ═══════════════════════════════════════════════════════════════════════════
# TASK 6: Payments Blueprint Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestPaymentsBP:
    """Tests for payments_bp endpoints."""

    @patch("arbitrage.blueprints.payments_bp._payments")
    def test_checkout_valid_body(self, mock_payments, client):
        mock_payments.return_value = (
            MagicMock(return_value={"url": "https://checkout.stripe.com/test"}),
            MagicMock(),
            MagicMock(),
        )
        resp = client.post(
            "/api/arbitrage/checkout",
            json={"tier": "pilot"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "url" in data

    @patch("arbitrage.blueprints.payments_bp._payments")
    def test_checkout_returns_400_when_no_url(self, mock_payments, client):
        mock_payments.return_value = (
            MagicMock(return_value={"error": "Invalid tier"}),
            MagicMock(),
            MagicMock(),
        )
        resp = client.post("/api/arbitrage/checkout", json={"tier": "invalid"})
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    @patch("arbitrage.blueprints.payments_bp._payments")
    def test_checkout_default_tier(self, mock_payments, client):
        create_mock = MagicMock(return_value={"url": "https://stripe.com/s"})
        mock_payments.return_value = (create_mock, MagicMock(), MagicMock())
        resp = client.post("/api/arbitrage/checkout", json={})
        assert resp.status_code == 200
        create_mock.assert_called_once_with(
            "pilot", "http://localhost:9000", "http://localhost:9000"
        )

    @patch("arbitrage.blueprints.payments_bp._payments")
    def test_webhook_invalid_json(self, mock_payments, client):
        mock_payments.return_value = (
            MagicMock(),
            MagicMock(return_value=True),  # verify_webhook_signature
            MagicMock(),
        )
        resp = client.post(
            "/api/arbitrage/webhook/stripe",
            data=b"not-json",
            content_type="application/octet-stream",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"] == "Invalid JSON"

    @patch("arbitrage.blueprints.payments_bp._payments")
    def test_webhook_valid_event(self, mock_payments, client):
        event_data = {"type": "checkout.session.completed", "data": {"object": {}}}
        handle_mock = MagicMock(return_value={"received": True})
        mock_payments.return_value = (
            MagicMock(),
            MagicMock(return_value=True),  # verify passes
            handle_mock,
        )
        resp = client.post(
            "/api/arbitrage/webhook/stripe",
            data=json.dumps(event_data),
            content_type="application/json",
        )
        assert resp.status_code == 200
        handle_mock.assert_called_once()

    @patch("arbitrage.blueprints.payments_bp._payments")
    def test_webhook_invalid_signature(self, mock_payments, client):
        mock_payments.return_value = (
            MagicMock(),
            MagicMock(return_value=False),  # verify fails
            MagicMock(),
        )
        with patch.dict("os.environ", {"STRIPE_WEBHOOK_SECRET": "whsec_test"}):
            resp = client.post(
                "/api/arbitrage/webhook/stripe",
                data=b'{"type":"test"}',
                content_type="application/json",
                headers={"Stripe-Signature": "bad_sig"},
            )
        assert resp.status_code == 401

    @patch("arbitrage.blueprints.payments_bp._rate_limiters")
    @patch("arbitrage.blueprints.payments_bp._mass_generator")
    def test_mass_generate_returns_200(self, mock_mass, mock_rl, client):
        mock_rl.return_value = _allow_all_rate_limiter()
        mock_mass.return_value = (
            MagicMock(return_value={"generated": 10, "errors": 0}),
            MagicMock(),
            MagicMock(),
        )
        resp = client.post("/api/arbitrage/mass-generate", json={})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["generated"] == 10

    @patch("arbitrage.blueprints.payments_bp._rate_limiters")
    def test_mass_generate_rate_limited(self, mock_rl, client):
        mock_rl.return_value = _deny_all_rate_limiter()
        resp = client.post("/api/arbitrage/mass-generate", json={})
        assert resp.status_code == 429

    @patch("arbitrage.blueprints.payments_bp._mass_generator")
    def test_manifest_returns_404_when_no_file(self, mock_mass, client, tmp_path):
        manifest_path = tmp_path / "manifest.json"
        mock_mass.return_value = (MagicMock(), MagicMock(), manifest_path)
        resp = client.get("/api/arbitrage/manifest")
        assert resp.status_code == 404
        data = resp.get_json()
        assert "error" in data

    @patch("arbitrage.blueprints.payments_bp._mass_generator")
    def test_manifest_returns_data_when_exists(self, mock_mass, client, tmp_path):
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {"products": [{"name": "Widget A"}], "count": 1}
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
        mock_mass.return_value = (MagicMock(), MagicMock(), manifest_path)
        resp = client.get("/api/arbitrage/manifest")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 1
