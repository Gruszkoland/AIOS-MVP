"""
Unit tests for arbitrage/stream_emitters.py — Auxiliary Stream Emitters.
All DB and network calls are mocked.
"""
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# _seeded_ratio — pure function
# ---------------------------------------------------------------------------

def test_seeded_ratio_returns_float_between_0_and_1():
    from arbitrage.stream_emitters import _seeded_ratio
    ratio = _seeded_ratio("test:seed:value")
    assert 0.0 <= ratio <= 1.0


def test_seeded_ratio_deterministic():
    from arbitrage.stream_emitters import _seeded_ratio
    r1 = _seeded_ratio("ugc:2026-04-05:WellnessLab")
    r2 = _seeded_ratio("ugc:2026-04-05:WellnessLab")
    assert r1 == r2


def test_seeded_ratio_different_seeds():
    from arbitrage.stream_emitters import _seeded_ratio
    r1 = _seeded_ratio("ugc:2026-04-05:BrandA")
    r2 = _seeded_ratio("ugc:2026-04-05:BrandB")
    assert r1 != r2


# ---------------------------------------------------------------------------
# _normalize_external_events — pure function
# ---------------------------------------------------------------------------

def test_normalize_none_payload_returns_empty():
    from arbitrage.stream_emitters import _normalize_external_events
    result = _normalize_external_events("ugc", None)
    assert result == []


def test_normalize_empty_list():
    from arbitrage.stream_emitters import _normalize_external_events
    result = _normalize_external_events("ugc", [])
    assert result == []


def test_normalize_list_payload():
    from arbitrage.stream_emitters import _normalize_external_events
    payload = [{"event_type": "ugc_deal_closed", "amount_usd": 150.0, "est_cost_usd": 1.5}]
    result = _normalize_external_events("ugc", payload)
    assert len(result) == 1
    assert result[0]["amount_usd"] == 150.0


def test_normalize_dict_with_events_key():
    from arbitrage.stream_emitters import _normalize_external_events
    payload = {"events": [{"amount_usd": 100.0, "est_cost_usd": 0.5}]}
    result = _normalize_external_events("ugc", payload)
    assert len(result) == 1


def test_normalize_dict_with_opportunities_key():
    from arbitrage.stream_emitters import _normalize_external_events
    payload = {"opportunities": [{"amount_usd": 50.0, "est_cost_usd": 0.2}]}
    result = _normalize_external_events("resale", payload)
    assert len(result) == 1


def test_normalize_non_dict_items_skipped():
    from arbitrage.stream_emitters import _normalize_external_events
    payload = [None, "not-a-dict", 42, {"amount_usd": 100.0, "est_cost_usd": 0.5}]
    result = _normalize_external_events("ugc", payload)
    assert len(result) == 1


def test_normalize_clamps_negative_values():
    from arbitrage.stream_emitters import _normalize_external_events
    payload = [{"amount_usd": -50.0, "est_cost_usd": -10.0}]
    result = _normalize_external_events("ugc", payload)
    assert result[0]["amount_usd"] == 0.0
    assert result[0]["est_cost_usd"] == 0.0


def test_normalize_defaults_ugc_event_type():
    from arbitrage.stream_emitters import _normalize_external_events
    payload = [{"amount_usd": 100.0, "est_cost_usd": 0.5, "brand": "TestBrand"}]
    result = _normalize_external_events("ugc", payload)
    assert result[0]["event_type"] == "ugc_deal_closed"


def test_normalize_defaults_resale_event_type():
    from arbitrage.stream_emitters import _normalize_external_events
    payload = [{"amount_usd": 60.0, "est_cost_usd": 0.3, "asset": "domain"}]
    result = _normalize_external_events("resale", payload)
    assert result[0]["event_type"] == "resale_flip_closed"


def test_normalize_ugc_pitch_when_zero_amount():
    from arbitrage.stream_emitters import _normalize_external_events
    payload = [{"amount_usd": 0, "est_cost_usd": 0.3}]
    result = _normalize_external_events("ugc", payload)
    assert result[0]["event_type"] == "ugc_pitch_sent"


def test_normalize_resale_listing_when_zero_amount():
    from arbitrage.stream_emitters import _normalize_external_events
    payload = [{"amount_usd": 0, "est_cost_usd": 0.3}]
    result = _normalize_external_events("resale", payload)
    assert result[0]["event_type"] == "resale_listing_created"


def test_normalize_invalid_numeric_skipped():
    from arbitrage.stream_emitters import _normalize_external_events
    payload = [{"amount_usd": "not-a-number", "est_cost_usd": 0.5}]
    result = _normalize_external_events("ugc", payload)
    assert len(result) == 0


def test_normalize_dict_with_items_key():
    from arbitrage.stream_emitters import _normalize_external_events
    payload = {"items": [{"amount_usd": 80.0, "est_cost_usd": 0.4}]}
    result = _normalize_external_events("ugc", payload)
    assert len(result) == 1


def test_normalize_invalid_raw_items():
    from arbitrage.stream_emitters import _normalize_external_events
    result = _normalize_external_events("ugc", 42)  # non-dict, non-list
    assert result == []


# ---------------------------------------------------------------------------
# _emit_events — with dry_run=True
# ---------------------------------------------------------------------------

def test_emit_events_dry_run_counts_without_db():
    from arbitrage.stream_emitters import _emit_events
    events = [
        {"event_type": "ugc_deal_closed", "amount_usd": 100.0, "est_cost_usd": 0.5, "meta": {}},
        {"event_type": "ugc_deal_closed", "amount_usd": 120.0, "est_cost_usd": 0.6, "meta": {}},
    ]
    count = _emit_events("ugc", events, dry_run=True)
    assert count == 2


def test_emit_events_dry_run_empty():
    from arbitrage.stream_emitters import _emit_events
    count = _emit_events("ugc", [], dry_run=True)
    assert count == 0


def test_emit_events_calls_record_kpi():
    from arbitrage.stream_emitters import _emit_events
    with patch("arbitrage.stream_emitters.record_kpi_event") as mock_record:
        events = [{"event_type": "ugc_deal_closed", "amount_usd": 100.0, "est_cost_usd": 0.5, "meta": {}}]
        count = _emit_events("ugc", events, dry_run=False)
    assert count == 1
    mock_record.assert_called_once()


# ---------------------------------------------------------------------------
# _fetch_external_payload
# ---------------------------------------------------------------------------

def test_fetch_returns_none_for_none_url():
    from arbitrage.stream_emitters import _fetch_external_payload
    result = _fetch_external_payload(None, "test")
    assert result is None


def test_fetch_returns_none_on_url_error():
    from urllib.error import URLError

    from arbitrage.stream_emitters import _fetch_external_payload
    with patch("arbitrage.stream_emitters.urlopen", side_effect=URLError("connection failed")):
        result = _fetch_external_payload("http://localhost:1/test", "test")
    assert result is None


def test_fetch_returns_parsed_json():
    import json as json_mod

    from arbitrage.stream_emitters import _fetch_external_payload
    mock_response = MagicMock()
    mock_response.read.return_value = json_mod.dumps({"events": []}).encode()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("arbitrage.stream_emitters.urlopen", return_value=mock_response):
        result = _fetch_external_payload("http://fake.url/events", "ugc")
    assert result == {"events": []}


# ---------------------------------------------------------------------------
# get_stream_sources_status — pure function
# ---------------------------------------------------------------------------

def test_get_stream_sources_status_keys():
    from arbitrage.stream_emitters import get_stream_sources_status
    status = get_stream_sources_status()
    assert "ugc_source_url_configured" in status
    assert "resale_source_url_configured" in status
    assert "connector_token_configured" in status
    for v in status.values():
        assert isinstance(v, bool)


# ---------------------------------------------------------------------------
# run_ugc_emitter — with mocked _daily_count + dry_run
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_daily_zero(monkeypatch):
    monkeypatch.setattr("arbitrage.stream_emitters._daily_count", lambda stream: 0)


@pytest.fixture
def mock_daily_capped(monkeypatch):
    monkeypatch.setattr("arbitrage.stream_emitters._daily_count", lambda stream: 100)


def test_run_ugc_emitter_dry_run(mock_daily_zero):
    from arbitrage.stream_emitters import run_ugc_emitter
    with patch("arbitrage.stream_emitters._fetch_external_payload", return_value=None):
        result = run_ugc_emitter(max_events_per_day=4, dry_run=True)
    assert result["stream"] == "ugc"
    assert result["emitted"] > 0
    assert result["source_mode"] == "seed"


def test_run_ugc_emitter_daily_cap_reached(mock_daily_capped):
    from arbitrage.stream_emitters import run_ugc_emitter
    result = run_ugc_emitter(max_events_per_day=4)
    assert result["emitted"] == 0
    assert result.get("reason") == "daily_cap_reached"


def test_run_ugc_emitter_external_source(mock_daily_zero):
    from arbitrage.stream_emitters import run_ugc_emitter
    external_events = [{"amount_usd": 150.0, "est_cost_usd": 0.5}]
    with patch("arbitrage.stream_emitters._fetch_external_payload", return_value=external_events):
        result = run_ugc_emitter(dry_run=True)
    assert result["source_mode"] == "external"
    assert result["emitted"] > 0


# ---------------------------------------------------------------------------
# run_resale_emitter
# ---------------------------------------------------------------------------

def test_run_resale_emitter_dry_run(mock_daily_zero):
    from arbitrage.stream_emitters import run_resale_emitter
    with patch("arbitrage.stream_emitters._fetch_external_payload", return_value=None):
        result = run_resale_emitter(max_events_per_day=4, dry_run=True)
    assert result["stream"] == "resale"
    assert result["emitted"] > 0
    assert result["source_mode"] == "seed"


def test_run_resale_emitter_daily_cap(mock_daily_capped):
    from arbitrage.stream_emitters import run_resale_emitter
    result = run_resale_emitter(max_events_per_day=4)
    assert result["emitted"] == 0


def test_run_resale_emitter_external_source(mock_daily_zero):
    from arbitrage.stream_emitters import run_resale_emitter
    payload = [{"amount_usd": 80.0, "est_cost_usd": 0.3}]
    with patch("arbitrage.stream_emitters._fetch_external_payload", return_value=payload):
        result = run_resale_emitter(dry_run=True)
    assert result["source_mode"] == "external"


# ---------------------------------------------------------------------------
# run_aux_streams
# ---------------------------------------------------------------------------

def test_run_aux_streams_returns_both(mock_daily_zero):
    from arbitrage.stream_emitters import run_aux_streams
    with patch("arbitrage.stream_emitters._fetch_external_payload", return_value=None):
        result = run_aux_streams(dry_run=True)
    assert "ugc" in result
    assert "resale" in result
    assert "timestamp" in result
    assert result["dry_run"] is True
