"""
Property-based tests for Trinity Score engine using Hypothesis.

Tests invariants:
  - scores always in [0.0, 1.0]
  - combined = mean(material, intellectual, essential)
  - approved=True requires all thresholds met
  - to_dict produces serialisable output
"""
import math

import hypothesis.strategies as st
from hypothesis import given, settings

from arbitrage.trinity import (
    TrinityScore,
    evaluate_trinity,
    _harmonic_mean,
    _geometric_mean,
    _clamp,
    _score_material,
    _score_intellectual,
    _score_essential,
    TRINITY_MIN_MATERIAL,
    TRINITY_MIN_INTELLECTUAL,
    TRINITY_MIN_ESSENTIAL,
    TRINITY_MIN_COMBINED,
)


# ── Strategies ───────────────────────────────────────────────────────────────

job_strategy = st.fixed_dictionaries({
    "title": st.text(min_size=0, max_size=200),
    "description": st.text(min_size=0, max_size=500),
    "budget_min": st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False),
    "budget_max": st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False),
})

analysis_strategy = st.fixed_dictionaries({
    "score": st.floats(min_value=0, max_value=10, allow_nan=False, allow_infinity=False),
    "fit": st.text(min_size=0, max_size=300),
    "risks": st.text(min_size=0, max_size=300),
    "est_profit": st.floats(min_value=-100, max_value=10000, allow_nan=False, allow_infinity=False),
})

resources_strategy = st.fixed_dictionaries({
    "cpu_percent": st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    "ram_available_ratio": st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
})


# ── Helper function invariants ───────────────────────────────────────────────

@given(a=st.floats(min_value=0, max_value=1, allow_nan=False),
       b=st.floats(min_value=0, max_value=1, allow_nan=False))
@settings(max_examples=200, deadline=1000)
def test_harmonic_mean_in_range(a, b):
    result = _harmonic_mean(a, b)
    assert 0.0 <= result <= 1.0


@given(a=st.floats(min_value=0, max_value=1, allow_nan=False),
       b=st.floats(min_value=0, max_value=1, allow_nan=False))
@settings(max_examples=200, deadline=1000)
def test_geometric_mean_in_range(a, b):
    result = _geometric_mean(a, b)
    assert 0.0 <= result <= 1.0


@given(v=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False))
@settings(max_examples=200, deadline=1000)
def test_clamp_always_in_bounds(v):
    result = _clamp(v)
    assert 0.0 <= result <= 1.0


# ── Material score invariants ────────────────────────────────────────────────

@given(resources=resources_strategy)
@settings(max_examples=200, deadline=2000)
def test_material_score_in_range(resources):
    score, details = _score_material(resources)
    assert 0.0 <= score <= 1.0
    assert "cpu_percent" in details
    assert "ram_available_pct" in details


# ── Intellectual score invariants ────────────────────────────────────────────

@given(analysis=analysis_strategy)
@settings(max_examples=200, deadline=2000)
def test_intellectual_score_in_range(analysis):
    score, details = _score_intellectual(analysis)
    assert 0.0 <= score <= 1.0
    assert "raw_score" in details


# ── Essential score invariants ───────────────────────────────────────────────

@given(job=job_strategy, analysis=analysis_strategy)
@settings(max_examples=200, deadline=2000)
def test_essential_score_in_range(job, analysis):
    score, details = _score_essential(job, analysis)
    assert 0.0 <= score <= 1.0
    assert "keyword_count" in details
    assert "profit_norm" in details


# ── Full Trinity evaluation invariants ───────────────────────────────────────

@given(job=job_strategy, analysis=analysis_strategy, resources=resources_strategy)
@settings(max_examples=200, deadline=2000)
def test_trinity_scores_in_range(job, analysis, resources):
    result = evaluate_trinity(job, analysis, resources)

    assert 0.0 <= result.material <= 1.0
    assert 0.0 <= result.intellectual <= 1.0
    assert 0.0 <= result.essential <= 1.0
    assert 0.0 <= result.combined <= 1.0


@given(job=job_strategy, analysis=analysis_strategy, resources=resources_strategy)
@settings(max_examples=200, deadline=2000)
def test_combined_is_mean(job, analysis, resources):
    result = evaluate_trinity(job, analysis, resources)
    expected = round((result.material + result.intellectual + result.essential) / 3.0, 4)
    assert abs(result.combined - expected) < 0.001


@given(job=job_strategy, analysis=analysis_strategy, resources=resources_strategy)
@settings(max_examples=200, deadline=2000)
def test_approved_implies_all_thresholds_met(job, analysis, resources):
    result = evaluate_trinity(job, analysis, resources)

    if result.approved:
        assert result.material >= TRINITY_MIN_MATERIAL
        assert result.intellectual >= TRINITY_MIN_INTELLECTUAL
        assert result.essential >= TRINITY_MIN_ESSENTIAL
        assert result.combined >= TRINITY_MIN_COMBINED


@given(job=job_strategy, analysis=analysis_strategy, resources=resources_strategy)
@settings(max_examples=200, deadline=2000)
def test_denied_if_any_threshold_failed(job, analysis, resources):
    result = evaluate_trinity(job, analysis, resources)

    any_below = (
        result.material < TRINITY_MIN_MATERIAL
        or result.intellectual < TRINITY_MIN_INTELLECTUAL
        or result.essential < TRINITY_MIN_ESSENTIAL
        or result.combined < TRINITY_MIN_COMBINED
    )

    if any_below:
        assert result.approved is False


@given(job=job_strategy, analysis=analysis_strategy, resources=resources_strategy)
@settings(max_examples=50, deadline=2000)
def test_to_dict_structure(job, analysis, resources):
    result = evaluate_trinity(job, analysis, resources)
    d = result.to_dict()

    assert isinstance(d, dict)
    for key in ("material", "intellectual", "essential", "combined", "approved", "details"):
        assert key in d
    assert isinstance(d["details"], dict)
    assert "thresholds" in d["details"]
