"""
ADRION 369 - Analyzer Agent
Scores jobs using LLM (openrouter | openai | anthropic | mock).
Returns score 1-10 + profit estimate + reasoning.

Vortex Extensions (PROGRAMATOR #9, #10, #19):
  - digital_root(): 3-6-9 redukcja cyfrowa
  - vortex_filter(): filtr rezonansu marży
  - calculate_market_resonance(): DE↔PL delta scoring
"""
import json
import logging
import random

from .config import (
    ANALYZER_SYSTEM,
    ANALYZER_USER,
    ANTHROPIC_KEY,
    LLM_MODEL,
    MIN_ANALYZER_SCORE,
    MIN_PROFIT_USD,
    OPENAI_KEY,
    OPENROUTER_KEY,
    get_active_llm_backend,
)

logger = logging.getLogger("adrion.llm.analyzer")


def _call_openrouter(prompt: str, model: str = LLM_MODEL) -> str:
    from openai import OpenAI
    client = OpenAI(
        api_key=OPENROUTER_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": ANALYZER_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.3,
        max_tokens=400,
    )
    return response.choices[0].message.content


def _call_openai(prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": ANALYZER_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.3,
        max_tokens=400,
    )
    return response.choices[0].message.content


def _call_anthropic(prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    message = client.messages.create(
        model="claude-haiku-20240307",
        max_tokens=400,
        system=ANALYZER_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _mock_analyze(job: dict) -> dict:
    budget_mid = (job.get("budget_min", 0) + job.get("budget_max", 100)) / 2
    score = random.randint(6, 10)
    our_price = round(budget_mid * random.uniform(0.7, 0.9), 2)
    est_cost  = round(random.uniform(0, 3), 2)
    return {
        "score":      score,
        "fit":        "Good match for content writing skills (mock analysis)",
        "risks":      "Client communication unknown (mock)",
        "est_hours":  round(budget_mid / 25, 1),
        "our_price":  our_price,
        "est_cost":   est_cost,
        "est_profit": round(our_price - est_cost, 2),
    }


def analyze_job(job: dict) -> dict:
    """
    Run LLM analysis on a job.
    Returns analysis dict + llm_backend used.
    """
    backend = get_active_llm_backend()
    job_id = job.get("id", "unknown")

    if backend == "mock":
        result = _mock_analyze(job)
        result["llm_backend"] = "mock"
        logger.info("event=llm_analyze backend=mock mode=mock job_id=%s", job_id)
        return result

    prompt = ANALYZER_USER.format(
        title=job.get("title", ""),
        platform=job.get("platform", ""),
        budget_min=job.get("budget_min", 0),
        budget_max=job.get("budget_max", 100),
        description=(job.get("description", "") or "")[:800],
    )

    try:
        logger.info("event=llm_analyze backend=%s mode=attempt job_id=%s", backend, job_id)
        if backend == "openrouter":
            raw = _call_openrouter(prompt)
        elif backend == "openai":
            raw = _call_openai(prompt)
        elif backend == "anthropic":
            raw = _call_anthropic(prompt)
        else:
            raw = None

        if raw:
            # Extract JSON from response
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            result = json.loads(raw[start:end])
            result["llm_backend"] = backend
            logger.info("event=llm_analyze backend=%s mode=success job_id=%s", backend, job_id)
            return result

    except Exception as e:
        logger.warning("event=llm_analyze backend=%s mode=fallback job_id=%s error=%s", backend, job_id, e)

    result = _mock_analyze(job)
    result["llm_backend"] = "mock"
    logger.info("event=llm_analyze backend=mock mode=recovered job_id=%s", job_id)
    return result


def filter_worthy(analysis: dict) -> bool:
    """Return True if job passes minimum quality thresholds."""
    return (
        analysis.get("score", 0) >= MIN_ANALYZER_SCORE
        and analysis.get("est_profit", 0) >= MIN_PROFIT_USD
    )


# ═══════════════════════════════════════════════════════════════
# VORTEX MATH EXTENSIONS (PROGRAMATOR docs #9, #10, #19)
# ═══════════════════════════════════════════════════════════════

def digital_root(n: int) -> int:
    """Redukcja cyfrowa do jednej cyfry (Vortex Math 3-6-9)."""
    if n == 0:
        return 0
    r = abs(n) % 9
    return r if r else 9


def vortex_filter(margin_pct: float, min_margin: float = 0.15) -> bool:
    """Akceptuj marże z rezonansem 3-6-9 powyżej progu."""
    if margin_pct < min_margin:
        return False
    root = digital_root(int(margin_pct * 100))
    return root in (3, 6, 9)


def calculate_market_resonance(price_a: float, price_b: float) -> dict:
    """
    Oblicz rezonans cenowy między dwoma rynkami.
    price_a: source (wholesale)
    price_b: target (retail)
    """
    if price_a <= 0 or price_b <= 0 or price_b <= price_a:
        return {"resonance": 0, "margin_pct": 0.0, "vortex_pass": False, "is_369": False}
    diff = price_b - price_a
    margin_pct = diff / price_b
    resonance = digital_root(int(diff))
    return {
        "resonance": resonance,
        "margin_pct": round(margin_pct, 4),
        "vortex_pass": vortex_filter(margin_pct),
        "is_369": resonance in (3, 6, 9),
    }
