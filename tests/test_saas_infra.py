"""
Tests for micro-saas metrics.py and key_provider.py modules.

Covers:
  metrics.py  — Counter registration, record_* helpers, NullCounter fallback,
                prometheus_wsgi_app returns callable, WSGI stub when disabled.
  key_provider.py — get_api_key lazy reads env, is_key_set, SIGHUP handler
                    registration (mock), no-op on Windows-like env.

Run: pytest tests/test_saas_infra.py -v
"""
from __future__ import annotations

import importlib
import signal
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── path setup ────────────────────────────────────────────────────────────

_SAAS_DIR = Path(__file__).parent.parent / "micro-saas"
if str(_SAAS_DIR) not in sys.path:
    sys.path.insert(0, str(_SAAS_DIR))


# ═════════════════════════════════════════════════════════════════════════
# key_provider tests
# ═════════════════════════════════════════════════════════════════════════

class TestKeyProvider:
    """Lazy API key loading and SIGHUP handler."""

    def test_get_api_key_reads_env_dynamically(self, monkeypatch):
        """Each call to get_api_key() reflects current env — no caching."""
        import key_provider

        monkeypatch.setenv("UAP_API_KEY", "first-key")
        assert key_provider.get_api_key() == "first-key"

        monkeypatch.setenv("UAP_API_KEY", "rotated-key")
        assert key_provider.get_api_key() == "rotated-key"

    def test_get_api_key_returns_empty_when_unset(self, monkeypatch):
        """Returns '' when env var is absent."""
        import key_provider

        monkeypatch.delenv("UAP_API_KEY", raising=False)
        assert key_provider.get_api_key() == ""

    def test_is_key_set_true(self, monkeypatch):
        import key_provider

        monkeypatch.setenv("UAP_API_KEY", "some-key")
        assert key_provider.is_key_set() is True

    def test_is_key_set_false(self, monkeypatch):
        import key_provider

        monkeypatch.delenv("UAP_API_KEY", raising=False)
        assert key_provider.is_key_set() is False

    def test_register_sighup_handler_on_posix(self, monkeypatch):
        """register_sighup_handler() installs handler when SIGHUP available."""
        import key_provider

        fake_signal = MagicMock()
        monkeypatch.setattr(signal, "SIGHUP", signal.SIGHUP, raising=False)
        monkeypatch.setattr(signal, "signal", fake_signal)
        key_provider.register_sighup_handler()
        # Should have been called with SIGHUP and our handler
        fake_signal.assert_called_once_with(signal.SIGHUP, key_provider._handle_sighup)

    def test_register_sighup_noop_when_no_sighup(self, monkeypatch):
        """On Windows (no SIGHUP), register_sighup_handler() is a no-op."""
        import key_provider

        # Simulate Windows: remove SIGHUP attribute
        monkeypatch.delattr(signal, "SIGHUP", raising=False)
        # Should not raise
        key_provider.register_sighup_handler()

    def test_handle_sighup_logs_rotation(self, monkeypatch, caplog):
        """_handle_sighup logs the rotation event without raising."""
        import key_provider
        import logging

        monkeypatch.setenv("UAP_API_KEY", "new-key-after-rotation")
        with caplog.at_level(logging.INFO, logger="adrion.micro_saas.key_provider"):
            key_provider._handle_sighup(0, None)

        assert "reloaded" in caplog.text.lower() or "SIGHUP" in caplog.text


# ═════════════════════════════════════════════════════════════════════════
# metrics tests
# ═════════════════════════════════════════════════════════════════════════

class TestMetricsWithPrometheus:
    """Tests run only when prometheus_client is installed."""

    @pytest.fixture(autouse=True)
    def require_prometheus(self):
        pytest.importorskip("prometheus_client")

    def test_subscribe_counter_registered(self):
        """SUBSCRIBE_COUNTER is a real Prometheus Counter."""
        from prometheus_client import Counter
        import metrics

        assert isinstance(metrics.SUBSCRIBE_COUNTER, Counter)

    def test_bid_counter_registered(self):
        from prometheus_client import Counter
        import metrics

        assert isinstance(metrics.BID_COUNTER, Counter)

    def test_bid_consume_counter_registered(self):
        from prometheus_client import Counter
        import metrics

        assert isinstance(metrics.BID_CONSUME_COUNTER, Counter)

    def test_record_subscribe_increments_counter(self):
        """record_subscribe('pro') increments the 'pro' label bucket."""
        from prometheus_client import REGISTRY
        import metrics

        before = self._get_counter_value("saas_subscriptions_total", {"tier": "pro"})
        metrics.record_subscribe("pro")
        after = self._get_counter_value("saas_subscriptions_total", {"tier": "pro"})
        assert after == before + 1.0

    def test_record_bid_allowed_increments(self):
        from prometheus_client import REGISTRY
        import metrics

        before = self._get_counter_value("saas_bids_total", {"allowed": "true"})
        metrics.record_bid(allowed=True)
        after = self._get_counter_value("saas_bids_total", {"allowed": "true"})
        assert after == before + 1.0

    def test_record_bid_denied_increments(self):
        import metrics

        before = self._get_counter_value("saas_bids_total", {"allowed": "false"})
        metrics.record_bid(allowed=False)
        after = self._get_counter_value("saas_bids_total", {"allowed": "false"})
        assert after == before + 1.0

    def test_record_bid_consumed_increments(self):
        import metrics

        before = self._get_counter_value("saas_bid_consumed_total", {})
        metrics.record_bid_consumed()
        after = self._get_counter_value("saas_bid_consumed_total", {})
        assert after == before + 1.0

    def test_prometheus_wsgi_app_returns_callable(self):
        import metrics

        app = metrics.prometheus_wsgi_app()
        assert callable(app)

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _get_counter_value(metric_name: str, labels: dict) -> float:
        """Read current value of a labelled counter from REGISTRY."""
        from prometheus_client import REGISTRY

        for metric in REGISTRY.collect():
            if metric.name == metric_name:
                for sample in metric.samples:
                    if sample.name == metric_name + "_total":
                        if all(sample.labels.get(k) == v for k, v in labels.items()):
                            return sample.value
        return 0.0


class TestMetricsNullCounter:
    """Fallback NullCounter behaviour when prometheus_client is absent."""

    @pytest.fixture(autouse=True)
    def patch_out_prometheus(self, monkeypatch):
        """Make metrics module believe prometheus_client is not installed."""
        # Force reimport with _ENABLED=False by patching the module attribute
        import metrics
        monkeypatch.setattr(metrics, "_ENABLED", False)
        # Re-assign counters to NullCounter instances
        null = metrics._NullCounter()
        monkeypatch.setattr(metrics, "SUBSCRIBE_COUNTER", null)
        monkeypatch.setattr(metrics, "BID_COUNTER", null)
        monkeypatch.setattr(metrics, "BID_CONSUME_COUNTER", null)

    def test_record_subscribe_noop(self):
        """record_subscribe does not raise when prometheus_client absent."""
        import metrics
        metrics.record_subscribe("free")  # should not raise

    def test_record_bid_noop(self):
        import metrics
        metrics.record_bid(allowed=True)  # should not raise

    def test_record_bid_consumed_noop(self):
        import metrics
        metrics.record_bid_consumed()  # should not raise

    def test_prometheus_wsgi_app_returns_stub(self):
        """prometheus_wsgi_app returns a stub WSGI callable that yields 200."""
        import metrics

        app = metrics.prometheus_wsgi_app()
        assert callable(app)

        # Call the stub WSGI app
        responses: list = []
        def start_response(status, headers):
            responses.append(status)

        body = list(app({}, start_response))
        assert responses == ["200 OK"]
        assert b"prometheus_client" in body[0]
