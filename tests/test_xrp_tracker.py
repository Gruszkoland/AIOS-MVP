"""Tests for arbitrage/xrp_tracker.py — XRP price fetching and progress tracking."""
import sys
from unittest.mock import patch

import pytest


def get_xrp_tracker():
    import importlib
    if "arbitrage.xrp_tracker" in sys.modules:
        del sys.modules["arbitrage.xrp_tracker"]
    return importlib.import_module("arbitrage.xrp_tracker")


# ── fetch_xrp_price ───────────────────────────────────────────────────────────

class TestFetchXrpPrice:
    def test_fetches_from_coingecko(self, mock_requests_get_xrp):
        mod = get_xrp_tracker()
        with patch("arbitrage.xrp_tracker.requests.get", side_effect=mock_requests_get_xrp):
            price = mod.fetch_xrp_price()
        assert isinstance(price, float)
        assert price > 0

    def test_fallback_on_api_failure(self):
        mod = get_xrp_tracker()
        def _raise(*args, **kwargs):
            raise ConnectionError("network error")

        with patch("arbitrage.xrp_tracker.requests.get", side_effect=_raise):
            price = mod.fetch_xrp_price()
        # Should return FALLBACK_XRP_PRICE, not raise
        assert price == mod.FALLBACK_XRP_PRICE

    def test_returns_float(self, mock_requests_get_xrp):
        mod = get_xrp_tracker()
        with patch("arbitrage.xrp_tracker.requests.get", side_effect=mock_requests_get_xrp):
            price = mod.fetch_xrp_price()
        assert isinstance(price, float)

    def test_fallback_value_is_positive(self):
        mod = get_xrp_tracker()
        assert mod.FALLBACK_XRP_PRICE > 0


# ── calculate_xrp_progress ────────────────────────────────────────────────────

class TestCalcXrpProgress:
    def test_progress_zero_when_no_xrp(self):
        mod = get_xrp_tracker()
        if not hasattr(mod, "calculate_xrp_progress"):
            pytest.skip("calculate_xrp_progress not present in this version")
        prog = mod.calculate_xrp_progress(0.0, 2.0, 1000.0)
        assert prog["xrp_balance"] == 0.0
        assert prog["progress_pct"] == 0.0

    def test_progress_100_when_target_met(self):
        mod = get_xrp_tracker()
        if not hasattr(mod, "calculate_xrp_progress"):
            pytest.skip("calculate_xrp_progress not present in this version")
        prog = mod.calculate_xrp_progress(1000.0, 2.0, 1000.0)
        assert prog["progress_pct"] >= 100.0

    def test_usd_value_calculation(self):
        mod = get_xrp_tracker()
        if not hasattr(mod, "calculate_xrp_progress"):
            pytest.skip("calculate_xrp_progress not present in this version")
        prog = mod.calculate_xrp_progress(500.0, 2.0, 1000.0)
        assert prog["usd_value"] == pytest.approx(1000.0, rel=0.01)
