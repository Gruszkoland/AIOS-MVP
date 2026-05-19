"""
EBDI Homeostatic Decay Service + Event-Driven Trigger System.

Two responsibilities:
1. **Decay** (Section 3 of EBDI-MODEL.md): Exponential decay toward baseline.
       new_value = baseline + (current - baseline) * exp(-drift_rate * elapsed)
2. **Triggers** (Section 4 of EBDI-MODEL.md): System events inject PAD deltas.
       pad[dim] = clamp(0..1, pad[dim] + delta[dim])

Half-life: 60 seconds (configurable). Runs in a background daemon thread.
Pattern follows arbitrage/autopilot.py: Thread + Event.wait(timeout).
"""

import logging
import math
import threading
from typing import Callable, Dict, List, Optional

logger = logging.getLogger("adrion.uap.ebdi_homeostasis")

# Per EBDI-MODEL.md Section 3: baseline neutral state
EBDI_BASELINE: Dict[str, float] = {
    "pleasure": 0.0,
    "arousal": 0.0,
    "dominance": 0.5,
}

EBDI_HALF_LIFE_SECONDS = 60.0
EBDI_TICK_INTERVAL_SECONDS = 5.0

# ── EBDI-MODEL.md Section 4.1: Trigger Event Delta Table ────────────────────

EBDI_EVENT_DELTAS: Dict[str, Dict[str, float]] = {
    "mission_success":    {"pleasure": +0.5, "arousal": -0.2, "dominance": +0.3},
    "critical_error":     {"pleasure": -0.4, "arousal": +0.7, "dominance": -0.4},
    "security_anomaly":   {"pleasure": -0.3, "arousal": +0.6, "dominance": -0.3},
    "positive_feedback":  {"pleasure": +0.3, "arousal": -0.1, "dominance": +0.2},
    "timeout":            {"pleasure": -0.2, "arousal": +0.3, "dominance":  0.0},
    "abundant_resources":  {"pleasure": +0.1, "arousal":  0.0, "dominance": +0.1},
}

# EBDI-MODEL.md Section 4.2: Linguistic markers -> PAD deltas
EBDI_LINGUISTIC_MARKERS: Dict[str, Dict[str, float]] = {
    "dangerous": {"pleasure": -0.5, "arousal": +0.7, "dominance": -0.4},
    "risky":     {"pleasure": -0.3, "arousal": +0.5, "dominance": -0.2},
    "urgent":    {"pleasure":  0.0, "arousal": +0.8, "dominance":  0.0},
    "excellent": {"pleasure": +0.7, "arousal": -0.1, "dominance": +0.4},
    "trusted":   {"pleasure": +0.4, "arousal": -0.2, "dominance": +0.5},
    "stable":    {"pleasure": +0.2, "arousal": -0.3, "dominance": +0.3},
}


class EBDIHomeostaticService:
    """Background service applying exponential decay to EBDI telemetry vectors.

    Each tick (default 5s), all agent PAD dimensions decay toward their baseline
    values using the formula: baseline + (current - baseline) * exp(-rate * dt).

    Args:
        telemetry_store: Reference to the shared EBDI_TELEMETRY dict.
        half_life: Decay half-life in seconds (default 60s per spec).
        tick_interval: Seconds between decay ticks (default 5s).
    """

    def __init__(
        self,
        telemetry_store: Dict[str, Dict[str, float]],
        half_life: float = EBDI_HALF_LIFE_SECONDS,
        tick_interval: float = EBDI_TICK_INTERVAL_SECONDS,
    ):
        self._store = telemetry_store
        self._tick = tick_interval
        self._drift_rate = math.log(2) / half_life
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._event_listeners: List[Callable] = []

    def start(self) -> None:
        """Start the decay background thread (idempotent)."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="adrion-ebdi-homeostasis"
        )
        self._thread.start()
        logger.info("EBDI homeostatic decay service started (half-life=%.0fs, tick=%.0fs)",
                     math.log(2) / self._drift_rate, self._tick)

    def stop(self) -> None:
        """Stop the decay background thread gracefully."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
            logger.info("EBDI homeostatic decay service stopped")

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _loop(self) -> None:
        while not self._stop.is_set():
            self._apply_decay(self._tick)
            if self._stop.wait(self._tick):
                break

    def _apply_decay(self, elapsed: float) -> None:
        """Apply exponential decay toward baseline for all agents.

        Formula per EBDI-MODEL.md:
            decay_factor = exp(-drift_rate * elapsed)
            new_value = baseline + (current - baseline) * decay_factor
        """
        decay = math.exp(-self._drift_rate * elapsed)
        for pad in self._store.values():
            for dim in ("pleasure", "arousal", "dominance"):
                baseline_val = EBDI_BASELINE[dim]
                current = pad.get(dim, baseline_val)
                pad[dim] = max(0.0, min(1.0, baseline_val + (current - baseline_val) * decay))

    # ── U2: Event-Driven Triggers (EBDI-MODEL.md Section 4) ─────────────────

    def inject_event(self, agent: str, event_type: str) -> bool:
        """Inject a system event that modifies an agent's PAD vector.

        Args:
            agent: Agent name (must exist in telemetry store).
            event_type: One of EBDI_EVENT_DELTAS keys (e.g., 'mission_success').

        Returns:
            True if the event was applied, False if agent/event unknown.
        """
        deltas = EBDI_EVENT_DELTAS.get(event_type)
        if deltas is None:
            logger.warning("Unknown EBDI event type: %s", event_type)
            return False

        pad = self._store.get(agent)
        if pad is None:
            logger.warning("Unknown agent for EBDI event: %s", agent)
            return False

        with self._lock:
            for dim in ("pleasure", "arousal", "dominance"):
                pad[dim] = max(0.0, min(1.0, pad[dim] + deltas[dim]))

        logger.info("EBDI event '%s' injected for %s: P=%.2f A=%.2f D=%.2f",
                     event_type, agent, pad["pleasure"], pad["arousal"], pad["dominance"])

        # Notify listeners (e.g., WebSocket broadcast)
        for listener in self._event_listeners:
            try:
                listener(agent, event_type, pad)
            except Exception as exc:
                logger.warning("EBDI event listener error: %s", exc)

        return True

    def inject_linguistic_markers(self, agent: str, text: str) -> int:
        """Scan text for linguistic markers and inject PAD deltas.

        Per EBDI-MODEL.md Section 4.2. Returns the number of markers found.
        """
        count = 0
        text_lower = text.lower()
        pad = self._store.get(agent)
        if pad is None:
            return 0

        with self._lock:
            for marker, deltas in EBDI_LINGUISTIC_MARKERS.items():
                if marker in text_lower:
                    for dim in ("pleasure", "arousal", "dominance"):
                        pad[dim] = max(0.0, min(1.0, pad[dim] + deltas[dim]))
                    count += 1

        if count:
            logger.info("Linguistic markers injected for %s: %d marker(s)", agent, count)
        return count

    def on_event(self, listener: Callable) -> None:
        """Register a callback for EBDI events: fn(agent, event_type, pad_dict)."""
        self._event_listeners.append(listener)
