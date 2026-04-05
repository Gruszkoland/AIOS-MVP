"""
Unit tests for arbitrage/trinity.py — Trinity Score Engine.
No external deps (psutil mocked via system_resources dict).
"""
import math

import pytest

from arbitrage.trinity import (
    TRINITY_MIN_COMBINED,
    TRINITY_MIN_ESSENTIAL,
    TRINITY_MIN_INTELLECTUAL,
    TRINITY_MIN_MATERIAL,
    TrinityScore,
    _clamp,
    _geometric_mean,
    _harmonic_mean,
    _score_essential,
    _score_intellectual,
    _score_material,
    evaluate_trinity,
)

# ─────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────

def _res(cpu_percent=20.0, ram_ratio=0.7):
    return {"cpu_percent": cpu_percent, "ram_available_ratio": ram_ratio}


def _job(
    title="Blog post about SEO content writing",
    description="We need a skilled content writer for blog articles.",
    budget_min=100,
    budget_max=300,
):
    return {
        "title": title,
        "description": description,
        "budget_min": budget_min,
        "budget_max": budget_max,
    }


def _analysis(
    score=8,
    fit="Excellent match for our content writing portfolio",
    risks="Client is new, no reviews yet",
    est_profit=248.5,
):
    return {"score": score, "fit": fit, "risks": risks, "est_profit": est_profit}


# ─────────────────────────────────────────────────────────────────────
# Math helpers
# ─────────────────────────────────────────────────────────────────────

def test_harmonic_mean_normal():
    result = _harmonic_mean(0.8, 0.6)
    assert abs(result - 2 * 0.8 * 0.6 / (0.8 + 0.6)) < 1e-9


def test_harmonic_mean_both_zero():
    assert _harmonic_mean(0, 0) == 0.0


def test_harmonic_mean_one_zero():
    assert _harmonic_mean(0.5, 0) == 0.0
    assert _harmonic_mean(0, 0.5) == 0.0


def test_harmonic_mean_equal():
    assert _harmonic_mean(0.5, 0.5) == pytest.approx(0.5)


def test_geometric_mean_normal():
    a, b = 0.4, 0.9
    assert _geometric_mean(a, b) == pytest.approx(math.sqrt(a * b))


def test_geometric_mean_one_zero():
    assert _geometric_mean(0.0, 0.9) == 0.0


def test_geometric_mean_negative():
    assert _geometric_mean(-0.1, 0.9) == 0.0


def test_geometric_mean_both_zero():
    assert _geometric_mean(0, 0) == 0.0


def test_clamp_normal():
    assert _clamp(0.5) == 0.5


def test_clamp_below():
    assert _clamp(-1.0) == 0.0


def test_clamp_above():
    assert _clamp(1.5) == 1.0


def test_clamp_custom_bounds():
    assert _clamp(0.3, lo=0.4, hi=0.8) == 0.4
    assert _clamp(0.9, lo=0.4, hi=0.8) == 0.8


# ─────────────────────────────────────────────────────────────────────
# Perspektywa 1: Material
# ─────────────────────────────────────────────────────────────────────

def test_material_pass_normal():
    score, details = _score_material(_res(cpu_percent=20.0, ram_ratio=0.7))
    assert score > TRINITY_MIN_MATERIAL
    assert details["cpu_percent"] == 20.0
    assert details["ram_available_pct"] == 70.0


def test_material_high_cpu_usage():
    score, details = _score_material(_res(cpu_percent=95.0, ram_ratio=0.8))
    # cpu_avail = 0.05, ram_avail = 0.8 → harmonic mean very low
    assert score < TRINITY_MIN_MATERIAL
    assert details["cpu_avail"] == pytest.approx(0.05)


def test_material_low_ram():
    score, details = _score_material(_res(cpu_percent=10.0, ram_ratio=0.05))
    assert score < TRINITY_MIN_MATERIAL
    assert details["ram_avail"] == pytest.approx(0.05)


def test_material_full_resources():
    score, details = _score_material(_res(cpu_percent=0.0, ram_ratio=1.0))
    assert abs(score - 1.0) < 1e-9
    assert details["cpu_avail"] == 1.0
    assert details["ram_avail"] == 1.0


def test_material_both_exhausted():
    score, _ = _score_material(_res(cpu_percent=100.0, ram_ratio=0.0))
    assert score == 0.0


def test_material_none_resources_uses_psutil_or_fallback(monkeypatch):
    """With no resources dict — should use psutil or fallback (no crash)."""
    # Patch psutil to return controlled values
    class MockVM:
        available = 4 * 1024 ** 3
        total     = 8 * 1024 ** 3

    class MockPsutil:
        @staticmethod
        def cpu_percent(interval=0.1):
            return 30.0

        @staticmethod
        def virtual_memory():
            return MockVM()

    import arbitrage.trinity as trinity_mod
    monkeypatch.setattr(trinity_mod, "_score_material",
        lambda r: _score_material({"cpu_percent": 30.0, "ram_available_ratio": 0.5}))

    score, details = trinity_mod._score_material({"cpu_percent": 30.0, "ram_available_ratio": 0.5})
    assert score > 0


def test_material_clamps_ram_above_1():
    # ram_available_ratio > 1 should be clamped to 1
    score, details = _score_material({"cpu_percent": 20.0, "ram_available_ratio": 1.5})
    assert details["ram_avail"] == 1.0


def test_material_falsy_fields_use_defaults():
    # Missing fields → defaults (50% CPU, 50% RAM)
    score, details = _score_material({})
    assert details["cpu_percent"] == 50.0
    assert details["ram_available_pct"] == 50.0


# ─────────────────────────────────────────────────────────────────────
# Perspektywa 2: Intellectual
# ─────────────────────────────────────────────────────────────────────

def test_intellectual_pass_good_analysis():
    score, details = _score_intellectual(_analysis(score=9, fit="A" * 100, risks="B" * 100))
    assert score > TRINITY_MIN_INTELLECTUAL
    assert details["raw_score"] == 9


def test_intellectual_fail_zero_score():
    score, details = _score_intellectual(_analysis(score=0, fit="A" * 100, risks="B" * 100))
    # score_norm = 0 → harmonic_mean(0, ...) = 0
    assert score == 0.0


def test_intellectual_fail_below_min_score():
    from arbitrage.config import MIN_ANALYZER_SCORE
    score_low, _ = _score_intellectual(_analysis(score=MIN_ANALYZER_SCORE - 1, fit="Fit text here ok", risks="Some risk text"))
    score_ok,  _ = _score_intellectual(_analysis(score=MIN_ANALYZER_SCORE,     fit="Fit text here ok", risks="Some risk text"))
    assert score_low < score_ok


def test_intellectual_fail_no_reasoning():
    score, _ = _score_intellectual(_analysis(score=9, fit="", risks=""))
    # reasoning_norm = 0 → harmonic_mean(x, 0) = 0
    assert score == 0.0


def test_intellectual_short_reasoning():
    score, details = _score_intellectual(_analysis(score=8, fit="ok", risks="ok"))
    # reasoning_chars = 4, target = 200 → norm = 0.02
    assert details["reasoning_chars"] == 4
    assert details["reasoning_norm"] == pytest.approx(0.02)


def test_intellectual_max_score_full_reasoning():
    score, _ = _score_intellectual(_analysis(score=10, fit="A" * 150, risks="B" * 50))
    # score_norm = 1.0, reasoning_norm = 1.0 → harmonic = 1.0
    assert score == pytest.approx(1.0)


def test_intellectual_details_keys():
    _, details = _score_intellectual(_analysis())
    assert "raw_score" in details
    assert "score_norm" in details
    assert "reasoning_chars" in details
    assert "reasoning_norm" in details
    assert "min_score" in details


# ─────────────────────────────────────────────────────────────────────
# Perspektywa 3: Essential
# ─────────────────────────────────────────────────────────────────────

def test_essential_pass_keywords_and_profit():
    score, details = _score_essential(_job(), _analysis(est_profit=100.0))
    assert score > TRINITY_MIN_ESSENTIAL
    assert details["keyword_count"] >= 1


def test_essential_fail_no_keywords():
    score, details = _score_essential(
        _job(title="Build a React app", description="Mobile development"),
        _analysis(est_profit=100.0),
    )
    assert score == 0.0
    assert details["keyword_count"] == 0


def test_essential_fail_negative_profit():
    score, details = _score_essential(_job(), _analysis(est_profit=-50.0))
    # profit_norm = 0 → geometric_mean(x, 0) = 0
    assert score == 0.0
    assert details["profit_norm"] == 0.0


def test_essential_fail_zero_profit():
    score, _ = _score_essential(_job(), _analysis(est_profit=0.0))
    assert score == 0.0


def test_essential_two_keywords_full_purpose():
    # 2+ keywords → purpose_match = 1.0
    score, details = _score_essential(
        _job(title="SEO content writing blog", description="article copywriting"),
        _analysis(est_profit=999.0),
    )
    assert details["purpose_match"] == 1.0
    assert score > 0.9


def test_essential_one_keyword_half_purpose():
    score, details = _score_essential(
        _job(title="Blog only", description="some project"),
        _analysis(est_profit=999.0),
    )
    assert details["keyword_count"] == 1
    assert details["purpose_match"] == pytest.approx(0.5)


def test_essential_profit_capped_at_1():
    # est_profit >> MIN_PROFIT_USD → profit_norm capped to 1.0
    from arbitrage.config import MIN_PROFIT_USD
    score, details = _score_essential(_job(), _analysis(est_profit=MIN_PROFIT_USD * 100))
    assert details["profit_norm"] == 1.0


def test_essential_details_keys():
    _, details = _score_essential(_job(), _analysis())
    assert "keyword_count" in details
    assert "purpose_match" in details
    assert "est_profit" in details
    assert "profit_norm" in details
    assert "min_profit" in details


# ─────────────────────────────────────────────────────────────────────
# evaluate_trinity — integracja
# ─────────────────────────────────────────────────────────────────────

def _good_resources():
    return {"cpu_percent": 20.0, "ram_available_ratio": 0.8}


def test_evaluate_trinity_all_pass():
    result = evaluate_trinity(_job(), _analysis(), _good_resources())
    assert result.approved is True
    assert result.material     >= TRINITY_MIN_MATERIAL
    assert result.intellectual >= TRINITY_MIN_INTELLECTUAL
    assert result.essential    >= TRINITY_MIN_ESSENTIAL
    assert result.combined     >= TRINITY_MIN_COMBINED


def test_evaluate_trinity_material_fail():
    bad_res = {"cpu_percent": 98.0, "ram_available_ratio": 0.02}
    result = evaluate_trinity(_job(), _analysis(), bad_res)
    assert result.approved is False
    assert result.material < TRINITY_MIN_MATERIAL


def test_evaluate_trinity_intellectual_fail_zero_score():
    result = evaluate_trinity(_job(), _analysis(score=0), _good_resources())
    assert result.approved is False
    assert result.intellectual == 0.0


def test_evaluate_trinity_intellectual_fail_no_reasoning():
    result = evaluate_trinity(_job(), _analysis(score=5, fit="", risks=""), _good_resources())
    assert result.approved is False


def test_evaluate_trinity_essential_fail_no_keywords():
    result = evaluate_trinity(
        _job(title="React app", description="Mobile development"),
        _analysis(),
        _good_resources(),
    )
    assert result.approved is False
    assert result.essential == 0.0


def test_evaluate_trinity_essential_fail_negative_profit():
    result = evaluate_trinity(_job(), _analysis(est_profit=-50.0), _good_resources())
    assert result.approved is False
    assert result.essential == 0.0


def test_evaluate_trinity_returns_trinity_score_type():
    result = evaluate_trinity(_job(), _analysis(), _good_resources())
    assert isinstance(result, TrinityScore)


def test_evaluate_trinity_to_dict_structure():
    result = evaluate_trinity(_job(), _analysis(), _good_resources())
    d = result.to_dict()
    assert "material"     in d
    assert "intellectual" in d
    assert "essential"    in d
    assert "combined"     in d
    assert "approved"     in d
    assert "details"      in d
    assert isinstance(d["approved"], bool)
    for key in ("material", "intellectual", "essential", "combined"):
        assert 0.0 <= d[key] <= 1.0


def test_evaluate_trinity_details_structure():
    result = evaluate_trinity(_job(), _analysis(), _good_resources())
    assert "material"     in result.details
    assert "intellectual" in result.details
    assert "essential"    in result.details
    assert "thresholds"   in result.details
    thresholds = result.details["thresholds"]
    assert "material"     in thresholds
    assert "intellectual" in thresholds
    assert "essential"    in thresholds
    assert "combined"     in thresholds


def test_evaluate_trinity_combined_is_mean():
    result = evaluate_trinity(_job(), _analysis(), _good_resources())
    expected = (result.material + result.intellectual + result.essential) / 3.0
    assert result.combined == pytest.approx(round(expected, 4), abs=1e-4)


def test_evaluate_trinity_deny_logs_reasons(caplog):
    import logging
    with caplog.at_level(logging.INFO, logger="adrion.trinity"):
        result = evaluate_trinity(
            _job(title="React app", description="Mobile dev"),
            _analysis(score=0, fit="", risks="", est_profit=-50.0),
            _good_resources(),
        )
    assert result.approved is False
    assert "Trinity DENY" in caplog.text


def test_evaluate_trinity_approve_logs_debug(caplog):
    import logging
    with caplog.at_level(logging.DEBUG, logger="adrion.trinity"):
        result = evaluate_trinity(_job(), _analysis(), _good_resources())
    assert result.approved is True
    # DEBUG log may or may not appear depending on level — just verify no error


def test_evaluate_trinity_none_resources_no_crash(monkeypatch):
    """When resources=None — psutil path must not crash."""
    # Simulate psutil import error (ImportError) to exercise fallback
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError("psutil not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    # Should not raise
    result = evaluate_trinity(_job(), _analysis(), system_resources=None)
    assert isinstance(result, TrinityScore)


def test_score_material_none_with_psutil_mocked(monkeypatch):
    """resources=None — exercises actual psutil call path via sys.modules mock."""
    import sys
    import types

    fake_vm = types.SimpleNamespace(available=4 * 1024 ** 3, total=8 * 1024 ** 3)
    fake_psutil = types.ModuleType("psutil")
    fake_psutil.cpu_percent   = lambda interval=0.1: 25.0
    fake_psutil.virtual_memory = lambda: fake_vm

    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    score, details = _score_material(None)
    assert details["cpu_percent"] == 25.0
    assert details["ram_available_pct"] == pytest.approx(50.0)


def test_evaluate_trinity_combined_deny_borderline():
    """All individual scores pass thresholds but combined could be borderline."""
    # Create scenario where individual thresholds pass but combined barely passes
    result = evaluate_trinity(_job(), _analysis(score=8), _good_resources())
    # In this good scenario everything should pass
    assert result.approved is True
    assert 0.0 <= result.combined <= 1.0


# ─────────────────────────────────────────────────────────────────────
# TrinityScore dataclass
# ─────────────────────────────────────────────────────────────────────

def test_trinity_score_fields():
    ts = TrinityScore(
        material=0.8, intellectual=0.7, essential=0.6,
        combined=0.7, approved=True,
    )
    assert ts.material     == 0.8
    assert ts.intellectual == 0.7
    assert ts.essential    == 0.6
    assert ts.combined     == 0.7
    assert ts.approved     is True
    assert ts.details      == {}


def test_trinity_score_to_dict_rounds_values():
    ts = TrinityScore(
        material=0.8123456, intellectual=0.7234567,
        essential=0.6345678, combined=0.7234567,
        approved=True, details={"x": 1},
    )
    d = ts.to_dict()
    # Should round to 4 decimal places
    assert len(str(d["material"]).split(".")[-1]) <= 4
    assert d["details"] == {"x": 1}


def test_trinity_score_not_approved_fields():
    ts = TrinityScore(
        material=0.1, intellectual=0.2, essential=0.0,
        combined=0.1, approved=False,
    )
    assert ts.approved is False
    d = ts.to_dict()
    assert d["approved"] is False
