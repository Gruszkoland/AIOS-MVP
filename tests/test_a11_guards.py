"""Regression tests for A-11 hardening guards.

These tests validate core protections without requiring live HTTP services.
"""



def test_sliding_window_rate_limiter_blocks_after_limit(monkeypatch):
    """Limiter allows max requests in window, then blocks, then recovers."""
    from arbitrage.rate_limiter import SlidingWindowRateLimiter
    import arbitrage.rate_limiter as rate_limiter_module

    now = {"t": 1000.0}

    def _fake_monotonic():
        return now["t"]

    monkeypatch.setattr(rate_limiter_module.time, "monotonic", _fake_monotonic)

    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=10.0)

    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is False

    # Move outside the window, capacity should be restored.
    now["t"] += 10.1
    assert limiter.is_allowed("127.0.0.1") is True


def test_circuit_breaker_opens_after_threshold_and_recovers(monkeypatch):
    """Breaker opens after N failures and closes after recovery + success."""
    from arbitrage.circuit_breaker import CircuitBreaker, CircuitBreakerOpen
    import arbitrage.circuit_breaker as cb_module

    now = {"t": 2000.0}

    def _fake_monotonic():
        return now["t"]

    monkeypatch.setattr(cb_module.time, "monotonic", _fake_monotonic)

    breaker = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=5.0,
                             success_threshold=1)

    def _fail():
        raise RuntimeError("downstream error")

    def _ok():
        return "ok"

    assert breaker.state == "CLOSED"
    try: breaker.call(_fail)
    except RuntimeError: pass
    try: breaker.call(_fail)
    except RuntimeError: pass
    assert breaker.state == "CLOSED"

    try: breaker.call(_fail)
    except RuntimeError: pass
    assert breaker.state == "OPEN"

    now["t"] += 10.1  # backoff doubles on OPEN transition: 5.0 -> 10.0
    # After recovery timeout, breaker enters HALF_OPEN — allows one probe.
    assert breaker.state == "HALF_OPEN"

    breaker.call(_ok)
    assert breaker.state == "CLOSED"


def test_circuit_breaker_stays_open_within_recovery_window(monkeypatch):
    """Breaker remains open until configured recovery timeout elapses."""
    from arbitrage.circuit_breaker import CircuitBreaker, CircuitBreakerOpen
    import arbitrage.circuit_breaker as cb_module

    now = {"t": 3000.0}

    def _fake_monotonic():
        return now["t"]

    monkeypatch.setattr(cb_module.time, "monotonic", _fake_monotonic)

    breaker = CircuitBreaker(name="test2", failure_threshold=2, recovery_timeout=8.0)

    def _fail():
        raise RuntimeError("err")

    try: breaker.call(_fail)
    except RuntimeError: pass
    try: breaker.call(_fail)
    except RuntimeError: pass

    assert breaker.state == "OPEN"
    now["t"] += 7.9
    assert breaker.state == "OPEN"
