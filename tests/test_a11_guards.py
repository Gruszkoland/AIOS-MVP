"""Regression tests for A-11 hardening guards.

These tests validate core protections without requiring live HTTP services.
"""

import pytest


def test_sliding_window_rate_limiter_blocks_after_limit(monkeypatch):
    """Limiter allows max requests in window, then blocks, then recovers."""
    from arbitrage.api import _SlidingWindowRateLimiter
    import arbitrage.api as api_module

    now = {"t": 1000.0}

    def _fake_monotonic():
        return now["t"]

    monkeypatch.setattr(api_module.time, "monotonic", _fake_monotonic)

    limiter = _SlidingWindowRateLimiter(max_requests=3, window_seconds=10.0)

    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is False

    # Move outside the window, capacity should be restored.
    now["t"] += 10.1
    assert limiter.is_allowed("127.0.0.1") is True


def test_circuit_breaker_opens_after_threshold_and_recovers(monkeypatch):
    """Breaker opens after N failures and closes after recovery + success."""
    from arbitrage.quantum import _CircuitBreaker
    import arbitrage.quantum as quantum_module

    now = {"t": 2000.0}

    def _fake_monotonic():
        return now["t"]

    monkeypatch.setattr(quantum_module.time, "monotonic", _fake_monotonic)

    breaker = _CircuitBreaker(failure_threshold=3, recovery_timeout=5.0)

    assert breaker.is_open() is False
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.is_open() is False

    breaker.record_failure()
    assert breaker.is_open() is True

    now["t"] += 5.1
    # After recovery timeout, breaker allows probing (half-open behavior).
    assert breaker.is_open() is False

    breaker.record_success()
    assert breaker.is_open() is False


def test_circuit_breaker_stays_open_within_recovery_window(monkeypatch):
    """Breaker remains open until configured recovery timeout elapses."""
    from arbitrage.quantum import _CircuitBreaker
    import arbitrage.quantum as quantum_module

    now = {"t": 3000.0}

    def _fake_monotonic():
        return now["t"]

    monkeypatch.setattr(quantum_module.time, "monotonic", _fake_monotonic)

    breaker = _CircuitBreaker(failure_threshold=2, recovery_timeout=8.0)
    breaker.record_failure()
    breaker.record_failure()

    assert breaker.is_open() is True
    now["t"] += 7.9
    assert breaker.is_open() is True
