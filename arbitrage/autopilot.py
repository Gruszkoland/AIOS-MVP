"""
ADRION 369 - Autopilot Service
Background scheduler for fully automated orchestrator cycles.
Includes optional Healer integration (U5) for periodic health checks.
"""
import logging
import threading
from datetime import datetime

from .config import RESALE_EVENTS_DAILY_CAP, UGC_EVENTS_DAILY_CAP
from .database import get_last_autopilot_run, init_db, record_autopilot_run
from .orchestrator import run_cycle
from .stream_emitters import run_aux_streams

log = logging.getLogger("autopilot")

# U5: Default healer interval — run every N autopilot cycles (0 = disabled)
HEALER_CYCLE_INTERVAL = 3  # every 3rd autopilot cycle (~90 min at default 30-min interval)


class AutopilotService:
    def __init__(self, healer_cycle_interval: int = HEALER_CYCLE_INTERVAL):
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._interval_minutes = 30
        self._dry_run = False
        self._last_started_at = None
        self._last_finished_at = None
        self._last_error = None
        # U5: Healer integration
        self._healer_cycle_interval = max(0, healer_cycle_interval)
        self._cycle_count = 0
        self._healer = None  # Lazy-init to avoid import at module load

    def start(self, interval_minutes: int = 30, dry_run: bool = False) -> dict:
        with self._lock:
            if self.is_running():
                return self.get_status()

            self._interval_minutes = max(1, int(interval_minutes))
            self._dry_run = bool(dry_run)
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            log.info(
                "Autopilot started (interval=%s min, dry_run=%s)",
                self._interval_minutes,
                self._dry_run,
            )
            return self.get_status()

    def stop(self) -> dict:
        with self._lock:
            if not self.is_running():
                return self.get_status()

            self._stop_event.set()
            thread = self._thread

        if thread:
            thread.join(timeout=5)

        with self._lock:
            self._thread = None
            log.info("Autopilot stopped")
            return self.get_status()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def get_status(self) -> dict:
        last_run = get_last_autopilot_run()
        return {
            "running": self.is_running(),
            "interval_minutes": self._interval_minutes,
            "dry_run": self._dry_run,
            "last_started_at": self._last_started_at,
            "last_finished_at": self._last_finished_at,
            "last_error": self._last_error,
            "last_run": last_run,
        }

    def _get_healer(self):
        """Lazy-init AdrionHealer to avoid circular imports."""
        if self._healer is None:
            try:
                from scripts.adrion_healer import AdrionHealer
                self._healer = AdrionHealer()
                log.info("Healer integration initialized")
            except ImportError:
                log.warning("AdrionHealer not available — healer integration disabled")
                self._healer_cycle_interval = 0
        return self._healer

    def _run_healer(self):
        """Run a healer cycle if interval has elapsed. Non-fatal on failure."""
        if self._healer_cycle_interval <= 0:
            return
        self._cycle_count += 1
        if self._cycle_count % self._healer_cycle_interval != 0:
            return
        healer = self._get_healer()
        if healer is None:
            return
        try:
            log.info("Running Healer cycle (every %d autopilot cycles)", self._healer_cycle_interval)
            healer.run_cycle()
            log.info("Healer cycle completed successfully")
        except Exception as exc:
            log.error("Healer cycle failed (non-fatal): %s", exc, exc_info=True)

    def _loop(self):
        init_db()
        while not self._stop_event.is_set():
            started_at = datetime.now().isoformat(timespec="seconds")
            self._last_started_at = started_at
            run_data = {
                "started_at": started_at,
                "finished_at": None,
                "success": False,
                "dry_run": self._dry_run,
                "jobs_scouted": 0,
                "new_jobs": 0,
                "analyzed": 0,
                "bids_created": 0,
                "bids_today": 0,
                "total_earned_usd": 0,
                "error_message": None,
            }
            try:
                summary = run_cycle(dry_run=self._dry_run)
                aux_summary = run_aux_streams(
                    ugc_daily_cap=UGC_EVENTS_DAILY_CAP,
                    resale_daily_cap=RESALE_EVENTS_DAILY_CAP,
                    dry_run=self._dry_run,
                )
                run_data.update(
                    {
                        "success": True,
                        "jobs_scouted": summary.get("jobs_scouted", 0),
                        "new_jobs": summary.get("new_jobs", 0),
                        "analyzed": summary.get("analyzed", 0),
                        "bids_created": summary.get("bids_created", 0),
                        "bids_today": summary.get("bids_today", 0),
                        "total_earned_usd": summary.get("total_earned_usd", 0),
                    }
                )
                log.info("Aux streams summary: %s", aux_summary)
                self._last_error = None
            except Exception as exc:
                self._last_error = str(exc)
                run_data["error_message"] = str(exc)
                log.error("Autopilot cycle failed: %s", exc, exc_info=True)
            finally:
                finished_at = datetime.now().isoformat(timespec="seconds")
                self._last_finished_at = finished_at
                run_data["finished_at"] = finished_at
                record_autopilot_run(run_data)

            # U5: Run healer after main cycle completes
            self._run_healer()

            wait_seconds = self._interval_minutes * 60
            if self._stop_event.wait(wait_seconds):
                break


autopilot_service = AutopilotService()
