"""
Unit tests for arbitrage/orchestrator.py — SAP Orchestrator (run_cycle, run_continuous).
All external calls (DB, scout, analyze, bid, xrp) are mocked.
"""
from unittest.mock import MagicMock, patch

from arbitrage.trinity import TrinityScore

_BASE = "arbitrage.orchestrator"

# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

_MOCK_JOB = {
    "id": "abc123",
    "title": "Write 5 SEO articles",
    "platform": "upwork",
    "client": "TestClient",
    "budget_min": 150,
    "budget_max": 300,
    "description": "SEO content writing",
    "status": "new",
    "scouted_at": "2026-04-05T10:00:00",
}

_ANALYSIS_HIT = {
    "score": 8,
    "worthy": True,
    "fit": "Excellent match for our content writing portfolio",
    "risks": "Client is new, no reviews yet",
    "our_price": 200.0,
    "est_profit": 120.0,
    "est_cost": 1.0,   # kept below MAX_EST_COST_PER_BID_USD default (2.5)
    "est_cost_usd": 1.0,
    "channel": "CONTENT",
    "client_name": "TestClient",
    "cover_letter": "Hello...",
    "llm_backend": "mock",
}

_ANALYSIS_MISS = {
    "score": 2,
    "worthy": False,
    "our_price": 0,
    "est_profit": 0,
    "est_cost": 0,
    "est_cost_usd": 0,
    "channel": "CONTENT",
    "client_name": "TestClient",
    "cover_letter": "",
}

# Pre-built TrinityScore stubs — avoids psutil dependency in orchestrator tests
_TRINITY_PASS = TrinityScore(
    material=0.75, intellectual=0.80, essential=0.90,
    combined=0.82, approved=True,
)
_TRINITY_DENY = TrinityScore(
    material=0.10, intellectual=0.20, essential=0.00,
    combined=0.10, approved=False,
)


def _make_conn_cm(fetchall=None, fetchone=None):
    """Build a MagicMock context manager wrapping a DB connection mock."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = fetchall if fetchall is not None else []
    mock_conn.execute.return_value.fetchone.return_value = fetchone if fetchone is not None else {"c": 0}
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_conn)
    cm.__exit__ = MagicMock(return_value=False)
    return cm, mock_conn


# ---------------------------------------------------------------------------
# _count_bids_today
# ---------------------------------------------------------------------------

def test_count_bids_today_returns_int():
    cm, _ = _make_conn_cm(fetchone={"c": 3})
    with patch(f"{_BASE}.get_conn", return_value=cm):
        from arbitrage.orchestrator import _count_bids_today
        result = _count_bids_today()
    assert result == 3


def test_count_bids_today_none_row_returns_zero():
    cm, mock_conn = _make_conn_cm()
    mock_conn.execute.return_value.fetchone.return_value = None
    with patch(f"{_BASE}.get_conn", return_value=cm):
        from arbitrage.orchestrator import _count_bids_today
        result = _count_bids_today()
    assert result == 0


# ---------------------------------------------------------------------------
# run_cycle — basic paths
# ---------------------------------------------------------------------------

def test_run_cycle_returns_summary_dict():
    cm, _ = _make_conn_cm()
    with patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.run_scout", return_value={"jobs": [], "new_jobs": 0, "mode": "mock"}), \
         patch(f"{_BASE}.get_stream_kpis", return_value={"daily_est_cost_usd": 0}), \
         patch(f"{_BASE}.get_conn", return_value=cm), \
         patch(f"{_BASE}.analyze_job", return_value=_ANALYSIS_HIT), \
         patch(f"{_BASE}.evaluate_trinity", return_value=_TRINITY_PASS), \
         patch(f"{_BASE}.create_bid", return_value={"id": "bid-1", "our_price": 200.0}), \
         patch(f"{_BASE}.set_job_status"), \
         patch(f"{_BASE}.record_kpi_event"), \
         patch(f"{_BASE}.get_client_bid_count_today", return_value=0), \
         patch(f"{_BASE}.update_xrp_snapshot", return_value={"xrp_price_usd": 2.0}), \
         patch(f"{_BASE}.get_progress", return_value={"xrp_price_usd": 2.0, "xrp_earned": 10.0,
                                                       "xrp_target": 1000, "pct_complete": 1.0,
                                                       "total_earned_usd": 20.0}):
        from arbitrage.orchestrator import run_cycle
        result = run_cycle()

    assert isinstance(result, dict)
    assert "jobs_scouted"     in result
    assert "bids_created"     in result
    assert "xrp_earned"       in result
    assert "trinity_denied"   in result
    assert "guardian_denied"  in result


def test_run_cycle_dry_run_no_bids_created():
    cm, _ = _make_conn_cm(fetchall=[dict(_MOCK_JOB)])
    with patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.run_scout", return_value={"jobs": [_MOCK_JOB], "new_jobs": 1, "mode": "mock"}), \
         patch(f"{_BASE}.get_stream_kpis", return_value={"daily_est_cost_usd": 0}), \
         patch(f"{_BASE}.get_conn", return_value=cm), \
         patch(f"{_BASE}.analyze_job", return_value=_ANALYSIS_HIT), \
         patch(f"{_BASE}.evaluate_trinity", return_value=_TRINITY_PASS), \
         patch(f"{_BASE}.create_bid") as mock_bid, \
         patch(f"{_BASE}.set_job_status"), \
         patch(f"{_BASE}.record_kpi_event"), \
         patch(f"{_BASE}.get_client_bid_count_today", return_value=0), \
         patch(f"{_BASE}.update_xrp_snapshot", return_value={"xrp_price_usd": 2.0}), \
         patch(f"{_BASE}.get_progress", return_value={"xrp_price_usd": 2.0, "xrp_earned": 10.0,
                                                       "xrp_target": 1000, "pct_complete": 1.0,
                                                       "total_earned_usd": 20.0}):
        from arbitrage.orchestrator import run_cycle
        result = run_cycle(dry_run=True)

    mock_bid.assert_not_called()
    assert result["bids_created"] == 0


def test_run_cycle_calls_init_db():
    cm, _ = _make_conn_cm()
    with patch(f"{_BASE}.init_db") as mock_init, \
         patch(f"{_BASE}.run_scout", return_value={"jobs": [], "new_jobs": 0, "mode": "mock"}), \
         patch(f"{_BASE}.get_stream_kpis", return_value={"daily_est_cost_usd": 0}), \
         patch(f"{_BASE}.get_conn", return_value=cm), \
         patch(f"{_BASE}.set_job_status"), \
         patch(f"{_BASE}.record_kpi_event"), \
         patch(f"{_BASE}.get_client_bid_count_today", return_value=0), \
         patch(f"{_BASE}.update_xrp_snapshot", return_value={"xrp_price_usd": 2.0}), \
         patch(f"{_BASE}.get_progress", return_value={"xrp_price_usd": 2.0, "xrp_earned": 0.0,
                                                       "xrp_target": 1000, "pct_complete": 0.0,
                                                       "total_earned_usd": 0.0}):
        from arbitrage.orchestrator import run_cycle
        run_cycle()

    mock_init.assert_called_once()


def test_run_cycle_with_high_score_job_creates_bid():
    cm, _ = _make_conn_cm(fetchall=[dict(_MOCK_JOB)])
    with patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.run_scout", return_value={"jobs": [_MOCK_JOB], "new_jobs": 1, "mode": "mock"}), \
         patch(f"{_BASE}.get_stream_kpis", return_value={"daily_est_cost_usd": 0}), \
         patch(f"{_BASE}.get_conn", return_value=cm), \
         patch(f"{_BASE}.analyze_job", return_value=_ANALYSIS_HIT), \
         patch(f"{_BASE}.evaluate_trinity", return_value=_TRINITY_PASS), \
         patch(f"{_BASE}.create_bid", return_value={"id": "bid-1", "our_price": 200.0}) as mock_bid, \
         patch(f"{_BASE}.set_job_status"), \
         patch(f"{_BASE}.record_kpi_event"), \
         patch(f"{_BASE}.get_client_bid_count_today", return_value=0), \
         patch(f"{_BASE}.update_xrp_snapshot", return_value={"xrp_price_usd": 2.0}), \
         patch(f"{_BASE}.get_progress", return_value={"xrp_price_usd": 2.0, "xrp_earned": 10.0,
                                                       "xrp_target": 1000, "pct_complete": 1.0,
                                                       "total_earned_usd": 20.0}), \
         patch(f"{_BASE}.MIN_ANALYZER_SCORE", 6), \
         patch(f"{_BASE}.MAX_EST_COST_PER_BID_USD", 100.0), \
         patch(f"{_BASE}.MAX_DAILY_EST_COST_USD", 500.0), \
         patch(f"{_BASE}.MAX_BIDS_PER_CLIENT_PER_DAY", 5):
        from arbitrage.orchestrator import run_cycle
        run_cycle(dry_run=False)

    mock_bid.assert_called_once()


def test_run_cycle_with_low_score_job_no_bid():
    cm, _ = _make_conn_cm(fetchall=[dict(_MOCK_JOB)])
    with patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.run_scout", return_value={"jobs": [], "new_jobs": 0, "mode": "mock"}), \
         patch(f"{_BASE}.get_stream_kpis", return_value={"daily_est_cost_usd": 0}), \
         patch(f"{_BASE}.get_conn", return_value=cm), \
         patch(f"{_BASE}.analyze_job", return_value=_ANALYSIS_MISS), \
         patch(f"{_BASE}.create_bid") as mock_bid, \
         patch(f"{_BASE}.set_job_status"), \
         patch(f"{_BASE}.record_kpi_event"), \
         patch(f"{_BASE}.get_client_bid_count_today", return_value=0), \
         patch(f"{_BASE}.update_xrp_snapshot", return_value={"xrp_price_usd": 2.0}), \
         patch(f"{_BASE}.get_progress", return_value={"xrp_price_usd": 2.0, "xrp_earned": 0.0,
                                                       "xrp_target": 1000, "pct_complete": 0.0,
                                                       "total_earned_usd": 0.0}), \
         patch(f"{_BASE}.MIN_ANALYZER_SCORE", 6):
        from arbitrage.orchestrator import run_cycle
        run_cycle(dry_run=False)

    mock_bid.assert_not_called()


def test_run_cycle_daily_limit_stops_bidding():
    """When _count_bids_today already returns >= DAILY_BID_LIMIT, no new bids."""
    cm, _ = _make_conn_cm(fetchall=[dict(_MOCK_JOB)], fetchone={"c": 10})
    with patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.run_scout", return_value={"jobs": [], "new_jobs": 0, "mode": "mock"}), \
         patch(f"{_BASE}.get_stream_kpis", return_value={"daily_est_cost_usd": 0}), \
         patch(f"{_BASE}.get_conn", return_value=cm), \
         patch(f"{_BASE}.analyze_job", return_value=_ANALYSIS_HIT), \
         patch(f"{_BASE}.create_bid") as mock_bid, \
         patch(f"{_BASE}.set_job_status"), \
         patch(f"{_BASE}.record_kpi_event"), \
         patch(f"{_BASE}.get_client_bid_count_today", return_value=0), \
         patch(f"{_BASE}.update_xrp_snapshot", return_value={"xrp_price_usd": 2.0}), \
         patch(f"{_BASE}.get_progress", return_value={"xrp_price_usd": 2.0, "xrp_earned": 0.0,
                                                       "xrp_target": 1000, "pct_complete": 0.0,
                                                       "total_earned_usd": 0.0}), \
         patch(f"{_BASE}.DAILY_BID_LIMIT", 10):
        from arbitrage.orchestrator import run_cycle
        run_cycle()

    mock_bid.assert_not_called()


def test_run_cycle_multiple_jobs_processed():
    """run_cycle processes all pending jobs and creates bids for high scorers."""
    job2 = {**_MOCK_JOB, "id": "job2", "title": "Job 2", "client": "OtherClient"}
    cm, _ = _make_conn_cm(fetchall=[dict(_MOCK_JOB), dict(job2)])

    with patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.run_scout", return_value={"jobs": [], "new_jobs": 0, "mode": "mock"}), \
         patch(f"{_BASE}.get_stream_kpis", return_value={"daily_est_cost_usd": 0}), \
         patch(f"{_BASE}.get_conn", return_value=cm), \
         patch(f"{_BASE}.analyze_job", return_value=_ANALYSIS_HIT), \
         patch(f"{_BASE}.evaluate_trinity", return_value=_TRINITY_PASS), \
         patch(f"{_BASE}.create_bid", return_value={"id": "bid-x", "our_price": 200.0}) as mock_bid, \
         patch(f"{_BASE}.set_job_status"), \
         patch(f"{_BASE}.record_kpi_event"), \
         patch(f"{_BASE}.get_client_bid_count_today", return_value=0), \
         patch(f"{_BASE}.update_xrp_snapshot", return_value={"xrp_price_usd": 2.0}), \
         patch(f"{_BASE}.get_progress", return_value={"xrp_price_usd": 2.0, "xrp_earned": 0.0,
                                                       "xrp_target": 1000, "pct_complete": 0.0,
                                                       "total_earned_usd": 0.0}), \
         patch(f"{_BASE}.MIN_ANALYZER_SCORE", 6), \
         patch(f"{_BASE}.MAX_EST_COST_PER_BID_USD", 100.0), \
         patch(f"{_BASE}.MAX_DAILY_EST_COST_USD", 500.0), \
         patch(f"{_BASE}.MAX_BIDS_PER_CLIENT_PER_DAY", 5):
        from arbitrage.orchestrator import run_cycle
        result = run_cycle()

    assert isinstance(result, dict)
    assert mock_bid.call_count == 2  # both jobs scored high


def test_run_cycle_summary_numeric_fields():
    cm, _ = _make_conn_cm()
    with patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.run_scout", return_value={"jobs": [], "new_jobs": 0, "mode": "mock"}), \
         patch(f"{_BASE}.get_stream_kpis", return_value={"daily_est_cost_usd": 0}), \
         patch(f"{_BASE}.get_conn", return_value=cm), \
         patch(f"{_BASE}.set_job_status"), \
         patch(f"{_BASE}.record_kpi_event"), \
         patch(f"{_BASE}.get_client_bid_count_today", return_value=0), \
         patch(f"{_BASE}.update_xrp_snapshot", return_value={"xrp_price_usd": 2.0}), \
         patch(f"{_BASE}.get_progress", return_value={"xrp_price_usd": 2.0, "xrp_earned": 5.0,
                                                       "xrp_target": 1000, "pct_complete": 0.5,
                                                       "total_earned_usd": 10.0}):
        from arbitrage.orchestrator import run_cycle
        result = run_cycle()

    assert isinstance(result["jobs_scouted"], int)
    assert isinstance(result["bids_created"], int)
    assert isinstance(result["pct_complete"], float)


# ---------------------------------------------------------------------------
# Trinity integration paths
# ---------------------------------------------------------------------------

def test_run_cycle_trinity_denied_no_bid():
    """When Trinity denies — bid not created, status set to trinity_denied."""
    cm, _ = _make_conn_cm(fetchall=[dict(_MOCK_JOB)])
    with patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.run_scout", return_value={"jobs": [_MOCK_JOB], "new_jobs": 1, "mode": "mock"}), \
         patch(f"{_BASE}.get_stream_kpis", return_value={"daily_est_cost_usd": 0}), \
         patch(f"{_BASE}.get_conn", return_value=cm), \
         patch(f"{_BASE}.analyze_job", return_value=_ANALYSIS_HIT), \
         patch(f"{_BASE}.evaluate_trinity", return_value=_TRINITY_DENY) as mock_trinity, \
         patch(f"{_BASE}.create_bid") as mock_bid, \
         patch(f"{_BASE}.set_job_status") as mock_status, \
         patch(f"{_BASE}.record_kpi_event"), \
         patch(f"{_BASE}.get_client_bid_count_today", return_value=0), \
         patch(f"{_BASE}.update_xrp_snapshot", return_value={"xrp_price_usd": 2.0}), \
         patch(f"{_BASE}.get_progress", return_value={"xrp_price_usd": 2.0, "xrp_earned": 0.0,
                                                       "xrp_target": 1000, "pct_complete": 0.0,
                                                       "total_earned_usd": 0.0}), \
         patch(f"{_BASE}.MIN_ANALYZER_SCORE", 6), \
         patch(f"{_BASE}.MAX_EST_COST_PER_BID_USD", 100.0), \
         patch(f"{_BASE}.MAX_DAILY_EST_COST_USD", 500.0):
        from arbitrage.orchestrator import run_cycle
        result = run_cycle()

    mock_bid.assert_not_called()
    mock_trinity.assert_called_once()
    assert result["trinity_denied"] == 1
    # Status must be set to "trinity_denied"
    status_calls = [c.args[1] for c in mock_status.call_args_list]
    assert "trinity_denied" in status_calls


def test_run_cycle_trinity_denied_records_kpi_event():
    """Trinity denial must emit a 'trinity_denied' KPI event."""
    cm, _ = _make_conn_cm(fetchall=[dict(_MOCK_JOB)])
    with patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.run_scout", return_value={"jobs": [_MOCK_JOB], "new_jobs": 1, "mode": "mock"}), \
         patch(f"{_BASE}.get_stream_kpis", return_value={"daily_est_cost_usd": 0}), \
         patch(f"{_BASE}.get_conn", return_value=cm), \
         patch(f"{_BASE}.analyze_job", return_value=_ANALYSIS_HIT), \
         patch(f"{_BASE}.evaluate_trinity", return_value=_TRINITY_DENY), \
         patch(f"{_BASE}.create_bid"), \
         patch(f"{_BASE}.set_job_status"), \
         patch(f"{_BASE}.record_kpi_event") as mock_kpi, \
         patch(f"{_BASE}.get_client_bid_count_today", return_value=0), \
         patch(f"{_BASE}.update_xrp_snapshot", return_value={"xrp_price_usd": 2.0}), \
         patch(f"{_BASE}.get_progress", return_value={"xrp_price_usd": 2.0, "xrp_earned": 0.0,
                                                       "xrp_target": 1000, "pct_complete": 0.0,
                                                       "total_earned_usd": 0.0}), \
         patch(f"{_BASE}.MIN_ANALYZER_SCORE", 6), \
         patch(f"{_BASE}.MAX_EST_COST_PER_BID_USD", 100.0), \
         patch(f"{_BASE}.MAX_DAILY_EST_COST_USD", 500.0):
        from arbitrage.orchestrator import run_cycle
        run_cycle()

    event_types = [c.kwargs.get("event_type") for c in mock_kpi.call_args_list]
    assert "trinity_denied" in event_types


def test_run_cycle_summary_contains_trinity_guardian_counts():
    """Summary dict must contain trinity_denied and guardian_denied counters."""
    cm, _ = _make_conn_cm(fetchall=[dict(_MOCK_JOB)])
    with patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.run_scout", return_value={"jobs": [_MOCK_JOB], "new_jobs": 1, "mode": "mock"}), \
         patch(f"{_BASE}.get_stream_kpis", return_value={"daily_est_cost_usd": 0}), \
         patch(f"{_BASE}.get_conn", return_value=cm), \
         patch(f"{_BASE}.analyze_job", return_value=_ANALYSIS_HIT), \
         patch(f"{_BASE}.evaluate_trinity", return_value=_TRINITY_PASS), \
         patch(f"{_BASE}.create_bid", return_value={"id": "b1", "our_price": 200.0}), \
         patch(f"{_BASE}.set_job_status"), \
         patch(f"{_BASE}.record_kpi_event"), \
         patch(f"{_BASE}.get_client_bid_count_today", return_value=0), \
         patch(f"{_BASE}.update_xrp_snapshot", return_value={"xrp_price_usd": 2.0}), \
         patch(f"{_BASE}.get_progress", return_value={"xrp_price_usd": 2.0, "xrp_earned": 0.0,
                                                       "xrp_target": 1000, "pct_complete": 0.0,
                                                       "total_earned_usd": 0.0}), \
         patch(f"{_BASE}.MIN_ANALYZER_SCORE", 6), \
         patch(f"{_BASE}.MAX_EST_COST_PER_BID_USD", 100.0), \
         patch(f"{_BASE}.MAX_DAILY_EST_COST_USD", 500.0), \
         patch(f"{_BASE}.MAX_BIDS_PER_CLIENT_PER_DAY", 5):
        from arbitrage.orchestrator import run_cycle
        result = run_cycle()

    assert result["trinity_denied"]  == 0
    assert result["guardian_denied"] == 0
    assert result["bids_created"]    == 1
