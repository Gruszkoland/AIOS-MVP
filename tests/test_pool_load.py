"""
ADRION 369 — Connection Pool Load Tests

Validates that get_pooled_conn / return_conn behaves correctly under
concurrent load using the SQLite fallback path (no PostgreSQL required).
"""
import concurrent.futures
import sqlite3
import threading
import time

import pytest

import arbitrage.database as db_mod
from arbitrage.metrics import PoolMetrics, track_query


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def fresh_metrics():
    """Reset singleton metrics between tests."""
    metrics = PoolMetrics()
    return metrics


@pytest.fixture()
def sqlite_conn_factory(tmp_path):
    """Factory that returns SQLite connections to a temp DB."""
    db_path = tmp_path / "load_test.db"

    def factory():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn

    return factory


# ── Unit: PoolMetrics ─────────────────────────────────────────────────────────

class TestPoolMetrics:
    def test_initial_state(self, fresh_metrics):
        snap = fresh_metrics.snapshot()
        assert snap["pool_size"] == 0
        assert snap["checked_out"] == 0
        assert snap["total_checkouts"] == 0
        assert snap["total_timeouts"] == 0
        assert snap["utilization_pct"] == 0.0

    def test_record_checkout_increments(self, fresh_metrics):
        fresh_metrics.record_checkout()
        fresh_metrics.record_checkout()
        snap = fresh_metrics.snapshot()
        assert snap["checked_out"] == 2
        assert snap["total_checkouts"] == 2

    def test_record_return_decrements(self, fresh_metrics):
        fresh_metrics.record_checkout()
        fresh_metrics.record_checkout()
        fresh_metrics.record_return()
        snap = fresh_metrics.snapshot()
        assert snap["checked_out"] == 1

    def test_return_does_not_go_below_zero(self, fresh_metrics):
        fresh_metrics.record_return()  # called without checkout
        assert fresh_metrics.snapshot()["checked_out"] == 0

    def test_peak_tracked(self, fresh_metrics):
        for _ in range(5):
            fresh_metrics.record_checkout()
        for _ in range(3):
            fresh_metrics.record_return()
        assert fresh_metrics.snapshot()["peak_checked_out"] == 5

    def test_set_pool_size(self, fresh_metrics):
        fresh_metrics.set_pool_size(10)
        assert fresh_metrics.snapshot()["pool_size"] == 10

    def test_utilization_pct(self, fresh_metrics):
        fresh_metrics.set_pool_size(10)
        for _ in range(3):
            fresh_metrics.record_checkout()
        assert fresh_metrics.snapshot()["utilization_pct"] == 30.0

    def test_record_timeout(self, fresh_metrics):
        fresh_metrics.record_timeout()
        fresh_metrics.record_timeout()
        assert fresh_metrics.snapshot()["total_timeouts"] == 2

    def test_thread_safety(self, fresh_metrics):
        """100 concurrent checkouts should be counted exactly."""
        def do_checkout():
            fresh_metrics.record_checkout()

        threads = [threading.Thread(target=do_checkout) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert fresh_metrics.snapshot()["total_checkouts"] == 100


# ── Unit: track_query context manager ────────────────────────────────────────

class TestTrackQuery:
    def test_completes_without_error(self):
        with track_query():
            time.sleep(0.001)

    def test_exits_on_exception(self):
        try:
            with track_query():
                raise ValueError("test error")
        except ValueError:
            pass  # context manager should not swallow exceptions


# ── Integration: get_pooled_conn / return_conn (SQLite fallback) ──────────────

class TestSQLitePoolFallback:
    """Validates pool API against SQLite (no PostgreSQL needed)."""

    def test_get_pooled_conn_returns_connection(self, monkeypatch):
        assert db_mod._pool is None  # No pool in SQLite mode
        conn = db_mod.get_pooled_conn()
        assert conn is not None
        conn.close()

    def test_return_conn_noop_for_sqlite(self, monkeypatch):
        """return_conn should not raise for a SQLite connection."""
        conn = db_mod.get_pooled_conn()
        db_mod.return_conn(conn)  # should not raise
        conn.close()

    def test_graceful_drain_noop_when_no_pool(self):
        """graceful_drain should complete silently when _pool is None."""
        assert db_mod._pool is None
        db_mod.graceful_drain()  # must not raise


# ── Load test: concurrent SQLite connections ──────────────────────────────────

@pytest.mark.slow
class TestConcurrentLoad:
    """Simulate concurrent DB access using the pooled connection API."""

    def test_100_sequential_queries(self):
        """100 sequential checkout/query/return cycles must complete cleanly."""
        for _ in range(100):
            conn = db_mod.get_pooled_conn()
            conn.execute("SELECT 1")
            db_mod.return_conn(conn)
            conn.close()

    def test_50_concurrent_connections(self):
        """50 concurrent workers each performing one query must all succeed."""
        errors: list[Exception] = []
        lock = threading.Lock()

        def worker(_i: int) -> bool:
            try:
                conn = db_mod.get_pooled_conn()
                conn.execute("SELECT 1")
                time.sleep(0.005)  # simulate query time
                db_mod.return_conn(conn)
                conn.close()
                return True
            except Exception as exc:
                with lock:
                    errors.append(exc)
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as exe:
            results = list(exe.map(worker, range(100)))

        assert not errors, f"Errors during concurrent access: {errors}"
        assert all(results), "Not all workers completed successfully"

    def test_metrics_no_leaks(self, fresh_metrics):
        """After balanced checkout/return cycles, checked_out must return to 0."""
        for _ in range(20):
            fresh_metrics.record_checkout()
        for _ in range(20):
            fresh_metrics.record_return()

        assert fresh_metrics.snapshot()["checked_out"] == 0
