"""
Tests for micro-saas rate_limiter.py

Covers:
  - TTLCache sliding window counter
  - check_rate() — allowed / denied
  - Tier limit enforcement (free/pro/elite)
  - Fail-open on Redis error
  - rate_limit decorator: 200 → headers, 429 → Retry-After
  - RATE_LIMIT_ENABLED=false bypass
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add micro-saas directory to path
_SAAS_DIR = Path(__file__).parent.parent / "micro-saas"
if str(_SAAS_DIR) not in sys.path:
    sys.path.insert(0, str(_SAAS_DIR))


# ── TTLCache tests ────────────────────────────────────────────────────────

class TestTTLCache:
    def test_single_increment(self):
        from rate_limiter import _TTLCache
        cache = _TTLCache()
        count, _ = cache.increment("test-key", 3600)
        assert count == 1

    def test_multiple_increments_accumulate(self):
        from rate_limiter import _TTLCache
        cache = _TTLCache()
        for _ in range(5):
            count, _ = cache.increment("multi-key", 3600)
        assert count == 5

    def test_different_keys_independent(self):
        from rate_limiter import _TTLCache
        cache = _TTLCache()
        cache.increment("key-a", 3600)
        cache.increment("key-a", 3600)
        count_b, _ = cache.increment("key-b", 3600)
        assert count_b == 1

    def test_expired_buckets_evicted(self):
        from rate_limiter import _TTLCache
        cache = _TTLCache()

        # Manually insert an old bucket
        old_ts = int(time.time()) - 7200
        cache._store["stale-key"] = {old_ts: 99}

        count, _ = cache.increment("stale-key", 3600)
        # Old bucket should be evicted; only the new increment counts
        assert count == 1

    def test_thread_safety(self):
        from rate_limiter import _TTLCache
        import threading

        cache = _TTLCache()
        results = []

        def worker():
            for _ in range(50):
                c, _ = cache.increment("concurrent", 3600)
                results.append(c)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Final count should equal total increments
        final_count, _ = cache.increment("concurrent", 3600)
        assert final_count == 201  # 4*50 + 1


# ── check_rate() — no Redis ───────────────────────────────────────────────

class TestCheckRate:
    def setup_method(self):
        # Reset TTLCache and Redis state between tests
        import rate_limiter
        rate_limiter._fallback_cache = rate_limiter._TTLCache()
        rate_limiter._redis_client = None
        rate_limiter._redis_init_attempted = False

    def test_first_request_allowed(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        from rate_limiter import check_rate
        allowed, headers = check_rate("user-1", "free")
        assert allowed is True
        assert "X-RateLimit-Limit" in headers
        assert headers["X-RateLimit-Limit"] == "100"

    def test_remaining_decrements(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        from rate_limiter import check_rate
        for _ in range(3):
            check_rate("user-decr", "free")
        _, headers = check_rate("user-decr", "free")
        assert int(headers["X-RateLimit-Remaining"]) == 96  # 100 - 4

    def test_free_limit_enforced(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        from rate_limiter import check_rate, _TTLCache, _TIER_LIMITS
        import rate_limiter

        # Pre-seed cache to simulate limit reached
        key = "rl:free:user-over"
        now_ts = int(time.time())
        rate_limiter._fallback_cache._store[key] = {now_ts: 100}

        allowed, headers = check_rate("user-over", "free")
        assert allowed is False
        assert headers["X-RateLimit-Remaining"] == "0"

    def test_pro_limit_higher_than_free(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        from rate_limiter import check_rate
        _, headers_free = check_rate("u1", "free")
        import rate_limiter
        rate_limiter._fallback_cache = rate_limiter._TTLCache()
        _, headers_pro = check_rate("u1", "pro")
        assert int(headers_pro["X-RateLimit-Limit"]) > int(headers_free["X-RateLimit-Limit"])

    def test_elite_is_unlimited_effectively(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        from rate_limiter import check_rate, _TTLCache
        import rate_limiter

        key = "rl:elite:power-user"
        now_ts = int(time.time())
        rate_limiter._fallback_cache._store[key] = {now_ts: 9_998}

        allowed, headers = check_rate("power-user", "elite")
        assert allowed is True
        assert int(headers["X-RateLimit-Remaining"]) == 1

    def test_fail_open_on_redis_error(self, monkeypatch):
        monkeypatch.setenv("REDIS_URL", "redis://bad-host:6379/0")
        import rate_limiter
        rate_limiter._redis_init_attempted = False
        rate_limiter._redis_client = None

        from rate_limiter import check_rate

        # Patch _get_redis to raise after init
        with patch("rate_limiter._get_redis", side_effect=RuntimeError("network error")):
            allowed, headers = check_rate("user-x", "free")
        assert allowed is True  # fail open


# ── Flask decorator integration ───────────────────────────────────────────

class TestRateLimitDecorator:
    def setup_method(self):
        import rate_limiter
        rate_limiter._fallback_cache = rate_limiter._TTLCache()
        rate_limiter._redis_client = None
        rate_limiter._redis_init_attempted = False

    def _make_app(self):
        from flask import Flask, jsonify
        from rate_limiter import rate_limit

        app = Flask(__name__)

        @app.route("/test")
        @rate_limit
        def test_view():
            return jsonify({"ok": True})

        return app

    def test_successful_request_has_ratelimit_headers(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        app = self._make_app()
        with app.test_client() as client:
            resp = client.get("/test")
        assert resp.status_code == 200
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers
        assert "X-RateLimit-Reset" in resp.headers

    def test_rate_limit_exceeded_returns_429(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        app = self._make_app()
        import rate_limiter

        # Pre-fill cache to force limit
        with app.test_request_context("/test"):
            from flask import request as r
            ip = "127.0.0.1"

        key = f"rl:free:{ip}"
        now_ts = int(time.time())
        rate_limiter._fallback_cache._store[key] = {now_ts: 100}

        with app.test_client() as client:
            resp = client.get("/test")
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers
        assert resp.headers["Retry-After"] == "3600"

    def test_rate_limit_disabled_bypasses_check(self, monkeypatch):
        monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
        monkeypatch.delenv("REDIS_URL", raising=False)
        app = self._make_app()
        import rate_limiter

        # Pre-fill cache way over limit
        key = "rl:free:127.0.0.1"
        now_ts = int(time.time())
        rate_limiter._fallback_cache._store[key] = {now_ts: 99_999}

        with app.test_client() as client:
            resp = client.get("/test")
        assert resp.status_code == 200  # bypass
