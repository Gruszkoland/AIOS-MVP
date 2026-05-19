"""Tests for arbitrage/amplifier.py — AdrionAmplifier (G5/G6/G7 Guardian class)."""
import pytest

from arbitrage.amplifier import AdrionAmplifier


@pytest.fixture
def amplifier(monkeypatch):
    monkeypatch.setenv("LINKEDIN_API_BASE", "https://api.linkedin.com/v2")
    monkeypatch.setenv("MIN_TRINITY_PUBLISH", "0.65")
    # No real LinkedIn credentials → safe
    monkeypatch.delenv("LINKEDIN_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("LINKEDIN_ACCOUNT_ID", raising=False)
    return AdrionAmplifier()


@pytest.fixture
def strong_achievement():
    return {
        "title": "Vortex Engine Released",
        "description": "Full 3-6-9 logic in Go with 97% coverage.",
        "metrics": {"tests": 45, "coverage": 0.97},
        "trinity_scores": {"material": 0.9, "intellectual": 0.85, "essential": 0.95},
    }


@pytest.fixture
def weak_achievement():
    return {
        "title": "Minor Tweak",
        "description": "Reformatted some files.",
        "metrics": {},                           # no metrics → not authentic
        "trinity_scores": {"material": 0.3, "intellectual": 0.4, "essential": 0.3},
    }


# ── analyze_achievement ───────────────────────────────────────────────────────

class TestAnalyzeAchievement:
    def test_publish_when_above_threshold(self, amplifier, strong_achievement):
        can_publish, status, score = amplifier.analyze_achievement(strong_achievement)
        assert can_publish is True
        assert status == "READY_TO_PUBLISH"
        assert score >= 0.65

    def test_reject_low_alignment(self, amplifier, weak_achievement):
        can_publish, status, score = amplifier.analyze_achievement(weak_achievement)
        assert can_publish is False
        assert "REJECTED" in status

    def test_needs_review_mid_score(self, amplifier):
        mid_achievement = {
            "title": "Mid Effort",
            "description": "Some useful work.",
            "metrics": {"items": 1},
            "trinity_scores": {"material": 0.60, "intellectual": 0.55, "essential": 0.55},
        }
        can_publish, status, score = amplifier.analyze_achievement(mid_achievement)
        assert not can_publish
        assert score < 0.65

    def test_no_trinity_scores_returns_zero_avg(self, amplifier):
        achievement = {"title": "X", "description": "Y", "metrics": {"a": 1}, "trinity_scores": {}}
        can_publish, status, score = amplifier.analyze_achievement(achievement)
        assert score == 0.0

    def test_authenticity_required_for_publish(self, amplifier):
        # No metrics → not authentic even if scores are high
        achievement = {
            "title": "High Score No Metrics",
            "description": "...",
            "metrics": {},
            "trinity_scores": {"material": 0.9, "intellectual": 0.9, "essential": 0.9},
        }
        can_publish, status, _ = amplifier.analyze_achievement(achievement)
        assert not can_publish


# ── generate_post_content ─────────────────────────────────────────────────────

class TestGeneratePostContent:
    def test_post_contains_title(self, amplifier, strong_achievement):
        post = amplifier.generate_post_content(strong_achievement, 0.9)
        assert "Vortex Engine Released" in post

    def test_post_contains_hashtags(self, amplifier, strong_achievement):
        post = amplifier.generate_post_content(strong_achievement, 0.9)
        assert "#ADRION369" in post

    def test_post_contains_trinity_breakdown(self, amplifier, strong_achievement):
        post = amplifier.generate_post_content(strong_achievement, 0.9)
        assert "Material" in post
        assert "Intellectual" in post
        assert "Essential" in post

    def test_post_contains_score(self, amplifier, strong_achievement):
        post = amplifier.generate_post_content(strong_achievement, 0.90)
        assert "0.90" in post


# ── publish_to_linkedin ───────────────────────────────────────────────────────

class TestPublishToLinkedIn:
    def test_publish_fails_without_credentials(self, amplifier):
        result = amplifier.publish_to_linkedin("some content")
        assert result is False

    def test_publish_succeeds_with_credentials(self, amplifier, monkeypatch):
        monkeypatch.setattr(amplifier, "access_token", "tok_test")
        monkeypatch.setattr(amplifier, "account_id", "acc_test")
        result = amplifier.publish_to_linkedin("some content")
        assert result is True
