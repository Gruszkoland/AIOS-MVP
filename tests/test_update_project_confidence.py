from scripts.reporting.update_project_confidence import compute_confidence


def test_compute_confidence_clamped_range() -> None:
    score = compute_confidence(success_rate=1.2, freshness_hours=0, completed_tasks=100)
    assert 0.0 <= score <= 100.0


def test_compute_confidence_drops_when_stale() -> None:
    fresh = compute_confidence(success_rate=0.95, freshness_hours=2, completed_tasks=10)
    stale = compute_confidence(success_rate=0.95, freshness_hours=120, completed_tasks=10)
    assert stale < fresh
