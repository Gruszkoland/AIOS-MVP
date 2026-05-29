from kimi_migration.trinity_kurs import KursVector, evaluate_kurs_drift


def test_kurs_vector_mean() -> None:
    kv = KursVector(0.9, 0.9, 0.9, 0.9, 0.9)
    assert kv.mean() == 0.9


def test_kurs_drift_threshold_behavior() -> None:
    target = KursVector(0.9, 0.9, 0.9, 0.9, 0.9)
    drift = evaluate_kurs_drift(target, 0.3)
    assert drift > 0.5
