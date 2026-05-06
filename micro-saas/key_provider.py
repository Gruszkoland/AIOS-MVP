"""
micro-saas key_provider — lazy API key loader with hot-reload.

Design:
  - `get_api_key()` reads `UAP_API_KEY` from environment on EVERY call
    (lazy, no module-level cache). This allows key rotation without restart.
  - On POSIX systems: send SIGHUP to the process to log a rotation event
    (Python does NOT need to restart — the next `get_api_key()` call picks
    up the new value automatically via os.getenv).
  - On Windows: env var updates propagate after the parent process sets them;
    SIGHUP is not available. Rotation is still zero-downtime via process-level
    env var update (e.g., Docker `--env-file` + rolling restart is recommended).

Security:
  - hmac.compare_digest is used at the call site (never expose raw key in logs).
  - Empty key string means server is misconfigured — all protected endpoints return 500.
"""
from __future__ import annotations

import logging
import os
import signal

logger = logging.getLogger("adrion.micro_saas.key_provider")

_ENV_VAR = "UAP_API_KEY"


def get_api_key() -> str:
    """Return current UAP_API_KEY from environment (read on every call).

    Never caches the value — callers always get the live key.
    """
    return os.getenv(_ENV_VAR, "")


def is_key_set() -> bool:
    """Return True if UAP_API_KEY is non-empty."""
    return bool(get_api_key())


# ── SIGHUP rotation handler (POSIX only) ─────────────────────────────────

def _handle_sighup(signum: int, frame) -> None:  # noqa: ANN001
    """Log key rotation event on SIGHUP. Key is picked up automatically."""
    new_key = get_api_key()
    status = "set" if new_key else "EMPTY (misconfigured)"
    logger.info("SIGHUP received — UAP_API_KEY reloaded: %s", status)


def register_sighup_handler() -> None:
    """Register SIGHUP handler for graceful key rotation (no-op on Windows)."""
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, _handle_sighup)
        logger.debug("SIGHUP handler registered for API key hot-reload")
    else:
        logger.debug("SIGHUP not available on this platform (Windows) — key rotation via env update")
