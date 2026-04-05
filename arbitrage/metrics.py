"""
ADRION 369 — Database Pool Metrics
Tracks pool size, checked-out connections, and query latency.
Optionally exposes prometheus_client gauges/histograms if the
library is installed; otherwise falls back to plain in-process counters.
"""
import logging
import threading
import time

logger = logging.getLogger("adrion.metrics")

# ── Optional Prometheus integration ──────────────────────────────────────────
try:
    import prometheus_client as prom

    _pool_size_gauge = prom.Gauge("adrion_db_pool_size", "Total connections in pool")
    _pool_checked_out_gauge = prom.Gauge(
        "adrion_db_pool_checked_out", "Connections currently in use"
    )
    _query_latency_hist = prom.Histogram(
        "adrion_db_query_latency_seconds",
        "Database query latency in seconds",
        buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
    )
    _PROMETHEUS = True
except ImportError:  # pragma: no cover
    _PROMETHEUS = False


# ── In-process fallback counters ─────────────────────────────────────────────
class PoolMetrics:
    """Thread-safe pool usage tracker."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.pool_size: int = 0
        self.checked_out: int = 0
        self.peak_checked_out: int = 0
        self.total_checkouts: int = 0
        self.total_timeouts: int = 0

    def record_checkout(self) -> None:
        with self._lock:
            self.checked_out += 1
            self.total_checkouts += 1
            if self.checked_out > self.peak_checked_out:
                self.peak_checked_out = self.checked_out
        if _PROMETHEUS:
            _pool_checked_out_gauge.set(self.checked_out)

    def record_return(self) -> None:
        with self._lock:
            if self.checked_out > 0:
                self.checked_out -= 1
        if _PROMETHEUS:
            _pool_checked_out_gauge.set(self.checked_out)

    def set_pool_size(self, size: int) -> None:
        with self._lock:
            self.pool_size = size
        if _PROMETHEUS:
            _pool_size_gauge.set(size)

    def record_timeout(self) -> None:
        with self._lock:
            self.total_timeouts += 1

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "pool_size": self.pool_size,
                "checked_out": self.checked_out,
                "peak_checked_out": self.peak_checked_out,
                "total_checkouts": self.total_checkouts,
                "total_timeouts": self.total_timeouts,
                "utilization_pct": round(
                    (self.checked_out / self.pool_size * 100) if self.pool_size else 0.0, 1
                ),
            }

    def log_status(self) -> None:
        snap = self.snapshot()
        logger.info(
            "Pool metrics — size=%d checked_out=%d peak=%d utilization=%.1f%%",
            snap["pool_size"],
            snap["checked_out"],
            snap["peak_checked_out"],
            snap["utilization_pct"],
        )


# Singleton shared across the process
pool_metrics = PoolMetrics()


# ── Query latency context manager ─────────────────────────────────────────────
class track_query:
    """Context manager that records query latency."""

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_):
        elapsed = time.perf_counter() - self._start
        if _PROMETHEUS:
            _query_latency_hist.observe(elapsed)
        if elapsed > 1.0:
            logger.warning("Slow query detected: %.3fs", elapsed)


# ── Periodic logging worker ───────────────────────────────────────────────────
_log_thread: threading.Thread | None = None


def start_periodic_logging(interval_seconds: int = 300) -> None:
    """Log pool metrics every `interval_seconds` (default 5 min) in a daemon thread."""
    global _log_thread

    def _worker():
        while True:
            time.sleep(interval_seconds)
            pool_metrics.log_status()

    _log_thread = threading.Thread(target=_worker, daemon=True, name="adrion-pool-metrics")
    _log_thread.start()
    logger.debug("Pool metrics logging started (interval=%ds)", interval_seconds)
