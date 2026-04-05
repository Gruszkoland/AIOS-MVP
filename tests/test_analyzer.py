"""Tests for arbitrage/analyzer.py — job scoring and LLM integration (mocked)."""
import sys
from unittest.mock import MagicMock, patch

# ── Import helper ─────────────────────────────────────────────────────────────

def get_analyzer():
    import importlib
    if "arbitrage.analyzer" in sys.modules:
        del sys.modules["arbitrage.analyzer"]
    return importlib.import_module("arbitrage.analyzer")


# ── digital_root ──────────────────────────────────────────────────────────────

class TestDigitalRoot:
    def test_digital_root_nine(self):
        mod = get_analyzer()
        assert mod.digital_root(18) == 9
        assert mod.digital_root(9) == 9
        assert mod.digital_root(162) == 9

    def test_digital_root_one(self):
        mod = get_analyzer()
        assert mod.digital_root(1) == 1
        assert mod.digital_root(10) == 1

    def test_digital_root_zero(self):
        mod = get_analyzer()
        assert mod.digital_root(0) == 0


# ── vortex_filter ─────────────────────────────────────────────────────────────

class TestVortexFilter:
    def test_passes_high_margin_with_369_root(self):
        mod = get_analyzer()
        # margin_pct = 0.18 → int(18) = 18 → digital_root=9 → pass, and 0.18 >= 0.15 ✓
        assert mod.vortex_filter(0.18) is True

    def test_rejects_below_min_margin(self):
        mod = get_analyzer()
        assert mod.vortex_filter(0.05) is False

    def test_rejects_non_369_margin(self):
        mod = get_analyzer()
        # 0.20 → int(20) = 20 → digital_root=2 → not 3/6/9 → reject
        assert mod.vortex_filter(0.20) is False

    def test_custom_min_margin(self):
        mod = get_analyzer()
        # 0.12 passes if min_margin=0.10 and root is 369
        # 0.12 → int(12) = 12 → digital_root=3 → pass
        assert mod.vortex_filter(0.12, min_margin=0.10) is True


# ── calculate_market_resonance ────────────────────────────────────────────────

class TestCalculateMarketResonance:
    def test_valid_prices(self):
        mod = get_analyzer()
        result = mod.calculate_market_resonance(100.0, 200.0)
        assert "resonance" in result
        assert "margin_pct" in result
        assert "vortex_pass" in result
        assert "is_369" in result

    def test_invalid_prices_return_zero(self):
        mod = get_analyzer()
        result = mod.calculate_market_resonance(0, 100)
        assert result["resonance"] == 0
        assert result["vortex_pass"] is False

    def test_retail_below_wholesale_returns_zero(self):
        mod = get_analyzer()
        result = mod.calculate_market_resonance(200.0, 100.0)
        assert result["margin_pct"] == 0.0


# ── analyze_job ───────────────────────────────────────────────────────────────

class TestAnalyzeJob:
    def _sample_job(self):
        return {
            "id": "test-001",
            "title": "SEO Writer",
            "platform": "upwork",
            "budget_min": 100,
            "budget_max": 300,
            "description": "Write blog posts.",
        }

    def test_analyze_job_mock_backend(self, monkeypatch):
        monkeypatch.setenv("LLM_BACKEND", "mock")
        mod = get_analyzer()
        result = mod.analyze_job(self._sample_job())
        assert isinstance(result, dict)
        assert "score" in result
        assert 1 <= result["score"] <= 10
        assert result["llm_backend"] == "mock"

    def test_analyze_job_returns_all_keys(self, monkeypatch):
        monkeypatch.setenv("LLM_BACKEND", "mock")
        mod = get_analyzer()
        result = mod.analyze_job(self._sample_job())
        for key in ("score", "fit", "risks", "est_hours", "our_price", "est_cost", "est_profit"):
            assert key in result, f"Missing key: {key}"

    def test_analyze_job_falls_back_on_bad_json(self, monkeypatch):
        monkeypatch.setenv("LLM_BACKEND", "openrouter")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
        mod = get_analyzer()
        bad_choice = MagicMock()
        bad_choice.message.content = "I am not JSON {{{brokennnnn"
        fake_client = MagicMock()
        fake_client.chat.completions.create.return_value = MagicMock(choices=[bad_choice])
        # OpenAI is imported lazily inside _call_openrouter, patch via openai module
        with patch("openai.OpenAI", return_value=fake_client):
            result = mod.analyze_job(self._sample_job())
        assert result is not None
        assert "score" in result


# ── filter_worthy ─────────────────────────────────────────────────────────────

class TestFilterWorthy:
    def test_passes_good_analysis(self, monkeypatch):
        monkeypatch.setenv("MIN_ANALYZER_SCORE", "7")
        monkeypatch.setenv("MIN_PROFIT_USD", "30")
        mod = get_analyzer()
        assert mod.filter_worthy({"score": 8, "est_profit": 50}) is True

    def test_rejects_low_score(self, monkeypatch):
        monkeypatch.setenv("MIN_ANALYZER_SCORE", "7")
        monkeypatch.setenv("MIN_PROFIT_USD", "30")
        mod = get_analyzer()
        assert mod.filter_worthy({"score": 4, "est_profit": 100}) is False

    def test_rejects_low_profit(self, monkeypatch):
        monkeypatch.setenv("MIN_ANALYZER_SCORE", "7")
        monkeypatch.setenv("MIN_PROFIT_USD", "30")
        mod = get_analyzer()
        assert mod.filter_worthy({"score": 9, "est_profit": 5}) is False
