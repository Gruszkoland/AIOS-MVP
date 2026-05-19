"""
ADRION 369 — Circuit Breaker

Protects external API calls (LLM, Stripe, Apify, XRP price feeds) from
cascading failures. When `failure_threshold` consecutive failures occur,
the breaker opens and immediately raises CircuitBreakerOpen without
attempting the call, giving the downstream service time to recover.

States:
    CLOSED     — normal operation; all calls pass through
    OPEN       — downstream is failing; calls are rejected immediately
    HALF_OPEN  — one probe call is allowed; success → CLOSED, failure → OPEN

Usage:

    from arbitrage.circuit_breaker import llm_breaker

    try:
        result = llm_breaker.call(my_llm_function, prompt="hello")
    except CircuitBreakerOpen as exc:
        # Return a safe fallback instead of calling the LLM
        result = {"text": "LLM temporarily unavailable — retrying soon."}
    except SomeLLMError:
        pass  # circuit breaker already counted this failure

Backoff:
    Retry-after delay doubles on each consecutive failure up to MAX_BACKOFF_SECONDS.
    After recovery_timeout seconds in OPEN state, the breaker enters HALF_OPEN.
"""
import logging
import threading
import time
from typing import Any, Callable

logger = logging.getLogger("adrion.circuit_breaker")

MAX_BACKOFF_SECONDS: float = 300.0  # 5 minutes ceiling


class CircuitBreakerOpen(Exception):
    """Raised when a call is rejected because the circuit is open."""

    def __init__(self, name: str, retry_after: float) -> None:
        self.name = name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit '{name}' is OPEN. Retry after {retry_after:.1f}s."
        )


class CircuitBreaker:
    """
    Thread-safe circuit breaker with exponential backoff.

    Args:
        name: Human-readable name (used in logs and exceptions).
        failure_threshold: Consecutive failures before opening the circuit.
        recovery_timeout: Seconds to wait after opening before probing.
        success_threshold: Consecutive successes in HALF_OPEN before closing.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._lock = threading.Lock()
        self._state: str = "CLOSED"
        self._failure_count: int = 0
        self._success_count: int = 0
        self._last_failure_time: float = 0.0
        self._backoff: float = recovery_timeout

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def state(self) -> str:
        """Current state: CLOSED, OPEN, or HALF_OPEN."""
        with self._lock:
            self._maybe_transition_to_half_open()
            return self._state

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Call `func` if the circuit allows it.

        Raises:
            CircuitBreakerOpen: When the circuit is OPEN and recovery_timeout
                                has not elapsed.
            Any exception raised by `func` (after recording a failure).
        """
        with self._lock:
            self._maybe_transition_to_half_open()

            if self._state == "OPEN":
                retry_after = max(
                    0.0,
                    self._last_failure_time + self._backoff - time.monotonic(),
                )
                raise CircuitBreakerOpen(self.name, retry_after)

        # Execute outside the lock to avoid blocking other threads
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def reset(self) -> None:
        """Manually close the circuit (e.g., after a manual intervention)."""
        with self._lock:
            self._state = "CLOSED"
            self._failure_count = 0
            self._success_count = 0
            self._backoff = self.recovery_timeout
        logger.info("[CB:%s] Manually reset to CLOSED", self.name)

    def status(self) -> dict:
        """Return a snapshot of the breaker's internal state."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "backoff_seconds": self._backoff,
                "last_failure_at": self._last_failure_time or None,
            }

    # ── Internal transitions ──────────────────────────────────────────────────

    def _on_success(self) -> None:
        with self._lock:
            if self._state == "HALF_OPEN":
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = "CLOSED"
                    self._failure_count = 0
                    self._success_count = 0
                    self._backoff = self.recovery_timeout
                    logger.info("[CB:%s] HALF_OPEN → CLOSED after %d successes", self.name, self.success_threshold)
            elif self._state == "CLOSED":
                self._failure_count = 0

    def _on_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == "HALF_OPEN":
                # Probe failed — reopen immediately
                self._state = "OPEN"
                self._backoff = min(self._backoff * 2, MAX_BACKOFF_SECONDS)
                logger.warning(
                    "[CB:%s] HALF_OPEN → OPEN (probe failed); next retry in %.0fs",
                    self.name, self._backoff,
                )
            elif self._failure_count >= self.failure_threshold:
                self._state = "OPEN"
                self._backoff = min(self._backoff * 2, MAX_BACKOFF_SECONDS)
                logger.warning(
                    "[CB:%s] CLOSED → OPEN after %d failures; next retry in %.0fs",
                    self.name, self._failure_count, self._backoff,
                )
            else:
                logger.debug(
                    "[CB:%s] Failure %d/%d",
                    self.name, self._failure_count, self.failure_threshold,
                )

    def _maybe_transition_to_half_open(self) -> None:
        """Called under lock — transition OPEN → HALF_OPEN if timeout elapsed."""
        if (
            self._state == "OPEN"
            and time.monotonic() - self._last_failure_time >= self._backoff
        ):
            self._state = "HALF_OPEN"
            self._success_count = 0
            logger.info("[CB:%s] OPEN → HALF_OPEN (probe window open)", self.name)


# ── Pre-configured breakers for each external dependency ─────────────────────

llm_breaker = CircuitBreaker(
    name="llm",
    failure_threshold=3,
    recovery_timeout=60.0,
)

stripe_breaker = CircuitBreaker(
    name="stripe",
    failure_threshold=2,
    recovery_timeout=30.0,
)

apify_breaker = CircuitBreaker(
    name="apify",
    failure_threshold=3,
    recovery_timeout=120.0,
)

xrp_feed_breaker = CircuitBreaker(
    name="xrp_feed",
    failure_threshold=5,
    recovery_timeout=30.0,
)


def all_statuses() -> list[dict]:
    """Return status snapshots for all pre-configured breakers."""
    return [
        llm_breaker.status(),
        stripe_breaker.status(),
        apify_breaker.status(),
        xrp_feed_breaker.status(),
    ]
