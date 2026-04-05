"""Tests for arbitrage/config.py — environment configuration and defaults."""
import importlib
import sys



# ── Helper ────────────────────────────────────────────────────────────────────

def reload_config():
    """Force-reload the config module so env vars take effect."""
    if "arbitrage.config" in sys.modules:
        del sys.modules["arbitrage.config"]
    return importlib.import_module("arbitrage.config")


# ── Default values ────────────────────────────────────────────────────────────

class TestConfigDefaults:
    def test_db_engine_default(self, clean_env):
        cfg = reload_config()
        assert cfg.DB_ENGINE == "sqlite"

    def test_llm_backend_default(self, clean_env):
        cfg = reload_config()
        assert cfg.LLM_BACKEND == "auto"

    def test_daily_bid_limit_default(self, clean_env):
        cfg = reload_config()
        assert cfg.DAILY_BID_LIMIT == 20

    def test_min_profit_default(self, clean_env):
        cfg = reload_config()
        assert cfg.MIN_PROFIT_USD == 30.0

    def test_min_analyzer_score_default(self, clean_env):
        cfg = reload_config()
        assert cfg.MIN_ANALYZER_SCORE == 7

    def test_max_est_cost_default(self, clean_env):
        cfg = reload_config()
        assert cfg.MAX_EST_COST_PER_BID_USD == 2.5

    def test_scout_platforms_default(self, clean_env):
        cfg = reload_config()
        assert "upwork" in cfg.SCOUT_PLATFORMS
        assert "fiverr" in cfg.SCOUT_PLATFORMS


# ── Env overrides ─────────────────────────────────────────────────────────────

class TestConfigEnvOverrides:
    def test_db_engine_override(self, monkeypatch):
        monkeypatch.setenv("DB_ENGINE", "postgres")
        cfg = reload_config()
        assert cfg.DB_ENGINE == "postgres"

    def test_daily_bid_limit_override(self, monkeypatch):
        monkeypatch.setenv("DAILY_BID_LIMIT", "5")
        cfg = reload_config()
        assert cfg.DAILY_BID_LIMIT == 5

    def test_min_profit_override(self, monkeypatch):
        monkeypatch.setenv("MIN_PROFIT_USD", "50.5")
        cfg = reload_config()
        assert cfg.MIN_PROFIT_USD == 50.5

    def test_xrp_target_override(self, monkeypatch):
        monkeypatch.setenv("XRP_TARGET", "2000")
        cfg = reload_config()
        assert cfg.XRP_TARGET == 2000.0


# ── get_active_llm_backend ────────────────────────────────────────────────────

class TestGetActiveLLMBackend:
    def test_explicit_backend_returns_as_is(self, monkeypatch):
        monkeypatch.setenv("LLM_BACKEND", "openai")
        cfg = reload_config()
        assert cfg.get_active_llm_backend() == "openai"

    def test_auto_picks_openrouter_when_key_present(self, clean_env, monkeypatch):
        monkeypatch.setenv("LLM_BACKEND", "auto")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
        cfg = reload_config()
        assert cfg.get_active_llm_backend() == "openrouter"

    def test_auto_picks_openai_when_only_openai_key(self, clean_env, monkeypatch):
        monkeypatch.setenv("LLM_BACKEND", "auto")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
        cfg = reload_config()
        assert cfg.get_active_llm_backend() == "openai"

    def test_auto_falls_back_to_mock(self, clean_env):
        # clean_env removes all API keys, so auto-detection should fall back to mock
        cfg = reload_config()
        assert cfg.get_active_llm_backend() == "mock"

    def test_anthropic_backend_selected(self, clean_env, monkeypatch):
        monkeypatch.setenv("LLM_BACKEND", "anthropic")
        cfg = reload_config()
        assert cfg.get_active_llm_backend() == "anthropic"


# ── Quantum scan channels ─────────────────────────────────────────────────────

class TestQuantumScanChannels:
    def test_five_channels_defined(self, clean_env):
        cfg = reload_config()
        assert len(cfg.QUANTUM_SCAN_CHANNELS) == 5

    def test_channels_have_required_keys(self, clean_env):
        cfg = reload_config()
        for ch in cfg.QUANTUM_SCAN_CHANNELS:
            assert "id" in ch
            assert "min_margin" in ch
            assert "frequency" in ch
            assert "keywords" in ch
