"""
ADRION 369 — micro-saas Rate Limiter

Sliding window rate limiter with Redis (primary) and TTLCache (fallback).
Enforces per-tier hourly request limits on billing API endpoints.

Tiers:
  free  — 100 requests/hour
  pro   — 1 000 requests/hour
  elite — 10 000 requests/hour

Configuration (env vars):
  REDIS_URL          — Redis connection URL (e.g. redis://localhost:6379/0)
  RATE_LIMIT_ENABLED — "true" / "false" (default: true)

Response headers added by the @rate_limit decorator:
  X-RateLimit-Limit     — tier limit per hour
  X-RateLimit-Remaining — requests left in current window
  X-RateLimit-Reset     — Unix timestamp when the window resets

Returns 429 Too Many Requests with Retry-After: 3600 when limit exceeded.
"""
from __future__ import annotations

import logging
import os
import time
from functools import wraps
from threading import Lock
from typing import Any, Callable, Optional

from flask import jsonify, request

logger = logging.getLogger("adrion.micro_saas.rate_limiter")

# ── Tier limits ───────────────────────────────────────────────────────────

_TIER_LIMITS: dict[str, int] = {
    "free": 100,
    "pro": 1_000,
    "elite": 10_000,
}
_WINDOW_SECONDS = 3600  # 1 hour sliding window
_DEFAULT_LIMIT = _TIER_LIMITS["free"]  # unauthenticated → free limit


# ── TTLCache fallback (in-process, no external deps) ──────────────────────

class _TTLCache:
    """
    Minimal thread-safe sliding window counter backed by an in-memory dict.
    Precision: 1-second buckets within the rolling window.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        # key → {bucket_ts: count}
        self._store: dict[str, dict[int, int]] = {}

    def increment(self, key: str, window: int) -> tuple[int, int]:
        """
        Increment counter for key; returns (current_count, window_start_ts).
        window: sliding window size in seconds.
        """
        now_ts = int(time.time())
        cutoff = now_ts - window

        with self._lock:
            if key not in self._store:
                self._store[key] = {}
            buckets = self._store[key]

            # Evict stale buckets
            stale = [ts for ts in list(buckets) if ts < cutoff]
            for ts in stale:
                del buckets[ts]

            # Increment current-second bucket
            buckets[now_ts] = buckets.get(now_ts, 0) + 1

            total = sum(buckets.values())
            window_start = min(buckets.keys()) if buckets else now_ts

        return total, window_start


_fallback_cache = _TTLCache()


# ── Redis backend ─────────────────────────────────────────────────────────

_redis_client: Any = None  # type: ignore[assignment]
_redis_init_attempted = False


def _get_redis() -> Optional[Any]:
    global _redis_client, _redis_init_attempted
    if _redis_init_attempted:
        return _redis_client

    _redis_init_attempted = True
    url = os.getenv("REDIS_URL")
    if not url:
        return None

    try:
        import redis  # type: ignore[import]
        client = redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
        _redis_client = client
        logger.info("Rate limiter using Redis at %s", url.split("@")[-1])
    except Exception as exc:
        logger.warning("Redis unavailable (%s) — using TTLCache fallback", exc)
        _redis_client = None

    return _redis_client


def _redis_increment(key: str, window: int) -> tuple[int, int]:
    """
    Sliding window counter via Redis sorted set (ZADD + ZRANGEBYSCORE).
    Returns (current_count, window_start_ts).
    """
    import time as _time
    client = _get_redis()
    now = _time.time()
    cutoff = now - window
    member = str(now)

    pipe = client.pipeline()
    pipe.zadd(key, {member: now})
    pipe.zremrangebyscore(key, "-inf", cutoff)
    pipe.zcard(key)
    pipe.zrange(key, 0, 0, withscores=True)  # oldest member
    pipe.expire(key, window + 10)  # TTL with small buffer
    results = pipe.execute()

    count: int = results[2]
    oldest_score = results[3][0][1] if results[3] else now
    window_start = int(oldest_score)

    return count, window_start


# ── Public rate check ─────────────────────────────────────────────────────

def check_rate(identifier: str, tier: str) -> tuple[bool, dict]:
    """
    Check if identifier (user_id or IP) has remaining quota.

    Returns:
      (allowed: bool, headers: dict) — headers to attach to the response.
    """
    limit = _TIER_LIMITS.get(tier, _DEFAULT_LIMIT)
    key = f"rl:{tier}:{identifier}"

    try:
        redis = _get_redis()
        if redis:
            count, window_start = _redis_increment(key, _WINDOW_SECONDS)
        else:
            count, window_start = _fallback_cache.increment(key, _WINDOW_SECONDS)
    except Exception as exc:
        # Fail open: if rate limiter itself errors, let the request through
        logger.error("Rate limiter error: %s — failing open", exc)
        return True, {}

    remaining = max(0, limit - count)
    reset_ts = window_start + _WINDOW_SECONDS
    allowed = count <= limit

    headers = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_ts),
    }
    return allowed, headers


# ── Flask decorator ───────────────────────────────────────────────────────

def rate_limit(f: Callable) -> Callable:
    """
    Decorator for Flask route handlers.
    Reads user_id from request args/body and tier from active subscription.
    Falls back to IP-based limiting when user_id is unknown.
    """

    @wraps(f)
    def _inner(*args, **kwargs):
        if os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("0", "false", "no"):
            return f(*args, **kwargs)

        # Resolve identifier + tier
        user_id = (
            request.args.get("user_id")
            or (request.get_json(silent=True) or {}).get("user_id")
            or kwargs.get("user_id")
            or request.remote_addr
            or "anonymous"
        )

        tier = "free"
        try:
            from billing import get_subscription
            sub = get_subscription(str(user_id))
            if sub:
                tier = sub.tier
        except Exception:
            pass

        allowed, headers = check_rate(str(user_id), tier)

        if not allowed:
            resp = jsonify({
                "error": "Rate limit exceeded",
                "message": f"Tier '{tier}' allows {_TIER_LIMITS.get(tier, _DEFAULT_LIMIT)} requests/hour.",
                "retry_after": _WINDOW_SECONDS,
            })
            resp.status_code = 429
            resp.headers["Retry-After"] = str(_WINDOW_SECONDS)
            for h, v in headers.items():
                resp.headers[h] = v
            logger.warning("Rate limit hit: user=%s tier=%s", user_id, tier)
            return resp

        response = f(*args, **kwargs)

        # Attach rate limit headers to successful response
        if hasattr(response, "headers"):
            for h, v in headers.items():
                response.headers[h] = v

        return response

    return _inner
