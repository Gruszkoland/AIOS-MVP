"""
Unit tests for arbitrage/autopilot.py — AutopilotService.
Thread-based scheduler; stop_event and run_cycle are mocked.
"""
import time
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service():
    """Import and return a fresh AutopilotService instance for each test."""
    from arbitrage.autopilot import AutopilotService
    return AutopilotService()


# ---------------------------------------------------------------------------
# get_status — initial state
# ---------------------------------------------------------------------------

def test_initial_status_not_running():
    with patch("arbitrage.autopilot.get_last_autopilot_run", return_value=None):
        svc = _make_service()
        status = svc.get_status()
    assert status["running"] is False
    assert status["interval_minutes"] == 30
    assert status["dry_run"] is False
    assert status["last_error"] is None


def test_is_running_false_when_not_started():
    svc = _make_service()
    assert svc.is_running() is False


# ---------------------------------------------------------------------------
# start / stop
# ---------------------------------------------------------------------------

def test_start_returns_status_dict():
    with patch("arbitrage.autopilot.run_cycle", return_value={}), \
         patch("arbitrage.autopilot.run_aux_streams", return_value={}), \
         patch("arbitrage.autopilot.init_db"), \
         patch("arbitrage.autopilot.record_autopilot_run"), \
         patch("arbitrage.autopilot.get_last_autopilot_run", return_value=None):
        svc = _make_service()
        status = svc.start(interval_minutes=60, dry_run=False)

    assert isinstance(status, dict)
    svc.stop()  # cleanup


def test_start_sets_interval_minutes():
    with patch("arbitrage.autopilot.run_cycle", return_value={}), \
         patch("arbitrage.autopilot.run_aux_streams", return_value={}), \
         patch("arbitrage.autopilot.init_db"), \
         patch("arbitrage.autopilot.record_autopilot_run"), \
         patch("arbitrage.autopilot.get_last_autopilot_run", return_value=None):
        svc = _make_service()
        svc.start(interval_minutes=45)
        assert svc._interval_minutes == 45
        svc.stop()


def test_start_sets_dry_run_flag():
    with patch("arbitrage.autopilot.run_cycle", return_value={}), \
         patch("arbitrage.autopilot.run_aux_streams", return_value={}), \
         patch("arbitrage.autopilot.init_db"), \
         patch("arbitrage.autopilot.record_autopilot_run"), \
         patch("arbitrage.autopilot.get_last_autopilot_run", return_value=None):
        svc = _make_service()
        svc.start(dry_run=True)
        assert svc._dry_run is True
        svc.stop()


def test_start_twice_returns_existing_status():
    """Calling start while already running returns current status without restart."""
    with patch("arbitrage.autopilot.run_cycle", return_value={}), \
         patch("arbitrage.autopilot.run_aux_streams", return_value={}), \
         patch("arbitrage.autopilot.init_db"), \
         patch("arbitrage.autopilot.record_autopilot_run"), \
         patch("arbitrage.autopilot.get_last_autopilot_run", return_value=None):
        svc = _make_service()
        svc.start(interval_minutes=30)
        svc.start(interval_minutes=99)  # should be ignored
        assert svc._interval_minutes == 30  # unchanged
        svc.stop()


def test_stop_when_not_running():
    with patch("arbitrage.autopilot.get_last_autopilot_run", return_value=None):
        svc = _make_service()
        status = svc.stop()
    assert status["running"] is False


def test_stop_after_start_sets_running_false():
    with patch("arbitrage.autopilot.run_cycle", return_value={}), \
         patch("arbitrage.autopilot.run_aux_streams", return_value={}), \
         patch("arbitrage.autopilot.init_db"), \
         patch("arbitrage.autopilot.record_autopilot_run"), \
         patch("arbitrage.autopilot.get_last_autopilot_run", return_value=None):
        svc = _make_service()
        svc.start(interval_minutes=60)
        status = svc.stop()
    assert status["running"] is False


# ---------------------------------------------------------------------------
# interval_minutes clamp
# ---------------------------------------------------------------------------

def test_start_interval_minimum_is_1():
    with patch("arbitrage.autopilot.run_cycle", return_value={}), \
         patch("arbitrage.autopilot.run_aux_streams", return_value={}), \
         patch("arbitrage.autopilot.init_db"), \
         patch("arbitrage.autopilot.record_autopilot_run"), \
         patch("arbitrage.autopilot.get_last_autopilot_run", return_value=None):
        svc = _make_service()
        svc.start(interval_minutes=0)  # should be clamped to 1
        assert svc._interval_minutes >= 1
        svc.stop()


# ---------------------------------------------------------------------------
# Error handling in _loop
# ---------------------------------------------------------------------------

def test_loop_records_error_on_exception():
    """If run_cycle raises, last_error is set and record_autopilot_run is called."""
    mock_record = MagicMock()

    with patch("arbitrage.autopilot.run_cycle", side_effect=RuntimeError("DB gone")), \
         patch("arbitrage.autopilot.run_aux_streams", return_value={}), \
         patch("arbitrage.autopilot.init_db"), \
         patch("arbitrage.autopilot.record_autopilot_run", mock_record), \
         patch("arbitrage.autopilot.get_last_autopilot_run", return_value=None):

        svc = _make_service()
        # Use a tiny interval so the loop runs once quickly
        svc.start(interval_minutes=1)
        time.sleep(0.3)  # let the thread execute at least one cycle
        svc.stop()

    # record_autopilot_run should have been called (even on failure)
    assert mock_record.call_count >= 1


# ---------------------------------------------------------------------------
# module-level singleton
# ---------------------------------------------------------------------------

def test_module_has_singleton():
    from arbitrage.autopilot import AutopilotService, autopilot_service
    assert isinstance(autopilot_service, AutopilotService)
