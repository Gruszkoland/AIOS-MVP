"""
ADRION 369 — Trinity Score Engine (M3 Real Implementation)

3 perspektywy oceny każdej decyzji arbitrażowej:

  Material     — dostępność zasobów systemowych (CPU/RAM) via psutil
                 Agregacja: harmonic_mean(cpu_avail, ram_avail)
                 Logika: wszystkie składniki MUSZĄ przejść (fail-fast)

  Intellectual — jakość analizy LLM (score + reasoning)
                 Agregacja: harmonic_mean(score_norm, reasoning_norm)
                 Logika: niska ocena jakościowa blokuje całą analizę

  Essential    — zgodność z celem + rentowność oferty
                 Agregacja: geometric_mean(purpose_match, profit_norm)
                 Logika: oba muszą być wysokie (multiplikatywne)

Decyzja Trinity:
  combined = (material + intellectual + essential) / 3
  approved = material >= 0.3 AND intellectual >= 0.5 AND essential >= 0.2
             AND combined >= TRINITY_MIN_COMBINED
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

from .config import MIN_ANALYZER_SCORE, MIN_PROFIT_USD

logger = logging.getLogger("adrion.trinity")

# ─────────────────────────────────────────────────────────────────────
# Progi zatwierdzenia
# ─────────────────────────────────────────────────────────────────────
TRINITY_MIN_MATERIAL     = 0.30  # CPU/RAM muszą być co najmniej na 30% free
TRINITY_MIN_INTELLECTUAL = 0.50  # Score + reasoning ≥ 50% jakoności
TRINITY_MIN_ESSENTIAL    = 0.20  # Purpose + profit alignment
TRINITY_MIN_COMBINED     = 0.40  # Łączny próg zatwierdzenia

# Stałe obliczeniowe
_REASONING_TARGET_CHARS = 200    # Docelowa długość reasoning (100% = 200 znaków)
_PURPOSE_KEYWORDS = frozenset({
    "content", "writing", "blog", "article", "copy", "seo",
    "ghostwriting", "editorial", "text", "post", "script",
    "copywriting", "proofreading", "translation", "newsletter",
})


# ─────────────────────────────────────────────────────────────────────
# Struktury danych
# ─────────────────────────────────────────────────────────────────────

@dataclass
class TrinityScore:
    """Wynik ewaluacji Trinity — 3 perspektywy + decyzja końcowa."""
    material:     float          # 0.0–1.0 — zasoby systemowe
    intellectual: float          # 0.0–1.0 — jakość analizy LLM
    essential:    float          # 0.0–1.0 — zgodność z celem + profit
    combined:     float          # 0.0–1.0 — łączny wynik
    approved:     bool           # True jeśli wszystkie progi spełnione
    details:      dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "material":     round(self.material, 4),
            "intellectual": round(self.intellectual, 4),
            "essential":    round(self.essential, 4),
            "combined":     round(self.combined, 4),
            "approved":     self.approved,
            "details":      self.details,
        }


# ─────────────────────────────────────────────────────────────────────
# Pomocnicze funkcje agregacji
# ─────────────────────────────────────────────────────────────────────

def _harmonic_mean(a: float, b: float) -> float:
    """Harmonic mean — wrażliwa na niskie wartości (fail-fast)."""
    if a <= 0 or b <= 0:
        return 0.0
    return 2 * a * b / (a + b)


def _geometric_mean(a: float, b: float) -> float:
    """Geometric mean — multiplikatywna (obie wartości muszą być wysokie)."""
    if a < 0 or b < 0:
        return 0.0
    return math.sqrt(a * b)


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


# ─────────────────────────────────────────────────────────────────────
# Perspektywa 1: Material — zasoby systemowe (CPU/RAM)
# ─────────────────────────────────────────────────────────────────────

def _score_material(resources: dict | None) -> tuple[float, dict]:
    """
    Oblicza dostępność zasobów systemowych.

    Args:
        resources: dict z polami cpu_percent (0-100) i ram_available_ratio (0-1),
                   lub None → próba odczytu przez psutil.

    Returns:
        (score 0-1, details dict)
    """
    cpu_percent: float
    ram_ratio:   float

    if resources is not None:
        cpu_percent = float(resources.get("cpu_percent", 50.0))
        ram_ratio   = float(resources.get("ram_available_ratio", 0.5))
    else:
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            vm          = psutil.virtual_memory()
            ram_ratio   = vm.available / vm.total
        except Exception as exc:  # pragma: no cover
            logger.warning("psutil unavailable (%s) — using fallback 50%%", exc)
            cpu_percent = 50.0
            ram_ratio   = 0.5

    cpu_avail = _clamp((100.0 - cpu_percent) / 100.0)
    ram_avail = _clamp(ram_ratio)
    score     = _harmonic_mean(cpu_avail, ram_avail)

    return score, {
        "cpu_percent":      cpu_percent,
        "ram_available_pct": round(ram_ratio * 100, 1),
        "cpu_avail":         round(cpu_avail, 4),
        "ram_avail":         round(ram_avail, 4),
    }


# ─────────────────────────────────────────────────────────────────────
# Perspektywa 2: Intellectual — jakość analizy LLM
# ─────────────────────────────────────────────────────────────────────

def _score_intellectual(analysis: dict) -> tuple[float, dict]:
    """
    Oblicza jakość analizy LLM.

    Składniki:
      - score_norm:    (score / 10) * (score >= MIN_ANALYZER_SCORE ? 1 : 0.5)
      - reasoning_norm: min(len(fit+risks) / TARGET, 1.0)
      - harmonic_mean(score_norm, reasoning_norm)
    """
    raw_score = float(analysis.get("score") or 0)
    fit       = (analysis.get("fit")   or "").strip()
    risks     = (analysis.get("risks") or "").strip()

    # Niespełnienie progu MIN_ANALYZER_SCORE → obniżka o 50%
    score_norm = _clamp(raw_score / 10.0)
    if raw_score < MIN_ANALYZER_SCORE:
        score_norm *= 0.5

    reasoning_chars = len(fit) + len(risks)
    reasoning_norm  = _clamp(reasoning_chars / _REASONING_TARGET_CHARS)

    score = _harmonic_mean(score_norm, reasoning_norm)

    return score, {
        "raw_score":       raw_score,
        "min_score":       MIN_ANALYZER_SCORE,
        "score_norm":      round(score_norm, 4),
        "reasoning_chars": reasoning_chars,
        "reasoning_norm":  round(reasoning_norm, 4),
    }


# ─────────────────────────────────────────────────────────────────────
# Perspektywa 3: Essential — zgodność z celem + rentowność
# ─────────────────────────────────────────────────────────────────────

def _score_essential(job: dict, analysis: dict) -> tuple[float, dict]:
    """
    Ocenia zgodność z celem systemu i rentowność oferty.

    Składniki:
      - purpose_match: min(keyword_count / 2, 1.0)
        Co najmniej 2 słowa kluczowe = 100% zgodności
      - profit_norm: min(est_profit / MIN_PROFIT_USD, 1.0), 0 jeśli ujemny
      - geometric_mean(purpose_match, profit_norm)
    """
    title       = (job.get("title")       or "").lower()
    description = (job.get("description") or "").lower()
    combined    = title + " " + description

    keyword_count = sum(1 for kw in _PURPOSE_KEYWORDS if kw in combined)
    purpose_match = _clamp(keyword_count / 2.0)

    est_profit  = float(analysis.get("est_profit") or 0)
    profit_norm: float
    if est_profit <= 0:
        profit_norm = 0.0
    else:
        profit_norm = _clamp(est_profit / MIN_PROFIT_USD) if MIN_PROFIT_USD > 0 else 1.0

    score = _geometric_mean(purpose_match, profit_norm)

    return score, {
        "keyword_count":  keyword_count,
        "purpose_match":  round(purpose_match, 4),
        "est_profit":     est_profit,
        "min_profit":     MIN_PROFIT_USD,
        "profit_norm":    round(profit_norm, 4),
    }


# ─────────────────────────────────────────────────────────────────────
# Główna funkcja
# ─────────────────────────────────────────────────────────────────────

def evaluate_trinity(
    job:              dict,
    analysis:         dict,
    system_resources: dict | None = None,
) -> TrinityScore:
    """
    Ocenia ofertę arbitrażową z 3 perspektyw Trinity.

    Args:
        job:              dict z polami title, description, budget_*
        analysis:         dict z polami score, fit, risks, est_profit
        system_resources: opcjonalny dict {cpu_percent, ram_available_ratio};
                          jeśli None — odczyt przez psutil (lub fallback 50%)

    Returns:
        TrinityScore — wszystkie perspektywy + decyzja approved/denied
    """
    m_score, m_details = _score_material(system_resources)
    i_score, i_details = _score_intellectual(analysis)
    e_score, e_details = _score_essential(job, analysis)

    combined = (m_score + i_score + e_score) / 3.0

    # Fail-fast: każda perspektywa ma własny próg
    approved = (
        m_score  >= TRINITY_MIN_MATERIAL
        and i_score >= TRINITY_MIN_INTELLECTUAL
        and e_score >= TRINITY_MIN_ESSENTIAL
        and combined >= TRINITY_MIN_COMBINED
    )

    if not approved:
        reasons = []
        if m_score  < TRINITY_MIN_MATERIAL:
            reasons.append(f"material={m_score:.2f}<{TRINITY_MIN_MATERIAL}")
        if i_score < TRINITY_MIN_INTELLECTUAL:
            reasons.append(f"intellectual={i_score:.2f}<{TRINITY_MIN_INTELLECTUAL}")
        if e_score < TRINITY_MIN_ESSENTIAL:
            reasons.append(f"essential={e_score:.2f}<{TRINITY_MIN_ESSENTIAL}")
        if combined < TRINITY_MIN_COMBINED:
            reasons.append(f"combined={combined:.2f}<{TRINITY_MIN_COMBINED}")
        logger.info("Trinity DENY: %s", "; ".join(reasons))
    else:
        logger.debug(
            "Trinity APPROVE: combined=%.3f (M=%.3f I=%.3f E=%.3f)",
            combined, m_score, i_score, e_score,
        )

    return TrinityScore(
        material=round(m_score, 4),
        intellectual=round(i_score, 4),
        essential=round(e_score, 4),
        combined=round(combined, 4),
        approved=approved,
        details={
            "material":     m_details,
            "intellectual": i_details,
            "essential":    e_details,
            "thresholds": {
                "material":     TRINITY_MIN_MATERIAL,
                "intellectual": TRINITY_MIN_INTELLECTUAL,
                "essential":    TRINITY_MIN_ESSENTIAL,
                "combined":     TRINITY_MIN_COMBINED,
            },
        },
    )
