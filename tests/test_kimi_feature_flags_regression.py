import os

from kimi_migration.feature_flags import is_kimi_enabled


def test_kimi_feature_flag_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_KIMI_MODULES", raising=False)
    assert is_kimi_enabled() is False


def test_kimi_feature_flag_enabled(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_KIMI_MODULES", "1")
    assert is_kimi_enabled() is True
