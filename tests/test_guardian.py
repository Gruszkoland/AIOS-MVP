"""
Unit tests for arbitrage/guardian.py — 9 Guardian Laws Engine.
No external deps — pure logic testing.
"""
from arbitrage.guardian import (
    GuardianEval,
    LawResult,
    _law_autonomy,
    _law_causality,
    _law_justice,
    _law_nonmaleficence,
    _law_rhythm,
    _law_sustainability,
    _law_transparency,
    _law_truth,
    _law_unity,
    build_context,
    evaluate_guardians,
)

# ─────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────

def _job(
    title="Blog post about SEO content writing",
    platform="upwork",
    budget_min=100,
    budget_max=300,
    description="We need a skilled content writer for blog articles.",
    client="Acme Corp",
):
    return {
        "title": title,
        "platform": platform,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "description": description,
        "client": client,
    }


def _analysis(
    score=8,
    fit="Excellent match for our content writing portfolio",
    risks="Client is new, no reviews yet",
    our_price=250.0,
    est_cost=1.5,
    est_profit=248.5,
    llm_backend="mock",
):
    return {
        "score": score,
        "fit": fit,
        "risks": risks,
        "our_price": our_price,
        "est_cost": est_cost,
        "est_profit": est_profit,
        "llm_backend": llm_backend,
    }


def _ctx(
    bids_today=5,
    daily_est_cost=8.0,
    bids_for_client_today=0,
    daily_bid_limit=20,
    max_daily_cost=25.0,
    max_bids_per_client=1,
    max_est_cost_per_bid=2.5,
):
    return build_context(
        bids_today=bids_today,
        daily_est_cost=daily_est_cost,
        bids_for_client_today=bids_for_client_today,
        daily_bid_limit=daily_bid_limit,
        max_daily_cost=max_daily_cost,
        max_bids_per_client=max_bids_per_client,
        max_est_cost_per_bid=max_est_cost_per_bid,
    )


# ─────────────────────────────────────────────────────────────
# Law 1: Unity
# ─────────────────────────────────────────────────────────────

def test_unity_pass_keyword_in_title():
    r = _law_unity(_job(title="SEO content writing for tech blog"))
    assert r.passed is True
    assert r.name == "Unity"
    assert r.weight == "MEDIUM"


def test_unity_pass_keyword_in_description():
    r = _law_unity(_job(title="Web project", description="Need a copywriting expert for landing page"))
    assert r.passed is True


def test_unity_fail_unrelated_job():
    r = _law_unity(_job(title="Build a mobile app", description="React Native development"))
    assert r.passed is False
    assert "scope" in r.reason.lower() or "unclear" in r.reason.lower()


def test_unity_fail_empty_job():
    r = _law_unity({"title": "", "description": ""})
    assert r.passed is False


def test_unity_pass_ghostwriting():
    r = _law_unity(_job(title="Ghostwriting service needed"))
    assert r.passed is True


# ─────────────────────────────────────────────────────────────
# Law 2: Truth
# ─────────────────────────────────────────────────────────────

def test_truth_pass():
    r = _law_truth(_analysis(score=7, fit="Great match", risks="Some risk"))
    assert r.passed is True
    assert "7" in r.reason


def test_truth_fail_zero_score():
    r = _law_truth(_analysis(score=0))
    assert r.passed is False
    assert "0" in r.reason


def test_truth_fail_negative_score():
    r = _law_truth(_analysis(score=-1))
    assert r.passed is False


def test_truth_fail_missing_fit():
    r = _law_truth(_analysis(score=8, fit="", risks="some risks here"))
    assert r.passed is False
    assert "reasoning" in r.reason.lower() or "short" in r.reason.lower()


def test_truth_fail_missing_risks():
    r = _law_truth(_analysis(score=8, fit="good fit", risks=""))
    assert r.passed is False


def test_truth_fail_both_empty():
    r = _law_truth(_analysis(score=5, fit="", risks=""))
    assert r.passed is False


def test_truth_pass_score_10():
    r = _law_truth(_analysis(score=10, fit="Perfect match for us", risks="No major risks"))
    assert r.passed is True


# ─────────────────────────────────────────────────────────────
# Law 3: Rhythm
# ─────────────────────────────────────────────────────────────

def test_rhythm_pass_normal():
    r = _law_rhythm(_ctx(bids_today=5, daily_bid_limit=20))
    assert r.passed is True
    assert "5/20" in r.reason


def test_rhythm_fail_limit_reached():
    r = _law_rhythm(_ctx(bids_today=20, daily_bid_limit=20))
    assert r.passed is False
    assert "limit reached" in r.reason.lower() or "20/20" in r.reason


def test_rhythm_fail_over_limit():
    r = _law_rhythm(_ctx(bids_today=25, daily_bid_limit=20))
    assert r.passed is False


def test_rhythm_pass_zero_bids():
    r = _law_rhythm(_ctx(bids_today=0, daily_bid_limit=20))
    assert r.passed is True


def test_rhythm_pass_no_limit_configured():
    r = _law_rhythm({"daily_bid_limit": 0})
    assert r.passed is True


def test_rhythm_pass_at_80_percent(caplog):
    import logging
    with caplog.at_level(logging.WARNING, logger="adrion.guardian"):
        r = _law_rhythm(_ctx(bids_today=16, daily_bid_limit=20))
    assert r.passed is True
    assert "80%" in caplog.text or "Guardian Rhythm" in caplog.text


# ─────────────────────────────────────────────────────────────
# Law 4: Causality
# ─────────────────────────────────────────────────────────────

def test_causality_pass():
    r = _law_causality(_analysis(our_price=250, est_profit=248.5), _job(budget_min=100, budget_max=300))
    assert r.passed is True


def test_causality_fail_zero_price():
    r = _law_causality(_analysis(our_price=0), _job())
    assert r.passed is False
    assert "zero" in r.reason.lower() or "pricing" in r.reason.lower()


def test_causality_fail_negative_price():
    r = _law_causality(_analysis(our_price=-50), _job())
    assert r.passed is False


def test_causality_fail_price_over_budget():
    r = _law_causality(_analysis(our_price=400), _job(budget_max=300))
    assert r.passed is False
    assert "budget_max" in r.reason or "exceed" in r.reason.lower()


def test_causality_pass_price_at_10pct_over_budget():
    # 10% tolerance — 330 should pass when budget_max=300
    r = _law_causality(_analysis(our_price=330), _job(budget_max=300))
    assert r.passed is True


def test_causality_fail_negative_profit():
    r = _law_causality(_analysis(our_price=100, est_profit=-50), _job())
    assert r.passed is False
    assert "negative" in r.reason.lower()


def test_causality_pass_no_budget_max():
    r = _law_causality(_analysis(our_price=999), _job(budget_max=0))
    assert r.passed is True


# ─────────────────────────────────────────────────────────────
# Law 5: Transparency
# ─────────────────────────────────────────────────────────────

def test_transparency_pass():
    r = _law_transparency(_analysis())
    assert r.passed is True
    assert "backend=mock" in r.reason


def test_transparency_fail_missing_score():
    a = _analysis()
    del a["score"]
    r = _law_transparency(a)
    assert r.passed is False
    assert "score" in r.reason


def test_transparency_fail_missing_our_price():
    a = _analysis()
    del a["our_price"]
    r = _law_transparency(a)
    assert r.passed is False


def test_transparency_fail_none_field():
    a = _analysis()
    a["est_cost"] = None
    r = _law_transparency(a)
    assert r.passed is False
    assert "est_cost" in r.reason


def test_transparency_fail_multiple_missing():
    r = _law_transparency({})
    assert r.passed is False


# ─────────────────────────────────────────────────────────────
# Law 6: Nonmaleficence (CRITICAL)
# ─────────────────────────────────────────────────────────────

def test_nonmaleficence_pass():
    r = _law_nonmaleficence(_analysis(est_cost=1.5, est_profit=100.0))
    assert r.passed is True
    assert r.weight == "CRITICAL"


def test_nonmaleficence_fail_cost_over_limit():
    r = _law_nonmaleficence(_analysis(est_cost=5.0, est_profit=50.0))
    assert r.passed is False
    assert r.weight == "CRITICAL"
    assert "2.5" in r.reason or "limit" in r.reason.lower()


def test_nonmaleficence_fail_significant_negative_profit():
    # -5 when MIN_PROFIT_USD=30 → -5 < -(30*0.1) = -3 → fail
    r = _law_nonmaleficence(_analysis(est_cost=1.0, est_profit=-5.0))
    assert r.passed is False
    assert r.weight == "CRITICAL"


def test_nonmaleficence_pass_small_negative_profit():
    # -2 when MIN_PROFIT_USD=30 → -2 > -3 → pass
    r = _law_nonmaleficence(_analysis(est_cost=1.0, est_profit=-2.0))
    assert r.passed is True


def test_nonmaleficence_pass_zero_cost():
    r = _law_nonmaleficence(_analysis(est_cost=0.0, est_profit=200.0))
    assert r.passed is True


# ─────────────────────────────────────────────────────────────
# Law 7: Autonomy
# ─────────────────────────────────────────────────────────────

def test_autonomy_pass_first_bid_for_client():
    r = _law_autonomy(_job(client="Acme"), _ctx(bids_for_client_today=0))
    assert r.passed is True
    assert "Acme" in r.reason


def test_autonomy_fail_client_at_limit():
    r = _law_autonomy(_job(client="Acme"), _ctx(bids_for_client_today=1, max_bids_per_client=1))
    assert r.passed is False
    assert "Acme" in r.reason
    assert "1/1" in r.reason


def test_autonomy_pass_anonymous_client():
    r = _law_autonomy(_job(client=""), _ctx(bids_for_client_today=10))
    assert r.passed is True
    assert "anonymous" in r.reason.lower()


def test_autonomy_pass_none_client():
    r = _law_autonomy({"client": None}, _ctx(bids_for_client_today=10))
    assert r.passed is True


def test_autonomy_fail_over_limit():
    r = _law_autonomy(_job(client="SpamTarget"), _ctx(bids_for_client_today=5, max_bids_per_client=1))
    assert r.passed is False


# ─────────────────────────────────────────────────────────────
# Law 8: Justice
# ─────────────────────────────────────────────────────────────

def test_justice_pass_normal_budget():
    r = _law_justice(_job(budget_min=100, budget_max=300))
    assert r.passed is True


def test_justice_fail_budget_too_low():
    r = _law_justice(_job(budget_min=10, budget_max=30))
    assert r.passed is False
    assert "minimum" in r.reason.lower() or "below" in r.reason.lower()


def test_justice_fail_budget_insanely_high():
    r = _law_justice(_job(budget_min=0, budget_max=1_000_000))
    assert r.passed is False
    assert "sanity" in r.reason.lower() or "cap" in r.reason.lower()


def test_justice_pass_at_min_boundary():
    # SCOUT_MIN_BUDGET = 50 — exactly at limit
    from arbitrage.config import SCOUT_MIN_BUDGET
    r = _law_justice(_job(budget_min=SCOUT_MIN_BUDGET, budget_max=SCOUT_MIN_BUDGET + 50))
    assert r.passed is True


def test_justice_pass_high_but_reasonable():
    r = _law_justice(_job(budget_min=400, budget_max=500))
    assert r.passed is True


# ─────────────────────────────────────────────────────────────
# Law 9: Sustainability
# ─────────────────────────────────────────────────────────────

def test_sustainability_pass():
    r = _law_sustainability(_ctx(daily_est_cost=10.0, max_daily_cost=25.0))
    assert r.passed is True
    assert "15.00 remaining" in r.reason


def test_sustainability_fail_at_limit():
    r = _law_sustainability(_ctx(daily_est_cost=25.0, max_daily_cost=25.0))
    assert r.passed is False
    assert "reached" in r.reason.lower() or "25.00" in r.reason


def test_sustainability_fail_over_limit():
    r = _law_sustainability(_ctx(daily_est_cost=30.0, max_daily_cost=25.0))
    assert r.passed is False


def test_sustainability_pass_zero_cost():
    r = _law_sustainability(_ctx(daily_est_cost=0.0, max_daily_cost=25.0))
    assert r.passed is True
    assert "$0.00" in r.reason or "0.00" in r.reason


# ─────────────────────────────────────────────────────────────
# evaluate_guardians — integration
# ─────────────────────────────────────────────────────────────

def test_evaluate_guardians_all_pass():
    result = evaluate_guardians(_job(), _analysis(), _ctx())
    assert result.approved is True
    assert result.compliance == 9
    assert result.violations == 0
    assert result.denial_reason == ""
    assert len(result.laws) == 9


def test_evaluate_guardians_critical_deny():
    """Nonmaleficence violation → CRITICAL DENY even with 0 other violations."""
    bad_analysis = _analysis(est_cost=10.0, est_profit=50.0)  # cost > 2.5 limit
    result = evaluate_guardians(_job(), bad_analysis, _ctx())
    assert result.approved is False
    assert "CRITICAL" in result.denial_reason
    assert "Nonmaleficence" in result.denial_reason


def test_evaluate_guardians_two_violations_deny():
    """CRITICAL violation (Justice) + MEDIUM violation (Unity) → instant DENY.

    Justice is CRITICAL — single CRITICAL triggers deny regardless of Unity.
    """
    bad_job = _job(
        title="Build a mobile app",            # Law 1 Unity: FAIL (MEDIUM)
        description="React Native development", # no content keywords
        budget_min=10, budget_max=30,           # Law 8 Justice: FAIL (CRITICAL)
    )
    result = evaluate_guardians(bad_job, _analysis(), _ctx())
    assert result.approved is False
    assert result.violations >= 2
    assert "Unity" in result.denial_reason or "Justice" in result.denial_reason


def test_evaluate_guardians_one_violation_approve():
    """One non-critical violation → still APPROVE."""
    # Unity fails: no content keywords in title or description
    bad_job = _job(title="Build a mobile app", description="React Native development task")
    result = evaluate_guardians(bad_job, _analysis(), _ctx())
    assert result.approved is True
    assert result.violations == 1


def test_evaluate_guardians_two_medium_violations_approve():
    """Two MEDIUM violations (weight=1+1=2) are below threshold=4 → APPROVE.

    This validates the weighted system: low-severity edge cases should not
    block legitimate bids that pass all financial/critical checks.
    """
    bad_job = _job(title="Build a mobile app", description="React Native development")
    ctx = _ctx(bids_today=20, daily_bid_limit=20)  # Rhythm MEDIUM: FAIL
    # Unity MEDIUM (no keywords) + Rhythm MEDIUM (limit reached) = weight 2 < 4
    result = evaluate_guardians(bad_job, _analysis(), ctx)
    # With weighted system: 2 MEDIUM violations = weight 2 < threshold 4 → APPROVE
    assert result.violations >= 2
    # Rhythm + Unity both fail but combined weight < DENY_WEIGHTED_THRESHOLD
    assert result.approved is True


def test_evaluate_guardians_two_high_violations_deny():
    """Two HIGH violations (weight=2+2=4) reach threshold → DENY."""
    bad_job = _job(title="Build a mobile app", description="React Native development")
    # Sustainability HIGH fails + Truth HIGH fails
    ctx = _ctx(daily_est_cost=25.0, max_daily_cost=25.0)  # Sustainability HIGH: FAIL
    bad_analysis = _analysis(score=0)  # Truth HIGH: FAIL (score=0)
    result = evaluate_guardians(bad_job, bad_analysis, ctx)
    assert result.approved is False
    assert result.violations >= 2


def test_evaluate_guardians_rhythm_single_medium_approve():
    """Single Rhythm (MEDIUM) violation alone → APPROVE (weight=1 < 4)."""
    ctx = _ctx(bids_today=20, daily_bid_limit=20)  # Rhythm MEDIUM: FAIL
    result = evaluate_guardians(_job(), _analysis(), ctx)  # good job, all else passes
    assert result.approved is True
    assert result.violations == 1


def test_evaluate_guardians_sustainability_high_plus_medium_approve():
    """Sustainability (HIGH=2) + Unity (MEDIUM=1) = weight 3 < 4 → APPROVE."""
    bad_job = _job(title="React Native mobile app", description="Mobile development project")
    ctx = _ctx(daily_est_cost=25.0, max_daily_cost=25.0)  # Sustainability HIGH: FAIL
    result = evaluate_guardians(bad_job, _analysis(), ctx)
    # Unity(1) + Sustainability(2) = 3 < 4 → APPROVE
    assert result.approved is True
    assert result.violations >= 2


def test_evaluate_guardians_sustainability_deny():
    """Sustainability (HIGH) + Truth (HIGH) → weight 4 = threshold → DENY."""
    bad_job = _job(title="Build a React Native app", description="Mobile development project")
    ctx = _ctx(daily_est_cost=25.0, max_daily_cost=25.0)  # Sustainability HIGH: FAIL
    bad_analysis = _analysis(score=0)  # Truth HIGH: FAIL
    result = evaluate_guardians(bad_job, bad_analysis, ctx)
    assert result.approved is False


def test_evaluate_guardians_returns_9_laws():
    result = evaluate_guardians(_job(), _analysis(), _ctx())
    assert len(result.laws) == 9
    names = [law.name for law in result.laws]
    assert names == [
        "Unity", "Truth", "Rhythm", "Causality", "Transparency",
        "Nonmaleficence", "Autonomy", "Justice", "Sustainability",
    ]


def test_evaluate_guardians_to_dict():
    result = evaluate_guardians(_job(), _analysis(), _ctx())
    d = result.to_dict()
    assert "laws" in d
    assert "compliance" in d
    assert "violations" in d
    assert "approved" in d
    assert "denial_reason" in d
    assert len(d["laws"]) == 9
    for law in d["laws"]:
        assert "name" in law
        assert "passed" in law
        assert "reason" in law
        assert "weight" in law



# ─────────────────────────────────────────────────────────────
# build_context
# ─────────────────────────────────────────────────────────────

def test_build_context_defaults():
    ctx = build_context()
    assert ctx["bids_today"] == 0
    assert ctx["daily_est_cost"] == 0.0
    assert ctx["bids_for_client_today"] == 0
    assert ctx["daily_bid_limit"] > 0
    assert ctx["max_daily_cost"] > 0


def test_build_context_custom_values():
    ctx = build_context(bids_today=5, daily_est_cost=12.5)
    assert ctx["bids_today"] == 5
    assert ctx["daily_est_cost"] == 12.5


# ─────────────────────────────────────────────────────────────
# LawResult and GuardianEval dataclass sanity
# ─────────────────────────────────────────────────────────────

def test_law_result_fields():
    r = LawResult("Test", True, "reason", "HIGH")
    assert r.name == "Test"
    assert r.passed is True
    assert r.weight == "HIGH"


def test_guardian_eval_to_dict_structure():
    laws = [LawResult(f"Law{i}", True, "ok", "MEDIUM") for i in range(9)]
    g = GuardianEval(laws, 9, 0, True, "")
    d = g.to_dict()
    assert d["compliance"] == 9
    assert d["violations"] == 0
    assert d["approved"] is True
    assert len(d["laws"]) == 9
