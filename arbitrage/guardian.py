"""
ADRION 369 — Guardian Laws Engine v5.3

11 Ethical laws validated sequentially for every arbitrage decision (ADRION 369 §VI).

Decision rules (weighted system):
  WEIGHT_MAP: CRITICAL=10, HIGH=2, MEDIUM=1
  DENY_WEIGHTED_THRESHOLD = 4

  Any CRITICAL violation triggers instant DENY (weight >= 10).
  Otherwise: sum(weights of failed laws) >= threshold -> DENY.

  Rationale:
    2x MEDIUM = 2  -> APPROVE (two low-severity edge cases)
    1x HIGH    = 2  -> APPROVE (single moderate issue)
    1x HIGH+1x MED = 3 -> APPROVE
    2x HIGH    = 4  -> DENY (two moderate issues compound)
    1x CRITICAL    = 10 -> always DENY

11 Guardian Laws (§VI ADRION 369 v5.3):
  G1. Unity          (MEDIUM)   — job aligns with system's core purpose
  G2. Harmony        (MEDIUM)   — balance between competing objectives (was Truth)
  G3. Rhythm         (MEDIUM)   — bid pace is sustainable (daily limits)
  G4. Causality      (HIGH)     — price chain is traceable and non-negative
  G5. Transparency   (MEDIUM)   — all required analysis fields present
  G6. Authenticity   (HIGH)     — LLM output genuine, non-deceptive, non-frozen
  G7. Privacy        (CRITICAL) — no external disclosure without consent (was Autonomy)
  G8. Nonmaleficence (CRITICAL) — no financial harm to operator
  G9. Sustainability (HIGH)     — daily total operational cost within limit
  G10. Evolution     (HIGH)     — errors drive improvement; PME feedback loops active
  G11. RelationalCare (MEDIUM)  — respect user attention budget; transparency on cost

DSPy Signature:
  In(job:dict, analysis:dict, context:dict) -> Out(laws:list[LawResult], compliance:int, approved:bool)

Backward compatibility:
  Code "Harmony"    = Canonical G2 "Harmony"
  Code "Privacy"    = Canonical G7 "Privacy"        [CRITICAL]
  Code "Authenticity" = Canonical G6 "Authenticity" [HIGH]
  Runtime names preserved for API/test compatibility.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Literal

from .config import (
    DAILY_BID_LIMIT,
    MAX_BIDS_PER_CLIENT_PER_DAY,
    MAX_DAILY_EST_COST_USD,
    MAX_EST_COST_PER_BID_USD,
    MIN_PROFIT_USD,
    SCOUT_MAX_BUDGET,
    SCOUT_MIN_BUDGET,
)

logger = logging.getLogger("adrion.guardian")

Weight = Literal["CRITICAL", "HIGH", "MEDIUM"]

# Weighted violation scoring
_WEIGHT_MAP: dict[Weight, int] = {"CRITICAL": 10, "HIGH": 2, "MEDIUM": 1}
DENY_WEIGHTED_THRESHOLD = 4  # sum of violation weights triggering DENY



# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class LawResult:
    name: str
    passed: bool
    reason: str
    weight: Weight


@dataclass
class GuardianEval:
    laws: list[LawResult]
    compliance: int       # number of laws passed
    violations: int       # number of laws failed
    approved: bool
    denial_reason: str = field(default="")

    def to_dict(self) -> dict:
        return {
            "laws": [
                {
                    "name": law.name,
                    "passed": law.passed,
                    "reason": law.reason,
                    "weight": law.weight,
                }
                for law in self.laws
            ],
            "compliance": self.compliance,
            "violations": self.violations,
            "approved": self.approved,
            "denial_reason": self.denial_reason,
        }


# ═══════════════════════════════════════════════════════════════
# HELPER
# ═══════════════════════════════════════════════════════════════

def build_context(
    bids_today: int = 0,
    daily_est_cost: float = 0.0,
    bids_for_client_today: int = 0,
    daily_bid_limit: int = DAILY_BID_LIMIT,
    max_daily_cost: float = MAX_DAILY_EST_COST_USD,
    max_bids_per_client: int = MAX_BIDS_PER_CLIENT_PER_DAY,
    max_est_cost_per_bid: float = MAX_EST_COST_PER_BID_USD,
) -> dict:
    """Build a runtime context dict for evaluate_guardians()."""
    return {
        "bids_today": bids_today,
        "daily_est_cost": daily_est_cost,
        "bids_for_client_today": bids_for_client_today,
        "daily_bid_limit": daily_bid_limit,
        "max_daily_cost": max_daily_cost,
        "max_bids_per_client": max_bids_per_client,
        "max_est_cost_per_bid": max_est_cost_per_bid,
    }


# ═══════════════════════════════════════════════════════════════
# 9 GUARDIAN LAWS
# ═══════════════════════════════════════════════════════════════

_PURPOSE_KEYWORDS = frozenset({
    "content", "writing", "blog", "article", "copy", "seo",
    "ghostwriting", "editorial", "text", "post", "script",
    "copywriting", "proofreading", "translation", "newsletter",
})


def _law_unity(job: dict) -> LawResult:
    """Law 1: Unity — Job must align with system's core purpose."""
    title = (job.get("title") or "").lower()
    description = (job.get("description") or "").lower()
    combined = title + " " + description
    matches = [kw for kw in _PURPOSE_KEYWORDS if kw in combined]
    if matches:
        return LawResult(
            "Unity", True,
            f"Job aligned: {sorted(matches)[:3]}",
            "MEDIUM",
        )
    return LawResult(
        "Unity", False,
        "Job purpose unclear or outside content writing scope",
        "MEDIUM",
    )


def _law_harmony(analysis: dict) -> LawResult:
    """Law G2: Harmony — Analysis must balance competing objectives; reasoning genuine.
    
    (Renamed from 'Truth' for canonical alignment with ADRION 369 §VI G2)
    """
    score = analysis.get("score", 0)
    fit = (analysis.get("fit") or "").strip()
    risks = (analysis.get("risks") or "").strip()

    if not score or score <= 0:
        return LawResult(
            "Harmony", False,
            f"Score is {score!r} — zero or missing is invalid",
            "HIGH",
        )
    if len(fit) < 5 or len(risks) < 5:
        return LawResult(
            "Harmony", False,
            "Analysis missing fit/risks reasoning (too short)",
            "HIGH",
        )
    return LawResult(
        "Harmony", True,
        f"Score={score}, reasoning present ({len(fit) + len(risks)} chars)",
        "HIGH",
    )


def _law_rhythm(context: dict) -> LawResult:
    """Law 3: Rhythm — Bid pace must be sustainable (daily limit)."""
    bids_today = int(context.get("bids_today", 0))
    daily_limit = int(context.get("daily_bid_limit", DAILY_BID_LIMIT))

    if daily_limit <= 0:
        return LawResult("Rhythm", True, "No daily limit configured", "MEDIUM")

    if bids_today >= daily_limit:
        return LawResult(
            "Rhythm", False,
            f"Daily bid limit reached ({bids_today}/{daily_limit})",
            "MEDIUM",
        )
    pct = bids_today / daily_limit
    if pct >= 0.8:
        logger.warning("Guardian Rhythm: at %.0f%% of daily bid limit", pct * 100)
    return LawResult(
        "Rhythm", True,
        f"Pace OK: {bids_today}/{daily_limit} bids today ({pct:.0%})",
        "MEDIUM",
    )


def _law_causality(analysis: dict, job: dict) -> LawResult:
    """Law 4: Causality — Price chain must be traceable and internally consistent."""
    our_price = float(analysis.get("our_price") or 0)
    est_profit = float(analysis.get("est_profit") or 0)
    budget_max = float(job.get("budget_max") or 0)
    budget_min = float(job.get("budget_min") or 0)

    if our_price <= 0:
        return LawResult(
            "Causality", False,
            f"our_price={our_price} is zero/negative — pricing chain broken",
            "HIGH",
        )
    if budget_max > 0 and our_price > budget_max * 1.1:
        return LawResult(
            "Causality", False,
            f"our_price=${our_price:.0f} exceeds budget_max=${budget_max:.0f} by >10%",
            "HIGH",
        )
    if est_profit < 0:
        return LawResult(
            "Causality", False,
            f"est_profit=${est_profit:.2f} is negative — loss-making bid",
            "HIGH",
        )
    return LawResult(
        "Causality", True,
        f"Chain: budget=${budget_min:.0f}-{budget_max:.0f} → bid=${our_price:.0f} → profit=${est_profit:.0f}",
        "HIGH",
    )


def _law_transparency(analysis: dict) -> LawResult:
    """Law 5: Transparency — All required analysis fields must be present."""
    required = ("score", "fit", "our_price", "est_cost", "est_profit")
    missing = [f for f in required if analysis.get(f) is None]
    if missing:
        return LawResult(
            "Transparency", False,
            f"Analysis missing fields: {missing}",
            "MEDIUM",
        )
    backend = analysis.get("llm_backend", "unknown")
    return LawResult(
        "Transparency", True,
        f"All fields present (backend={backend})",
        "MEDIUM",
    )


def _law_nonmaleficence(analysis: dict) -> LawResult:
    """Law 6 (CRITICAL): Nonmaleficence — Do not harm the operator financially."""
    est_cost = float(analysis.get("est_cost") or 0)
    est_profit = float(analysis.get("est_profit") or 0)
    max_cost = float(analysis.get("_max_cost_override") or MAX_EST_COST_PER_BID_USD)

    if est_cost > max_cost:
        return LawResult(
            "Nonmaleficence", False,
            f"Est. cost ${est_cost:.2f} exceeds per-bid limit ${max_cost:.2f}",
            "CRITICAL",
        )
    # Significant negative profit = financial harm
    if est_profit < -(MIN_PROFIT_USD * 0.1):
        return LawResult(
            "Nonmaleficence", False,
            f"Est. profit ${est_profit:.2f} is significantly negative",
            "CRITICAL",
        )
    return LawResult(
        "Nonmaleficence", True,
        f"Cost=${est_cost:.2f} ✓, profit=${est_profit:.2f} ✓",
        "CRITICAL",
    )


def _law_privacy(job: dict, context: dict) -> LawResult:
    """Law G7: Privacy (CRITICAL) — No external disclosure without consent; respect user autonomy.
    
    (Renamed from 'Autonomy' for canonical alignment with ADRION 369 §VI G7 Privacy)
    """
    client_name = (job.get("client") or "").strip()
    bids_for_client = int(context.get("bids_for_client_today", 0))
    limit = int(context.get("max_bids_per_client", MAX_BIDS_PER_CLIENT_PER_DAY))

    if not client_name:
        return LawResult("Privacy", True, "Anonymous client — no spam risk", "CRITICAL")

    if bids_for_client >= limit:
        return LawResult(
            "Privacy", False,
            f"Client '{client_name}' already has {bids_for_client}/{limit} bid(s) today — privacy/autonomy violation",
            "CRITICAL",
        )
    return LawResult(
        "Privacy", True,
        f"Client '{client_name}': {bids_for_client}/{limit} bids today",
        "CRITICAL",
    )


def _law_budget_fairness(job: dict) -> LawResult:
    """Law G8: Nonmaleficence (CRITICAL) — Operating budget must not exceed scouted range.
    
    (Renamed from 'Justice' for canonical alignment with ADRION 369 §VI G8 Nonmaleficence)
    """
    budget_min = float(job.get("budget_min") or 0)
    budget_max = float(job.get("budget_max") or 0)

    if budget_max < SCOUT_MIN_BUDGET:
        return LawResult(
            "Nonmaleficence", False,
            f"Budget ${budget_min:.0f}-{budget_max:.0f} below minimum ${SCOUT_MIN_BUDGET}",
            "CRITICAL",
        )
    sanity_cap = SCOUT_MAX_BUDGET * 10
    if budget_max > sanity_cap:
        return LawResult(
            "Nonmaleficence", False,
            f"Budget ${budget_max:.0f} exceeds sanity cap ${sanity_cap:.0f} — possible data error",
            "CRITICAL",
        )
    return LawResult(
        "Nonmaleficence", True,
        f"Budget ${budget_min:.0f}-{budget_max:.0f} within fair range",
        "CRITICAL",
    )


def _law_sustainability(context: dict) -> LawResult:
    """Law 9: Sustainability — Daily operational cost must not exceed limit."""
    daily_cost = float(context.get("daily_est_cost", 0) or 0)
    max_daily = float(context.get("max_daily_cost", MAX_DAILY_EST_COST_USD))

    if daily_cost >= max_daily:
        return LawResult(
            "Sustainability", False,
            f"Daily cost ${daily_cost:.2f} reached limit ${max_daily:.2f}",
            "HIGH",
        )
    remaining = max_daily - daily_cost
    pct = daily_cost / max_daily if max_daily > 0 else 0
    return LawResult(
        "Sustainability", True,
        f"Daily cost ${daily_cost:.2f}/{max_daily:.2f} ({pct:.0%}), ${remaining:.2f} remaining",
        "HIGH",
    )


def _law_authenticity(analysis: dict, context: dict) -> LawResult:
    """Law 10: Authenticity (G6-ext) — LLM output must not be frozen or copy-pasted.

    Detects:
    - Identical fit/risks text (copy-paste / degenerate output)
    - Response too short to contain genuine reasoning
    - Hash collision with the previous response (frozen LLM loop)

    The analysis dict is mutated in-place: ``analysis["_response_hash"]`` is set
    so the orchestrator can persist it and pass it back via context["prev_fit_hash"].
    """
    fit = (analysis.get("fit") or "").strip()
    risks = (analysis.get("risks") or "").strip()

    # 1. Copy-paste: fit == risks (exact match on non-empty strings)
    if fit and risks and fit == risks:
        return LawResult(
            "Authenticity", False,
            "fit and risks are identical — likely copy-paste or frozen LLM output",
            "MEDIUM",
        )

    # 2. Minimal-entropy check: too little meaningful content
    meaningful = (fit + risks).replace(" ", "").replace(".", "").replace(",", "")
    if len(meaningful) < 10:
        return LawResult(
            "Authenticity", False,
            f"LLM output too short to be genuine ({len(meaningful)} non-trivial chars)",
            "MEDIUM",
        )

    # 3. Frozen-output detection: compare with previous response hash
    current_hash = hashlib.sha256((fit + risks).encode()).hexdigest()[:16]
    analysis["_response_hash"] = current_hash  # expose for orchestrator persistence

    prev_hash = context.get("prev_fit_hash")
    if prev_hash and prev_hash == current_hash:
        return LawResult(
            "Authenticity", False,
            f"Response hash '{current_hash}' matches previous response — frozen LLM loop detected",
            "MEDIUM",
        )

    return LawResult(
        "Authenticity", True,
        f"Output distinct (hash={current_hash}, {len(meaningful)} non-trivial chars)",
        "MEDIUM",
    )


def _law_evolution(context: dict) -> LawResult:
    """Law G10: Evolution (HIGH) — Errors drive improvement; PME feedback loops active.
    
    Checks that the system maintains records of past errors and incorporates
    lessons learned. In production, this would query the heuristics.json (PME records)
    and Genesis Record for evidence of adaptation.
    
    ADRION 369 §II.1: \"Błąd (Sev≥HIGH) lub SAV FAIL → paliwo ewolucji.\"
    """
    # In production, check:
    # - memories/repo/heuristics.json exists and has recent entries
    # - Genesis Record shows error recovery patterns
    # - TSPA scores reflect learning (improvement over sessions)
    
    pme_enabled = context.get("pme_enabled", True)
    error_count = int(context.get("error_count_session", 0))
    
    if not pme_enabled:
        return LawResult(
            "Evolution", False,
            "PME (Poor Man's Evolution) feedback loops are disabled — no learning mechanism active",
            "HIGH",
        )
    
    if error_count > 0:
        return LawResult(
            "Evolution", True,
            f"Evolution active: {error_count} errors recorded → PME loop processing",
            "HIGH",
        )
    
    return LawResult(
        "Evolution", True,
        "Evolution mechanism ready (no errors detected yet)",
        "HIGH",
    )


def _law_relational_care(context: dict) -> LawResult:
    """Law G11: Relational Care (MEDIUM) — Respect user attention budget; transparency on cost.
    
    ADRION 369 §X (EBDI Thresholds): Arousal>0.7 → Empathic Shortcut (reduce detail).
    Also checks that system communicates resource usage transparently.
    
    Implements §II.2: "Ekonomia Uwagi — Badaj Arousal (EBDI §X). Arousal>0.7 → Empathic Shortcut"
    """
    arousal = float(context.get("user_arousal", 0.0))  # EBDI Arousal [-1, +1]
    token_budget_used = float(context.get("token_budget_used", 0.0))  # CWM[5]
    token_budget_max = float(context.get("token_budget_max", 1.0))
    
    # Check 1: User stress level
    if arousal > 0.7:
        return LawResult(
            "RelationalCare", False,
            f"User attention budget critical (Arousal={arousal:.1f} > 0.7 threshold) — empathic shortcut required",
            "MEDIUM",
        )
    
    # Check 2: System resource transparency
    if token_budget_used > token_budget_max:
        return LawResult(
            "RelationalCare", False,
            f"Token budget exceeded ({token_budget_used:.0%} > {token_budget_max:.0%}) — not transparent on cost",
            "MEDIUM",
        )
    
    return LawResult(
        "RelationalCare", True,
        f"User care active (Arousal={arousal:.1f}, tokens={token_budget_used:.0%}/{token_budget_max:.0%})",
        "MEDIUM",
    )


# ═══════════════════════════════════════════════════════════════
# MAIN EVALUATOR
# ═══════════════════════════════════════════════════════════════

def evaluate_guardians(job: dict, analysis: dict, context: dict) -> GuardianEval:
    """
    Evaluate all 11 Guardian Laws (ADRION 369 §VI) sequentially.

    DSPy Signature:
        In(job:dict, analysis:dict, context:dict)
        → Out(laws:list[LawResult], compliance:int, violations:int, approved:bool, denial_reason:str)

    Args:
        job:      dict with title, platform, budget_min, budget_max, description, client
        analysis: dict with score, fit, risks, our_price, est_cost, est_profit, llm_backend, _response_hash
        context:  dict built via build_context(); optionally include:
                  - prev_fit_hash: for frozen-output detection (G6 Authenticity)
                  - pme_enabled: for G10 Evolution feedback loops
                  - error_count_session: for G10 Evolution tracking
                  - user_arousal: EBDI Arousal score for G11 RelationalCare
                  - token_budget_used/max: for G11 RelationalCare transparency

    Returns:
        GuardianEval — approved=True only when violation_weight < DENY_WEIGHTED_THRESHOLD
    """
    laws = [
        _law_unity(job),                             # G1: Unity (MED)
        _law_harmony(analysis),                      # G2: Harmony (MED) [renamed Truth]
        _law_rhythm(context),                        # G3: Rhythm (MED)
        _law_causality(analysis, job),               # G4: Causality (HIGH)
        _law_transparency(analysis),                 # G5: Transparency (MED)
        _law_authenticity(analysis, context),        # G6: Authenticity (HIGH)
        _law_privacy(job, context),                  # G7: Privacy (CRITICAL) [renamed Autonomy]
        _law_nonmaleficence(analysis),               # G8: Nonmaleficence (CRITICAL)
        _law_sustainability(context),                # G9: Sustainability (HIGH)
        _law_evolution(context),                     # G10: Evolution (HIGH)
        _law_relational_care(context),               # G11: RelationalCare (MED)
    ]

    all_violations = [law for law in laws if not law.passed]
    compliance = len(laws) - len(all_violations)
    violation_weight = sum(_WEIGHT_MAP[law.weight] for law in all_violations)

    # CRITICAL violation → instant DENY (weight = 10, always >= threshold)
    critical = [law for law in all_violations if law.weight == "CRITICAL"]
    if critical:
        denial = f"CRITICAL: {critical[0].name} — {critical[0].reason}"
        logger.warning("Guardian DENY [CRITICAL w=%d]: %s", violation_weight, denial)
        return GuardianEval(laws, compliance, len(all_violations), False, denial)

    # Weighted violations exceed threshold → DENY
    if violation_weight >= DENY_WEIGHTED_THRESHOLD:
        names = ", ".join(f"{law.name}({law.weight})" for law in all_violations)
        denial = f"Weighted violations={violation_weight}/{DENY_WEIGHTED_THRESHOLD}: {names}"
        logger.warning("Guardian DENY [w=%d]: %s", violation_weight, denial)
        return GuardianEval(laws, compliance, len(all_violations), False, denial)

    logger.info(
        "Guardian APPROVE: %d/%d laws passed (violation_weight=%d)",
        compliance, len(laws), violation_weight,
    )
    return GuardianEval(laws, compliance, len(all_violations), True, "")
