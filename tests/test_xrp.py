"""
Unit tests for arbitrage/xrp.py — XRP Tracker.
HTTP calls and DB calls are mocked; no network required.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# fetch_xrp_price_usd — success path
# ---------------------------------------------------------------------------

def test_fetch_xrp_price_success():
    payload = json.dumps({"ripple": {"usd": 2.35}}).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = payload
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("arbitrage.xrp.urlopen", return_value=mock_resp), \
         patch("arbitrage.xrp._cache_xrp_price") as mock_cache:
        from arbitrage.xrp import fetch_xrp_price_usd
        price = fetch_xrp_price_usd()

    assert price == pytest.approx(2.35)
    mock_cache.assert_called_once_with(2.35)


def test_fetch_xrp_price_fallback_on_url_error():
    from urllib.error import URLError
    with patch("arbitrage.xrp.urlopen", side_effect=URLError("timeout")), \
         patch("arbitrage.xrp._get_cached_xrp_price", return_value=1.80):
        from arbitrage.xrp import fetch_xrp_price_usd
        price = fetch_xrp_price_usd()
    assert price == pytest.approx(1.80)


def test_fetch_xrp_price_fallback_on_key_error():
    bad_payload = json.dumps({}).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = bad_payload
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("arbitrage.xrp.urlopen", return_value=mock_resp), \
         patch("arbitrage.xrp._get_cached_xrp_price", return_value=0.50):
        from arbitrage.xrp import fetch_xrp_price_usd
        price = fetch_xrp_price_usd()
    assert price == pytest.approx(0.50)


# ---------------------------------------------------------------------------
# _cache_xrp_price
# ---------------------------------------------------------------------------

def test_cache_xrp_price_writes_to_db():
    mock_conn = MagicMock()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_conn)
    cm.__exit__ = MagicMock(return_value=False)

    with patch("arbitrage.xrp.get_conn", return_value=cm):
        from arbitrage.xrp import _cache_xrp_price
        _cache_xrp_price(3.14)

    mock_conn.execute.assert_called_once()
    call_args = mock_conn.execute.call_args[0]
    assert "3.14" in call_args[1] or 3.14 in call_args[1]


# ---------------------------------------------------------------------------
# _get_cached_xrp_price
# ---------------------------------------------------------------------------

def test_get_cached_xrp_price_returns_cached():
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = {"value": "2.50"}
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_conn)
    cm.__exit__ = MagicMock(return_value=False)

    with patch("arbitrage.xrp.get_conn", return_value=cm):
        from arbitrage.xrp import _get_cached_xrp_price
        price = _get_cached_xrp_price()

    assert price == pytest.approx(2.50)


def test_get_cached_xrp_price_returns_default_when_empty():
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = None
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_conn)
    cm.__exit__ = MagicMock(return_value=False)

    with patch("arbitrage.xrp.get_conn", return_value=cm):
        from arbitrage.xrp import _get_cached_xrp_price
        price = _get_cached_xrp_price()

    assert price == pytest.approx(0.50)


def test_get_cached_xrp_price_exception_returns_default():
    with patch("arbitrage.xrp.get_conn", side_effect=RuntimeError("DB gone")):
        from arbitrage.xrp import _get_cached_xrp_price
        price = _get_cached_xrp_price()
    assert price == pytest.approx(0.50)


# ---------------------------------------------------------------------------
# total_earned_usd
# ---------------------------------------------------------------------------

def test_total_earned_usd_returns_float():
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = {"total": 250.75}
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_conn)
    cm.__exit__ = MagicMock(return_value=False)

    with patch("arbitrage.xrp.get_conn", return_value=cm):
        from arbitrage.xrp import total_earned_usd
        result = total_earned_usd()
    assert result == pytest.approx(250.75)


def test_total_earned_usd_none_row():
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = None
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_conn)
    cm.__exit__ = MagicMock(return_value=False)

    with patch("arbitrage.xrp.get_conn", return_value=cm):
        from arbitrage.xrp import total_earned_usd
        result = total_earned_usd()
    assert result == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# record_earning
# ---------------------------------------------------------------------------

def test_record_earning_inserts_to_db():
    mock_conn = MagicMock()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_conn)
    cm.__exit__ = MagicMock(return_value=False)

    with patch("arbitrage.xrp.get_conn", return_value=cm):
        from arbitrage.xrp import record_earning
        record_earning(150.0, source="stripe")

    mock_conn.execute.assert_called_once()
    args = mock_conn.execute.call_args[0]
    assert 150.0 in args[1]


def test_record_earning_zero_amount():
    mock_conn = MagicMock()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_conn)
    cm.__exit__ = MagicMock(return_value=False)

    with patch("arbitrage.xrp.get_conn", return_value=cm):
        from arbitrage.xrp import record_earning
        record_earning(0.0)  # should not raise


# ---------------------------------------------------------------------------
# get_progress
# ---------------------------------------------------------------------------

def test_get_progress_returns_dict_with_keys():
    with patch("arbitrage.xrp.fetch_xrp_price_usd", return_value=2.0), \
         patch("arbitrage.xrp.total_earned_usd", return_value=200.0):
        from arbitrage.xrp import get_progress
        result = get_progress()

    required = {"xrp_price_usd", "total_earned_usd", "xrp_earned",
                "xrp_target", "xrp_remaining", "pct_complete", "timestamp"}
    assert required.issubset(result.keys())


def test_get_progress_zero_price_no_division():
    with patch("arbitrage.xrp.fetch_xrp_price_usd", return_value=0.0), \
         patch("arbitrage.xrp.total_earned_usd", return_value=100.0):
        from arbitrage.xrp import get_progress
        result = get_progress()
    assert result["xrp_earned"] == 0.0


def test_get_progress_percentage_capped_at_100():
    with patch("arbitrage.xrp.fetch_xrp_price_usd", return_value=1.0), \
         patch("arbitrage.xrp.total_earned_usd", return_value=999999.0):
        from arbitrage.xrp import get_progress
        result = get_progress()
    assert result["pct_complete"] == pytest.approx(100.0)


def test_get_progress_correct_calculation():
    # 200 USD earned / 1.0 USD/XRP = 200 XRP / 1000 target = 20%
    with patch("arbitrage.xrp.fetch_xrp_price_usd", return_value=1.0), \
         patch("arbitrage.xrp.total_earned_usd", return_value=200.0):
        from arbitrage.xrp import get_progress
        result = get_progress()
    assert result["xrp_earned"] == pytest.approx(200.0)
    assert result["pct_complete"] == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# print_progress
# ---------------------------------------------------------------------------

def test_print_progress_outputs_to_stdout(capsys):
    with patch("arbitrage.xrp.get_progress", return_value={
        "xrp_price_usd": 2.0,
        "total_earned_usd": 100.0,
        "xrp_earned": 50.0,
        "xrp_target": 1000,
        "xrp_remaining": 950.0,
        "pct_complete": 5.0,
        "timestamp": "2026-04-05T10:00:00",
    }):
        from arbitrage.xrp import print_progress
        print_progress()
    out = capsys.readouterr().out
    assert "XRP" in out
    assert "5.0%" in out or "5.0" in out
