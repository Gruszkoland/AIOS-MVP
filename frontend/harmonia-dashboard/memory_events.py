"""
ADRION 369 — Memory Event Bus (Local-First)
Centralny bus zdarzeń pamięci eliminujący bezpośredni coupling między modułami.

Guardian Laws:
  - G5 (Transparency): każde zdarzenie ma ślad i timestamp
  - G7 (Privacy): zero eksportu, lokalne callbacki
  - G9 (Sustainability): lekki, bezstanowy, bez zewnętrznych zależności

Zdarzenia:
  - interaction_logged: nowa interakcja zapisana
  - feedback_received: użytkownik dał feedback
  - promoted_to_long_term: wspomnienie awansowane
  - judge_warned: Sędzia wydał ostrzeżenie
  - judge_blocked: Sędzia zablokował odpowiedź
"""

import time
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional


# ===== EVENT TYPES =====
INTERACTION_LOGGED = "interaction_logged"
FEEDBACK_RECEIVED = "feedback_received"
PROMOTED_TO_LONG_TERM = "promoted_to_long_term"
JUDGE_WARNED = "judge_warned"
JUDGE_BLOCKED = "judge_blocked"

ALL_EVENTS = frozenset({
    INTERACTION_LOGGED,
    FEEDBACK_RECEIVED,
    PROMOTED_TO_LONG_TERM,
    JUDGE_WARNED,
    JUDGE_BLOCKED,
})


@dataclass
class MemoryEvent:
    """Pojedyncze zdarzenie pamięci."""
    event_type: str
    timestamp: str = ""
    source_module: str = ""
    interaction_id: str = ""
    payload: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


# ===== METRICS =====
@dataclass
class EventMetrics:
    """Metryki operacyjne event bus."""
    events_emitted: int = 0
    events_delivered: int = 0
    events_failed: int = 0
    last_event_time: str = ""
    by_type: dict = field(default_factory=dict)
    avg_delivery_ms: float = 0.0
    _total_delivery_ms: float = 0.0

    def record_emit(self, event_type: str):
        self.events_emitted += 1
        self.last_event_time = datetime.now(timezone.utc).isoformat()
        self.by_type[event_type] = self.by_type.get(event_type, 0) + 1

    def record_delivery(self, duration_ms: float, success: bool):
        if success:
            self.events_delivered += 1
        else:
            self.events_failed += 1
        self._total_delivery_ms += duration_ms
        total = self.events_delivered + self.events_failed
        if total > 0:
            self.avg_delivery_ms = round(self._total_delivery_ms / total, 2)

    def to_dict(self) -> dict:
        return {
            "events_emitted": self.events_emitted,
            "events_delivered": self.events_delivered,
            "events_failed": self.events_failed,
            "delivery_rate": round(self.events_delivered / max(self.events_emitted, 1), 3),
            "avg_delivery_ms": self.avg_delivery_ms,
            "last_event_time": self.last_event_time,
            "by_type": dict(self.by_type),
        }


# ===== EVENT BUS =====
class MemoryEventBus:
    """
    Synchroniczny, lokalny event bus.
    Subskrybenci rejestrują callbacki per typ zdarzenia.
    Brak kolejek, brak sieci, brak eksportu.
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable[[MemoryEvent], None]]] = {}
        self._metrics = EventMetrics()

    def subscribe(self, event_type: str, callback: Callable[[MemoryEvent], None]):
        """Zarejestruj callback dla danego typu zdarzenia."""
        if event_type not in ALL_EVENTS:
            raise ValueError(f"Unknown event type: {event_type}. Valid: {ALL_EVENTS}")
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def emit(self, event: MemoryEvent):
        """Wyemituj zdarzenie do wszystkich subskrybentów danego typu."""
        self._metrics.record_emit(event.event_type)
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            t0 = time.monotonic()
            try:
                handler(event)
                duration_ms = (time.monotonic() - t0) * 1000
                self._metrics.record_delivery(duration_ms, success=True)
            except Exception:
                duration_ms = (time.monotonic() - t0) * 1000
                self._metrics.record_delivery(duration_ms, success=False)

    def get_metrics(self) -> dict:
        """Zwróć metryki operacyjne bus."""
        return self._metrics.to_dict()

    def subscriber_count(self, event_type: str = None) -> int:
        """Ile callbacków jest zarejestrowanych."""
        if event_type:
            return len(self._subscribers.get(event_type, []))
        return sum(len(v) for v in self._subscribers.values())

    def reset_metrics(self):
        """Resetuj metryki operacyjne (głównie dla testów)."""
        self._metrics = EventMetrics()


# ===== SINGLETON =====
_bus: Optional[MemoryEventBus] = None


def get_event_bus() -> MemoryEventBus:
    global _bus
    if _bus is None:
        _bus = MemoryEventBus()
    return _bus


# ===== HELPER EMITTERS =====

def emit_interaction_logged(source: str, interaction_id: str, **extra):
    get_event_bus().emit(MemoryEvent(
        event_type=INTERACTION_LOGGED,
        source_module=source,
        interaction_id=interaction_id,
        payload=extra,
    ))


def emit_feedback_received(source: str, interaction_id: str, score: int = 0, **extra):
    get_event_bus().emit(MemoryEvent(
        event_type=FEEDBACK_RECEIVED,
        source_module=source,
        interaction_id=interaction_id,
        payload={"score": score, **extra},
    ))


def emit_promoted_to_long_term(source: str, interaction_id: str, **extra):
    get_event_bus().emit(MemoryEvent(
        event_type=PROMOTED_TO_LONG_TERM,
        source_module=source,
        interaction_id=interaction_id,
        payload=extra,
    ))


def emit_judge_warned(source: str, interaction_id: str, reason: str = "", **extra):
    get_event_bus().emit(MemoryEvent(
        event_type=JUDGE_WARNED,
        source_module=source,
        interaction_id=interaction_id,
        payload={"reason": reason, **extra},
    ))


def emit_judge_blocked(source: str, interaction_id: str, reason: str = "", **extra):
    get_event_bus().emit(MemoryEvent(
        event_type=JUDGE_BLOCKED,
        source_module=source,
        interaction_id=interaction_id,
        payload={"reason": reason, **extra},
    ))
