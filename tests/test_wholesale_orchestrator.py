"""
Unit tests for arbitrage/wholesale_orchestrator.py — Wholesale Pipeline Orchestrator.
All external calls mocked.
"""
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Fixtures — mock all dependencies using monkeypatch
# ---------------------------------------------------------------------------

def _make_scout_result():
    return {
        "new_deals": 2, "updated_deals": 0, "total_parsed": 10, "total_qualified": 2,
        "mode": "mock", "deals": [
            {
                "sku": "SEN-HD660S2", "product_name": "Sennheiser HD 660S2",
                "channel_id": "AUDIO_PREMIUM", "wholesale_price": 285.0,
                "retail_price_de": 399.0, "margin_pct": 0.285,
                "vortex_resonance": 0.7, "vortex_pass": True, "stock_qty": 12,
            },
            {
                "sku": "BEY-DT1990", "product_name": "Beyerdynamic DT 1990 Pro",
                "channel_id": "AUDIO_PREMIUM", "wholesale_price": 320.0,
                "retail_price_de": 449.0, "margin_pct": 0.29,
                "vortex_resonance": 0.75, "vortex_pass": True, "stock_qty": 8,
            },
        ],
        "scan_timestamp": "2026-04-05T00:00:00",
    }


def _make_oracle_result():
    return {
        "predictions": [
            {
                "action": "BUY", "is_singularity": True, "signal": "528Hz",
                "confidence": 0.9, "solfeggio_hz": 528,
            },
            {
                "action": "HOLD", "is_singularity": False, "signal": "432Hz",
                "confidence": 0.5, "solfeggio_hz": 432,
            },
        ],
        "summary": {"singularities": 1, "buys": 1, "holds": 1, "waits": 0},
    }


@pytest.fixture
def mock_orchestrator_deps(monkeypatch):
    """Patch all external calls in wholesale_orchestrator module."""
    import arbitrage.wholesale_orchestrator as wo_mod

    mock_init_db = MagicMock()
    mock_scout = MagicMock(return_value=_make_scout_result())
    mock_oracle = MagicMock(return_value=_make_oracle_result())
    mock_autopojeza = MagicMock(return_value={"active": True, "health": 1.0})
    mock_get_deals = MagicMock(return_value=[
        {"id": "deal-1", "sku": "SEN-HD660S2", "margin_pct": 0.285}
    ])
    mock_update = MagicMock()
    mock_record = MagicMock()

    monkeypatch.setattr(wo_mod, "init_db", mock_init_db)
    monkeypatch.setattr(wo_mod, "scout_wholesale", mock_scout)
    monkeypatch.setattr(wo_mod, "oracle_scan_products", mock_oracle)
    monkeypatch.setattr(wo_mod, "get_autopojeza_status", mock_autopojeza)
    monkeypatch.setattr(wo_mod, "get_deals", mock_get_deals)
    monkeypatch.setattr(wo_mod, "update_deal_status", mock_update)
    monkeypatch.setattr(wo_mod, "record_kpi_event", mock_record)

    return {
        "scout": mock_scout,
        "oracle": mock_oracle,
        "autopojeza": mock_autopojeza,
        "get_deals": mock_get_deals,
        "update": mock_update,
        "record": mock_record,
    }


# ---------------------------------------------------------------------------
# run_wholesale_cycle — basic flow
# ---------------------------------------------------------------------------

def test_run_wholesale_cycle_returns_dict(mock_orchestrator_deps):
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    result = run_wholesale_cycle(use_mock=True)
    assert isinstance(result, dict)
    assert "phase_1_scout" in result
    assert "phase_2_oracle" in result
    assert "phase_3_execute" in result
    assert "autopojeza" in result


def test_run_wholesale_cycle_phase1_data(mock_orchestrator_deps):
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    result = run_wholesale_cycle(use_mock=True)
    p1 = result["phase_1_scout"]
    assert p1["new_deals"] == 2
    assert p1["total_qualified"] == 2
    assert p1["mode"] == "mock"


def test_run_wholesale_cycle_phase2_data(mock_orchestrator_deps):
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    result = run_wholesale_cycle(use_mock=True)
    p2 = result["phase_2_oracle"]
    assert p2["singularities"] == 1
    assert p2["buys"] == 1
    assert p2["holds"] == 1


def test_run_wholesale_cycle_phase3_held(mock_orchestrator_deps):
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    result = run_wholesale_cycle(use_mock=True, auto_execute=False)
    p3 = result["phase_3_execute"]
    assert p3["auto_execute"] is False
    # BUY+singularity → queued (held), HOLD → held
    assert "held" in p3


def test_run_wholesale_cycle_auto_execute(mock_orchestrator_deps):
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    result = run_wholesale_cycle(use_mock=True, auto_execute=True)
    p3 = result["phase_3_execute"]
    assert p3["auto_execute"] is True
    # BUY+singularity should be executed
    assert p3["executed"] >= 1


def test_run_wholesale_cycle_auto_execute_calls_update(mock_orchestrator_deps):
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    run_wholesale_cycle(use_mock=True, auto_execute=True)
    mock_orchestrator_deps["update"].assert_called()


def test_run_wholesale_cycle_auto_execute_records_kpi(mock_orchestrator_deps):
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    run_wholesale_cycle(use_mock=True, auto_execute=True)
    mock_orchestrator_deps["record"].assert_called()


def test_run_wholesale_cycle_has_timestamps(mock_orchestrator_deps):
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    result = run_wholesale_cycle(use_mock=True)
    assert "started_at" in result
    assert "finished_at" in result


def test_run_wholesale_cycle_with_channel_filter(mock_orchestrator_deps):
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    run_wholesale_cycle(use_mock=True, channel_filter="AUDIO_PREMIUM")
    mock_orchestrator_deps["scout"].assert_called_with(
        feed_data=None,
        feed_format="json",
        channel_filter="AUDIO_PREMIUM",
        min_margin=0.15,
        use_mock=True,
    )


def test_run_wholesale_cycle_with_min_margin(mock_orchestrator_deps):
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    run_wholesale_cycle(use_mock=True, min_margin=0.3)
    call_kwargs = mock_orchestrator_deps["scout"].call_args[1]
    assert call_kwargs["min_margin"] == 0.3


def test_run_wholesale_cycle_empty_deals(mock_orchestrator_deps, monkeypatch):
    """When oracle returns more predictions than deals, loop handles gracefully."""
    import arbitrage.wholesale_orchestrator as wo_mod
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    monkeypatch.setattr(wo_mod, "scout_wholesale", MagicMock(return_value={
        "new_deals": 0, "updated_deals": 0, "total_parsed": 0, "total_qualified": 0,
        "mode": "mock", "deals": [],
    }))
    monkeypatch.setattr(wo_mod, "oracle_scan_products", MagicMock(return_value={
        "predictions": [{"action": "BUY", "is_singularity": True, "signal": "528Hz",
                          "confidence": 0.9, "solfeggio_hz": 528}],
        "summary": {"singularities": 0, "buys": 0, "holds": 0, "waits": 0},
    }))
    result = run_wholesale_cycle(use_mock=True)
    assert result["phase_3_execute"]["executed"] == 0


def test_run_wholesale_cycle_hold_action(mock_orchestrator_deps, monkeypatch):
    """HOLD action → counted as held."""
    import arbitrage.wholesale_orchestrator as wo_mod
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    monkeypatch.setattr(wo_mod, "oracle_scan_products", MagicMock(return_value={
        "predictions": [
            {"action": "HOLD", "is_singularity": False, "signal": "432Hz", "confidence": 0.5, "solfeggio_hz": 432},
        ],
        "summary": {"singularities": 0, "buys": 0, "holds": 1, "waits": 0},
    }))
    result = run_wholesale_cycle(use_mock=True, auto_execute=False)
    p3 = result["phase_3_execute"]
    assert p3["held"] >= 1


def test_run_wholesale_cycle_wait_action(mock_orchestrator_deps, monkeypatch):
    """Non-BUY/HOLD action → counted as rejected."""
    import arbitrage.wholesale_orchestrator as wo_mod
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    monkeypatch.setattr(wo_mod, "scout_wholesale", MagicMock(return_value={
        "new_deals": 0, "updated_deals": 0, "total_parsed": 1, "total_qualified": 1,
        "mode": "mock", "deals": [
            {"sku": "X-1", "product_name": "Test", "channel_id": "AUDIO_PREMIUM",
             "wholesale_price": 100, "retail_price_de": 120, "margin_pct": 0.2}
        ],
    }))
    monkeypatch.setattr(wo_mod, "oracle_scan_products", MagicMock(return_value={
        "predictions": [
            {"action": "WAIT", "is_singularity": False, "signal": "174Hz", "confidence": 0.2, "solfeggio_hz": 174},
        ],
        "summary": {"singularities": 0, "buys": 0, "holds": 0, "waits": 1},
    }))
    result = run_wholesale_cycle(use_mock=True)
    p3 = result["phase_3_execute"]
    assert p3["rejected"] == 1


def test_run_wholesale_cycle_buy_non_singularity(mock_orchestrator_deps, monkeypatch):
    """BUY but NOT singularity → held."""
    import arbitrage.wholesale_orchestrator as wo_mod
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    monkeypatch.setattr(wo_mod, "oracle_scan_products", MagicMock(return_value={
        "predictions": [
            {"action": "BUY", "is_singularity": False, "signal": "396Hz", "confidence": 0.6, "solfeggio_hz": 396},
            {"action": "HOLD", "is_singularity": False, "signal": "432Hz", "confidence": 0.5, "solfeggio_hz": 432},
        ],
        "summary": {"singularities": 0, "buys": 1, "holds": 1, "waits": 0},
    }))
    result = run_wholesale_cycle(use_mock=True, auto_execute=False)
    p3 = result["phase_3_execute"]
    # BUY non-sing → held, HOLD → held
    assert p3["held"] == 2


# ---------------------------------------------------------------------------
# run_continuous — test that it calls run_wholesale_cycle
# ---------------------------------------------------------------------------

def test_run_continuous_calls_cycle(monkeypatch):
    """run_continuous should call run_wholesale_cycle repeatedly."""
    import time as time_mod

    import arbitrage.wholesale_orchestrator as wo_mod
    from arbitrage.wholesale_orchestrator import run_continuous
    call_count = 0

    def fake_cycle(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise KeyboardInterrupt()

    monkeypatch.setattr(wo_mod, "init_db", MagicMock())
    monkeypatch.setattr(wo_mod, "run_wholesale_cycle", fake_cycle)
    monkeypatch.setattr(time_mod, "sleep", lambda s: None)

    with pytest.raises(KeyboardInterrupt):
        run_continuous(interval_seconds=1)

    assert call_count >= 2
