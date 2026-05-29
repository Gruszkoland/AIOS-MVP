from __future__ import annotations

from datetime import datetime, timedelta, timezone

from arbitrage.project_state_confidence import compute_confidence, update_project_state_confidence


def test_should_not_return_100_when_idle_and_stale() -> None:
    now = datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)
    stale = (now - timedelta(days=7)).isoformat()

    confidence = compute_confidence(status="idle", updated_at=stale, last_task=None, now=now)

    assert confidence < 100


def test_should_increase_confidence_when_recent_and_active() -> None:
    now = datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)
    recent = (now - timedelta(minutes=10)).isoformat()

    active_confidence = compute_confidence(status="active", updated_at=recent, last_task="run-smoke", now=now)
    stale_idle_confidence = compute_confidence(
        status="idle",
        updated_at=(now - timedelta(days=5)).isoformat(),
        last_task=None,
        now=now,
    )

    assert active_confidence > stale_idle_confidence


def test_should_update_agents_and_metrics_in_state() -> None:
    now = datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)
    state = {
        "timestamp": "2026-05-20T00:00:00+00:00",
        "agents": {
            "A": {
                "status": "idle",
                "last_task": None,
                "updated_at": "2026-05-20T00:00:00+00:00",
                "confidence": 100,
            },
            "B": {
                "status": "active",
                "last_task": "task-1",
                "updated_at": "2026-05-29T11:50:00+00:00",
                "confidence": 100,
            },
        },
        "metrics": {},
    }

    updated = update_project_state_confidence(state, now=now)

    assert updated["agents"]["A"]["confidence"] < 100
    assert updated["agents"]["B"]["confidence"] > updated["agents"]["A"]["confidence"]
    assert updated["metrics"]["total_agents"] == 2
    assert updated["metrics"]["active_agents"] == 1
    assert updated["metrics"]["idle_agents"] == 1
