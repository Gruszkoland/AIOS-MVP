"""
Unit tests for arbitrage/main.py — CLI commands.
All external calls (DB, scout, analyze, bid, xrp) are mocked.
"""
import sys
from unittest.mock import patch

import pytest

# Patch targets (where the names are imported in main.py)
_BASE = "arbitrage.main"


# ---------------------------------------------------------------------------
# cmd_status
# ---------------------------------------------------------------------------

def test_cmd_status_calls_print_progress():
    with patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.print_progress") as mock_pp, \
         patch(f"{_BASE}.get_totals", return_value={"total_jobs": 0, "bids_sent": 0, "total_profit": 0}):
        from arbitrage.main import cmd_status
        cmd_status()
    mock_pp.assert_called_once()


def test_cmd_status_calls_get_totals(capsys):
    with patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.print_progress"), \
         patch(f"{_BASE}.get_totals", return_value={"total_jobs": 5, "bids_sent": 2, "total_profit": 100.0}):
        from arbitrage.main import cmd_status
        cmd_status()
    out = capsys.readouterr().out
    assert "5" in out


# ---------------------------------------------------------------------------
# cmd_scout
# ---------------------------------------------------------------------------

def test_cmd_scout_prints_new_jobs(capsys):
    mock_jobs = [{"platform": "upwork", "title": "Write blog post", "budget_min": 100, "budget_max": 200}]
    with patch(f"{_BASE}.run_scout", return_value={"new_jobs": 1, "jobs": mock_jobs, "mode": "mock"}):
        from arbitrage.main import cmd_scout
        cmd_scout()
    out = capsys.readouterr().out
    assert "1" in out or "Scout" in out


def test_cmd_scout_no_jobs(capsys):
    with patch(f"{_BASE}.run_scout", return_value={"new_jobs": 0, "jobs": [], "mode": "mock"}):
        from arbitrage.main import cmd_scout
        cmd_scout()
    out = capsys.readouterr().out
    assert "0" in out or "Scout" in out


def test_cmd_scout_shows_top_jobs(capsys):
    jobs = [
        {"platform": "upwork", "title": f"Job {i}", "budget_min": 100, "budget_max": 200}
        for i in range(6)
    ]
    with patch(f"{_BASE}.run_scout", return_value={"new_jobs": 6, "jobs": jobs, "mode": "mock"}):
        from arbitrage.main import cmd_scout
        cmd_scout()
    out = capsys.readouterr().out
    assert "upwork" in out.lower() or "Job" in out


# ---------------------------------------------------------------------------
# cmd_analyze
# ---------------------------------------------------------------------------

def test_cmd_analyze_no_jobs(capsys):
    with patch(f"{_BASE}.get_jobs", return_value=[]):
        from arbitrage.main import cmd_analyze
        cmd_analyze()
    out = capsys.readouterr().out
    assert "No new jobs" in out or "scout" in out.lower()


def test_cmd_analyze_with_worthy_job():
    jobs = [{"id": "job1", "title": "SEO article", "platform": "upwork",
             "budget_min": 100, "budget_max": 200}]
    with patch(f"{_BASE}.get_jobs", return_value=jobs), \
         patch(f"{_BASE}.analyze_job", return_value={"score": 8, "est_profit": 100}), \
         patch(f"{_BASE}.create_bid") as mock_bid, \
         patch(f"{_BASE}.MIN_ANALYZER_SCORE", 6):
        from arbitrage.main import cmd_analyze
        cmd_analyze()
    mock_bid.assert_called_once()


def test_cmd_analyze_unworthy_job_no_bid():
    jobs = [{"id": "job1", "title": "Cheap job", "platform": "fiverr",
             "budget_min": 10, "budget_max": 20}]
    with patch(f"{_BASE}.get_jobs", return_value=jobs), \
         patch(f"{_BASE}.analyze_job", return_value={"score": 3, "est_profit": 5}), \
         patch(f"{_BASE}.create_bid") as mock_bid, \
         patch(f"{_BASE}.MIN_ANALYZER_SCORE", 6):
        from arbitrage.main import cmd_analyze
        cmd_analyze()
    mock_bid.assert_not_called()


def test_cmd_analyze_daily_limit_stops_early():
    jobs = [{"id": f"job{i}", "title": f"Job {i}", "platform": "upwork",
             "budget_min": 100, "budget_max": 200} for i in range(15)]
    with patch(f"{_BASE}.get_jobs", return_value=jobs), \
         patch(f"{_BASE}.analyze_job", return_value={"score": 9, "est_profit": 150}), \
         patch(f"{_BASE}.create_bid") as mock_bid, \
         patch(f"{_BASE}.DAILY_BID_LIMIT", 3), \
         patch(f"{_BASE}.MIN_ANALYZER_SCORE", 6):
        from arbitrage.main import cmd_analyze
        cmd_analyze()
    assert mock_bid.call_count <= 3


def test_cmd_analyze_exception_handled():
    jobs = [{"id": "bad", "title": "Bad job", "platform": "upwork"}]
    with patch(f"{_BASE}.get_jobs", return_value=jobs), \
         patch(f"{_BASE}.analyze_job", side_effect=RuntimeError("LLM error")):
        from arbitrage.main import cmd_analyze
        cmd_analyze()  # should not raise


# ---------------------------------------------------------------------------
# cmd_earn
# ---------------------------------------------------------------------------

def test_cmd_earn_valid_amount():
    with patch(f"{_BASE}.record_earning") as mock_rec, \
         patch(f"{_BASE}.print_progress"):
        from arbitrage.main import cmd_earn
        cmd_earn("150.50")
    mock_rec.assert_called_once_with(150.50, source="manual")


def test_cmd_earn_zero_exits():
    with patch(f"{_BASE}.record_earning"), patch(f"{_BASE}.print_progress"):
        from arbitrage.main import cmd_earn
        with pytest.raises(SystemExit):
            cmd_earn("0")


def test_cmd_earn_negative_exits():
    with patch(f"{_BASE}.record_earning"), patch(f"{_BASE}.print_progress"):
        from arbitrage.main import cmd_earn
        with pytest.raises(SystemExit):
            cmd_earn("-5")


def test_cmd_earn_non_numeric_exits():
    with patch(f"{_BASE}.record_earning"), patch(f"{_BASE}.print_progress"):
        from arbitrage.main import cmd_earn
        with pytest.raises(SystemExit):
            cmd_earn("abc")


# ---------------------------------------------------------------------------
# cmd_run
# ---------------------------------------------------------------------------

def test_cmd_run_calls_scout_analyze_status():
    with patch(f"{_BASE}.cmd_scout") as mock_scout, \
         patch(f"{_BASE}.cmd_analyze") as mock_analyze, \
         patch(f"{_BASE}.cmd_status") as mock_status:
        from arbitrage.main import cmd_run
        cmd_run()
    mock_scout.assert_called_once()
    mock_analyze.assert_called_once()
    mock_status.assert_called_once()


# ---------------------------------------------------------------------------
# cmd_review
# ---------------------------------------------------------------------------

def test_cmd_review_no_pending(capsys):
    with patch(f"{_BASE}.get_pending_bids", return_value=[]):
        from arbitrage.main import cmd_review
        cmd_review()
    out = capsys.readouterr().out
    assert "No pending" in out


def test_cmd_review_with_pending_approve(capsys):
    bid = {"id": "b1", "title": "Test", "platform": "upwork", "url": "http://x",
            "analyzer_score": 8, "our_price": 100, "est_profit_usd": 40,
            "cover_letter": "Dear client..."}
    with patch(f"{_BASE}.get_pending_bids", return_value=[bid]), \
         patch(f"{_BASE}.approve_bid") as mock_approve, \
         patch("builtins.input", return_value="y"):
        from arbitrage.main import cmd_review
        cmd_review()
    mock_approve.assert_called_once_with("b1", approved=True)


def test_cmd_review_with_pending_deny(capsys):
    bid = {"id": "b2", "title": "Skip", "platform": "fiverr", "url": "http://y",
            "analyzer_score": 5, "our_price": 50, "est_profit_usd": 10,
            "cover_letter": "Hi..."}
    with patch(f"{_BASE}.get_pending_bids", return_value=[bid]), \
         patch(f"{_BASE}.approve_bid") as mock_approve, \
         patch("builtins.input", return_value="n"):
        from arbitrage.main import cmd_review
        cmd_review()
    mock_approve.assert_called_once_with("b2", approved=False)


def test_cmd_review_quit_stops_loop():
    bids = [
        {"id": f"b{i}", "title": f"Bid {i}", "platform": "upwork", "url": "http://z",
         "analyzer_score": 7, "our_price": 80, "est_profit_usd": 20, "cover_letter": "Hi"}
        for i in range(3)
    ]
    with patch(f"{_BASE}.get_pending_bids", return_value=bids), \
         patch(f"{_BASE}.approve_bid") as mock_approve, \
         patch("builtins.input", return_value="q"):
        from arbitrage.main import cmd_review
        cmd_review()
    mock_approve.assert_not_called()


# ---------------------------------------------------------------------------
# main() entry point
# ---------------------------------------------------------------------------

def test_main_help_prints_usage(capsys):
    import arbitrage.main as main_mod
    with patch.object(sys, "argv", ["main", "--help"]), \
         patch(f"{_BASE}.init_db"):
        main_mod.main()
    out = capsys.readouterr().out
    assert "ADRION" in out or "command" in out.lower()


def test_main_no_args_prints_help(capsys):
    import arbitrage.main as main_mod
    with patch.object(sys, "argv", ["main"]), \
         patch(f"{_BASE}.init_db"):
        main_mod.main()
    out = capsys.readouterr().out
    assert len(out) > 0


def test_main_unknown_command_exits():
    import arbitrage.main as main_mod
    with patch.object(sys, "argv", ["main", "unknown_cmd"]), \
         patch(f"{_BASE}.init_db"):
        with pytest.raises(SystemExit):
            main_mod.main()


def test_main_status_command(capsys):
    import arbitrage.main as main_mod
    with patch.object(sys, "argv", ["main", "status"]), \
         patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.print_progress"), \
         patch(f"{_BASE}.get_totals", return_value={"total_jobs": 3, "bids_sent": 1, "total_profit": 50.0}):
        main_mod.main()
    out = capsys.readouterr().out
    assert "3" in out  # total_jobs from status output


def test_main_scout_command(capsys):
    import arbitrage.main as main_mod
    with patch.object(sys, "argv", ["main", "scout"]), \
         patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.run_scout", return_value={"new_jobs": 2, "jobs": [], "mode": "mock"}):
        main_mod.main()
    out = capsys.readouterr().out
    assert "2" in out or "Scout" in out


def test_main_earn_missing_amount_exits():
    import arbitrage.main as main_mod
    with patch.object(sys, "argv", ["main", "earn"]), \
         patch(f"{_BASE}.init_db"):
        with pytest.raises(SystemExit):
            main_mod.main()


def test_main_earn_with_amount():
    import arbitrage.main as main_mod
    with patch.object(sys, "argv", ["main", "earn", "100"]), \
         patch(f"{_BASE}.init_db"), \
         patch(f"{_BASE}.record_earning") as mock_rec, \
         patch(f"{_BASE}.print_progress"):
        main_mod.main()
    mock_rec.assert_called_once_with(100.0, source="manual")
