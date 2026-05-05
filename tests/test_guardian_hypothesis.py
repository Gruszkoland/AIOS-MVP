"""
Property-based tests for Guardian Laws engine using Hypothesis.

Tests invariants that must hold for ANY input:
  - CRITICAL violation → always DENY
  - ≥2 violations → always DENY
  - scores always in valid range
  - evaluate_guardians returns correct structure
"""
import hypothesis.strategies as st
from hypothesis import given, settings, assume

from arbitrage.guardian import (
    GuardianEval,
    LawResult,
    evaluate_guardians,
    build_context,
    DENY_THRESHOLD,
    _law_unity,
    _law_truth,
    _law_rhythm,
    _law_causality,
    _law_transparency,
    _law_nonmaleficence,
    _law_autonomy,
    _law_justice,
    _law_sustainability,
)


# ── Strategies ───────────────────────────────────────────────────────────────

job_strategy = st.fixed_dictionaries({
    "id": st.text(min_size=1, max_size=20),
    "title": st.text(min_size=0, max_size=200),
    "description": st.text(min_size=0, max_size=500),
    "platform": st.sampled_from(["upwork", "fiverr", "freelancer", ""]),
    "budget_min": st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False),
    "budget_max": st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False),
    "client": st.text(min_size=0, max_size=50),
})

analysis_strategy = st.fixed_dictionaries({
    "score": st.floats(min_value=-10, max_value=100, allow_nan=False, allow_infinity=False),
    "fit": st.text(min_size=0, max_size=300),
    "risks": st.text(min_size=0, max_size=300),
    "our_price": st.floats(min_value=-100, max_value=10000, allow_nan=False, allow_infinity=False),
    "est_cost": st.floats(min_value=-100, max_value=10000, allow_nan=False, allow_infinity=False),
    "est_profit": st.floats(min_value=-1000, max_value=10000, allow_nan=False, allow_infinity=False),
    "llm_backend": st.sampled_from(["ollama", "openrouter", "mock", "unknown"]),
})

context_strategy = st.fixed_dictionaries({
    "bids_today": st.integers(min_value=0, max_value=1000),
    "daily_est_cost": st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False),
    "bids_for_client_today": st.integers(min_value=0, max_value=100),
    "daily_bid_limit": st.integers(min_value=1, max_value=100),
    "max_daily_cost": st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
    "max_bids_per_client": st.integers(min_value=1, max_value=50),
    "max_est_cost_per_bid": st.floats(min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False),
})


# ── Invariant: structure is always correct ────────────────────────────────────

@given(job=job_strategy, analysis=analysis_strategy, context=context_strategy)
@settings(max_examples=200, deadline=2000)
def test_evaluate_guardians_returns_valid_structure(job, analysis, context):
    result = evaluate_guardians(job, analysis, context)

    assert isinstance(result, GuardianEval)
    assert isinstance(result.laws, list)
    assert len(result.laws) == 9
    assert isinstance(result.compliance, int)
    assert isinstance(result.violations, int)
    assert isinstance(result.approved, bool)
    assert result.compliance + result.violations == 9
    assert result.compliance >= 0
    assert result.violations >= 0


# ── Invariant: CRITICAL violation → always DENY ──────────────────────────────

@given(job=job_strategy, analysis=analysis_strategy, context=context_strategy)
@settings(max_examples=200, deadline=2000)
def test_critical_violation_always_denies(job, analysis, context):
    result = evaluate_guardians(job, analysis, context)

    critical_violations = [law for law in result.laws if not law.passed and law.weight == "CRITICAL"]

    if critical_violations:
        assert result.approved is False, (
            f"CRITICAL violation present but approved=True: {critical_violations[0].name}"
        )


# ── Invariant: ≥2 violations → always DENY ──────────────────────────────────

@given(job=job_strategy, analysis=analysis_strategy, context=context_strategy)
@settings(max_examples=200, deadline=2000)
def test_multiple_violations_deny(job, analysis, context):
    result = evaluate_guardians(job, analysis, context)

    if result.violations >= DENY_THRESHOLD:
        assert result.approved is False, (
            f"{result.violations} violations but approved=True"
        )


# ── Invariant: approved=True → violations < threshold and no CRITICAL ────────

@given(job=job_strategy, analysis=analysis_strategy, context=context_strategy)
@settings(max_examples=200, deadline=2000)
def test_approved_implies_low_violations(job, analysis, context):
    result = evaluate_guardians(job, analysis, context)

    if result.approved:
        assert result.violations < DENY_THRESHOLD
        critical = [law for law in result.laws if not law.passed and law.weight == "CRITICAL"]
        assert len(critical) == 0


# ── Invariant: each law result has valid weight ──────────────────────────────

@given(job=job_strategy, analysis=analysis_strategy, context=context_strategy)
@settings(max_examples=100, deadline=2000)
def test_all_law_weights_valid(job, analysis, context):
    result = evaluate_guardians(job, analysis, context)

    for law in result.laws:
        assert isinstance(law, LawResult)
        assert law.weight in ("CRITICAL", "HIGH", "MEDIUM")
        assert isinstance(law.passed, bool)
        assert isinstance(law.name, str)
        assert len(law.name) > 0


# ── Invariant: to_dict roundtrip ─────────────────────────────────────────────

@given(job=job_strategy, analysis=analysis_strategy, context=context_strategy)
@settings(max_examples=50, deadline=2000)
def test_to_dict_returns_serialisable(job, analysis, context):
    result = evaluate_guardians(job, analysis, context)
    d = result.to_dict()

    assert isinstance(d, dict)
    assert "laws" in d
    assert "compliance" in d
    assert "violations" in d
    assert "approved" in d
    assert len(d["laws"]) == 9
    for law_dict in d["laws"]:
        assert "name" in law_dict
        assert "passed" in law_dict
        assert "weight" in law_dict
        assert "reason" in law_dict
