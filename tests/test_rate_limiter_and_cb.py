"""
ADRION 369 — Tests for rate_limiter and circuit_breaker modules.
"""
import time

import pytest

from arbitrage.circuit_breaker import CircuitBreaker, CircuitBreakerOpen, all_statuses
from arbitrage.rate_limiter import SlidingWindowRateLimiter

# ── SlidingWindowRateLimiter ──────────────────────────────────────────────────


class TestSlidingWindowRateLimiter:
    def test_allows_up_to_max(self):
        lim = SlidingWindowRateLimiter(max_requests=3, window_seconds=60.0)
        assert lim.is_allowed("ip1") is True
        assert lim.is_allowed("ip1") is True
        assert lim.is_allowed("ip1") is True

    def test_blocks_after_max(self):
        lim = SlidingWindowRateLimiter(max_requests=2, window_seconds=60.0)
        lim.is_allowed("ip1")
        lim.is_allowed("ip1")
        assert lim.is_allowed("ip1") is False

    def test_different_ips_independent(self):
        lim = SlidingWindowRateLimiter(max_requests=1, window_seconds=60.0)
        assert lim.is_allowed("ip1") is True
        assert lim.is_allowed("ip1") is False
        assert lim.is_allowed("ip2") is True  # different key — fresh bucket

    def test_window_expires(self):
        lim = SlidingWindowRateLimiter(max_requests=1, window_seconds=0.05)
        assert lim.is_allowed("ip1") is True
        assert lim.is_allowed("ip1") is False
        time.sleep(0.1)
        assert lim.is_allowed("ip1") is True  # window has slid past

    def test_properties(self):
        lim = SlidingWindowRateLimiter(max_requests=10, window_seconds=30.0, name="test")
        assert lim.max_requests == 10
        assert lim.window_seconds == 30.0


# ── CircuitBreaker ────────────────────────────────────────────────────────────


class TestCircuitBreakerClosed:
    def test_calls_function(self):
        cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout=30.0)
        result = cb.call(lambda: 42)
        assert result == 42

    def test_state_starts_closed(self):
        cb = CircuitBreaker("test")
        assert cb.state == "CLOSED"

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker("test", failure_threshold=3)

        def fail_then_succeed(flag):
            if flag:
                raise ValueError("fail")
            return "ok"

        try:
            cb.call(fail_then_succeed, True)
        except ValueError:
            pass
        # One failure, should still be CLOSED
        assert cb.state == "CLOSED"
        cb.call(fail_then_succeed, False)
        assert cb.status()["failure_count"] == 0


class TestCircuitBreakerOpening:
    def test_opens_after_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=60.0)
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
            except RuntimeError:
                pass
        assert cb.state == "OPEN"

    def test_raises_circuit_breaker_open_when_open(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=60.0)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        with pytest.raises(CircuitBreakerOpen) as exc_info:
            cb.call(lambda: "should not reach")
        assert exc_info.value.name == "test"
        assert exc_info.value.retry_after >= 0

    def test_open_exception_message(self):
        cb = CircuitBreaker("my_svc", failure_threshold=1, recovery_timeout=10.0)
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("x")))
        except ValueError:
            pass
        try:
            cb.call(lambda: None)
        except CircuitBreakerOpen as exc:
            assert "my_svc" in str(exc)
            assert "OPEN" in str(exc)


class TestCircuitBreakerHalfOpen:
    def test_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.05)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except RuntimeError:
            pass
        assert cb.state == "OPEN"
        time.sleep(0.25)  # wait for doubled backoff (0.05 * 2 = 0.1s) plus margin
        assert cb.state == "HALF_OPEN"

    def test_closes_after_success_in_half_open(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.05, success_threshold=1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except RuntimeError:
            pass
        time.sleep(0.25)
        assert cb.state == "HALF_OPEN"
        cb.call(lambda: "ok")
        assert cb.state == "CLOSED"

    def test_reopens_on_failure_in_half_open(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.05)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except RuntimeError:
            pass
        time.sleep(0.25)
        assert cb.state == "HALF_OPEN"
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except RuntimeError:
            pass
        assert cb.state == "OPEN"


class TestCircuitBreakerReset:
    def test_manual_reset_closes_open_circuit(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=999.0)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except RuntimeError:
            pass
        assert cb.state == "OPEN"
        cb.reset()
        assert cb.state == "CLOSED"
        assert cb.status()["failure_count"] == 0

    def test_status_snapshot(self):
        cb = CircuitBreaker("my_cb", failure_threshold=3, recovery_timeout=30.0)
        snap = cb.status()
        assert snap["name"] == "my_cb"
        assert snap["state"] == "CLOSED"
        assert snap["failure_count"] == 0
        assert snap["last_failure_at"] is None

    def test_all_statuses_returns_list(self):
        statuses = all_statuses()
        assert isinstance(statuses, list)
        assert len(statuses) >= 4
        names = [s["name"] for s in statuses]
        assert "llm" in names
        assert "stripe" in names
