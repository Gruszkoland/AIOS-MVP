"""
ADRION 369 — Per-Endpoint Rate Limiter

Provides thread-safe sliding-window rate limiters keyed by client IP,
one per API endpoint family. Each endpoint has independently tunable
`max_requests` and `window_seconds` via environment variables.

Usage in request handlers:

    from arbitrage.rate_limiter import scout_limiter

    client_ip = self.client_address[0]
    if not scout_limiter.is_allowed(client_ip):
        self._send({"error": "Rate limit exceeded", "retry_after": 60}, 429)
        return
"""
import collections
import logging
import os
import threading
import time

logger = logging.getLogger("adrion.rate_limiter")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        v = int(raw)
        if v <= 0:
            raise ValueError
        return v
    except ValueError:
        logger.warning("Invalid env %s=%r — using default %d", name, raw, default)
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        v = float(raw)
        if v <= 0:
            raise ValueError
        return v
    except ValueError:
        logger.warning("Invalid env %s=%r — using default %.2f", name, raw, default)
        return default


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding-window rate limiter keyed by an arbitrary string key
    (typically a client IP address).

    Records each accepted request's timestamp. On every `is_allowed()` call,
    evicts timestamps older than `window_seconds` before deciding.
    """

    def __init__(self, max_requests: int, window_seconds: float, name: str = "") -> None:
        self._max = max_requests
        self._window = window_seconds
        self._name = name or "limiter"
        self._lock = threading.Lock()
        self._buckets: dict[str, collections.deque] = {}

    def is_allowed(self, key: str) -> bool:
        """Return True if the request should proceed; False if rate-limited."""
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            dq = self._buckets.setdefault(key, collections.deque())
            while dq and dq[0] < cutoff:
                dq.popleft()
            if len(dq) >= self._max:
                logger.debug(
                    "[%s] Rate limit hit for key=%s (%d/%d in %.0fs)",
                    self._name, key, len(dq), self._max, self._window,
                )
                return False
            dq.append(now)
            return True

    @property
    def max_requests(self) -> int:
        return self._max

    @property
    def window_seconds(self) -> float:
        return self._window


# ── Per-endpoint limiter instances ────────────────────────────────────────────
#
# Environment overrides (all optional):
#   SCOUT_RATE_LIMIT_MAX              default 10  (per IP per minute)
#   SCOUT_RATE_LIMIT_WINDOW_SECONDS   default 60
#   ORACLE_RATE_LIMIT_MAX             default 20
#   ORACLE_RATE_LIMIT_WINDOW_SECONDS  default 60
#   CYCLE_RATE_LIMIT_MAX              default 5
#   CYCLE_RATE_LIMIT_WINDOW_SECONDS   default 60
#   MASS_GEN_RATE_LIMIT_MAX           default 3
#   MASS_GEN_RATE_LIMIT_WINDOW_SECONDS default 60
#   QUANTUM_RATE_LIMIT_MAX            default 30
#   QUANTUM_RATE_LIMIT_WINDOW_SECONDS default 60

scout_limiter = SlidingWindowRateLimiter(
    max_requests=_env_int("SCOUT_RATE_LIMIT_MAX", 10),
    window_seconds=_env_float("SCOUT_RATE_LIMIT_WINDOW_SECONDS", 60.0),
    name="scout",
)

oracle_limiter = SlidingWindowRateLimiter(
    max_requests=_env_int("ORACLE_RATE_LIMIT_MAX", 20),
    window_seconds=_env_float("ORACLE_RATE_LIMIT_WINDOW_SECONDS", 60.0),
    name="oracle",
)

cycle_limiter = SlidingWindowRateLimiter(
    max_requests=_env_int("CYCLE_RATE_LIMIT_MAX", 5),
    window_seconds=_env_float("CYCLE_RATE_LIMIT_WINDOW_SECONDS", 60.0),
    name="cycle",
)

mass_gen_limiter = SlidingWindowRateLimiter(
    max_requests=_env_int("MASS_GEN_RATE_LIMIT_MAX", 3),
    window_seconds=_env_float("MASS_GEN_RATE_LIMIT_WINDOW_SECONDS", 60.0),
    name="mass_gen",
)

quantum_limiter = SlidingWindowRateLimiter(
    max_requests=_env_int("QUANTUM_RATE_LIMIT_MAX", 30),
    window_seconds=_env_float("QUANTUM_RATE_LIMIT_WINDOW_SECONDS", 60.0),
    name="quantum",
)
