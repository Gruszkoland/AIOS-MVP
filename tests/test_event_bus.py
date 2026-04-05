"""Smoke test for memory event bus."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "harmonia-dashboard"))

from memory_events import (
    FEEDBACK_RECEIVED,
    INTERACTION_LOGGED,
    JUDGE_BLOCKED,
    JUDGE_WARNED,
    PROMOTED_TO_LONG_TERM,
    emit_feedback_received,
    emit_interaction_logged,
    emit_judge_blocked,
    emit_judge_warned,
    emit_promoted_to_long_term,
    get_event_bus,
)


def test_event_bus_smoke():
    received = []
    bus = get_event_bus()
    bus.reset_metrics()

    # Subscribe to all event types
    for et in [INTERACTION_LOGGED, FEEDBACK_RECEIVED, PROMOTED_TO_LONG_TERM, JUDGE_WARNED, JUDGE_BLOCKED]:
        bus.subscribe(et, lambda e, _et=et: received.append(e.event_type))

    # Emit each type
    emit_interaction_logged("test", "id1", category="smoke")
    emit_feedback_received("test", "id1", score=2)
    emit_promoted_to_long_term("test", "id2", score=5)
    emit_judge_warned("test", "id3", reason="drift detected")
    emit_judge_blocked("test", "id4", reason="below threshold")

    m = bus.get_metrics()
    print("Emitted:", m["events_emitted"])
    print("Delivered:", m["events_delivered"])
    print("Failed:", m["events_failed"])
    print("Types:", m["by_type"])
    print("Received:", received)
    print("Subs:", bus.subscriber_count())

    assert m["events_emitted"] == 5, f"Expected 5 emitted, got {m['events_emitted']}"
    assert m["events_delivered"] == 5, f"Expected 5 delivered, got {m['events_delivered']}"
    assert m["events_failed"] == 0, f"Expected 0 failed, got {m['events_failed']}"
    assert len(received) == 5, f"Expected 5 received, got {len(received)}"
    assert m["delivery_rate"] == 1.0, f"Expected 1.0 rate, got {m['delivery_rate']}"

    print("\nALL SMOKE TESTS PASSED")

if __name__ == "__main__":
    test_event_bus_smoke()
