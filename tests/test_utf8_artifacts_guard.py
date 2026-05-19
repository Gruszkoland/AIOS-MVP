from __future__ import annotations

from scripts.reporting.check_utf8_artifacts import find_utf8_issues


def test_accepts_polish_utf8_text() -> None:
    text = "Zażółć gęślą jaźń — poprawny UTF-8 oraz 162D"
    issues = find_utf8_issues(text)
    assert issues == []


def test_detects_replacement_character() -> None:
    text = "Błędny znak: \ufffd"
    issues = find_utf8_issues(text)
    assert any("U+FFFD" in item for item in issues)


def test_detects_mojibake_token() -> None:
    text = "To jest uszkodzone: Ã³ i â€”"
    issues = find_utf8_issues(text)
    assert any("mojibake" in item for item in issues)
