"""
ADRION 369 - Bidder Agent
Generates cover letters and creates bid records (approved=False).
Human must approve every bid before it is sent.
"""
import logging

from .config import (
    ANTHROPIC_KEY,
    COVER_LETTER_SYSTEM,
    COVER_LETTER_USER,
    LLM_MODEL,
    OPENAI_KEY,
    OPENROUTER_KEY,
    check_external_service_allowed,
    get_active_llm_backend,
)
from .database import insert_bid, set_job_status

logger = logging.getLogger("adrion.llm.bidder")


def _days_estimate(est_hours: float) -> int:
    if est_hours <= 4:
        return 2
    elif est_hours <= 10:
        return 5
    elif est_hours <= 20:
        return 7
    return 14


def _mock_cover_letter(job: dict, our_price: float, est_days: int) -> str:
    return (
        f"Your project '{job.get('title', 'this project')}' caught my attention immediately — "
        f"it's exactly the kind of work I excel at.\n\n"
        f"With 5+ years crafting compelling content for B2B and D2C brands, I understand "
        f"what makes readers take action. My recent work includes high-converting blog posts, "
        f"product descriptions that boosted click-through rates by 40%, and SEO articles ranking "
        f"on page 1 within 3 months.\n\n"
        f"For ${our_price}, I'll deliver polished, ready-to-publish content within {est_days} days. "
        f"I'm also happy to revise until you're 100% satisfied.\n\n"
        f"Let's discuss your vision — message me and we can start immediately."
    )


def _generate_cover_letter(job: dict, our_price: float, est_hours: float) -> str:
    est_days = _days_estimate(est_hours)
    backend  = get_active_llm_backend()
    job_id = job.get("id", "unknown")

    if backend == "mock":
        logger.info("event=llm_cover_letter backend=mock mode=mock job_id=%s", job_id)
        return _mock_cover_letter(job, our_price, est_days)

    prompt = COVER_LETTER_USER.format(
        title=job.get("title", ""),
        platform=job.get("platform", ""),
        description=(job.get("description", "") or "")[:500],
        our_price=our_price,
        est_days=est_days,
    )

    try:
        logger.info("event=llm_cover_letter backend=%s mode=attempt job_id=%s", backend, job_id)
        if backend == "openrouter":
            check_external_service_allowed("openrouter")
            from openai import OpenAI
            client = OpenAI(api_key=OPENROUTER_KEY, base_url="https://openrouter.ai/api/v1")
            resp = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": COVER_LETTER_SYSTEM},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.7,
                max_tokens=350,
            )
            logger.info("event=llm_cover_letter backend=%s mode=success job_id=%s", backend, job_id)
            return resp.choices[0].message.content

        elif backend == "openai":
            check_external_service_allowed("openai")
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_KEY)
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": COVER_LETTER_SYSTEM},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.7,
                max_tokens=350,
            )
            logger.info("event=llm_cover_letter backend=%s mode=success job_id=%s", backend, job_id)
            return resp.choices[0].message.content

        elif backend == "anthropic":
            check_external_service_allowed("anthropic")
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
            msg = client.messages.create(
                model="claude-haiku-20240307",
                max_tokens=350,
                system=COVER_LETTER_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            logger.info("event=llm_cover_letter backend=%s mode=success job_id=%s", backend, job_id)
            return msg.content[0].text

    except Exception as e:
        logger.warning("event=llm_cover_letter backend=%s mode=fallback job_id=%s error=%s", backend, job_id, e)

    return _mock_cover_letter(job, our_price, est_days)


def create_bid(job: dict, analysis: dict) -> dict:
    """
    Generate cover letter and save bid to DB with approved=False.
    Returns bid record dict.
    """
    our_price   = analysis.get("our_price", 0)
    est_profit  = analysis.get("est_profit", 0)
    est_hours   = analysis.get("est_hours", 4)
    score       = analysis.get("score", 0)
    llm_backend = analysis.get("llm_backend", "mock")

    cover_letter = _generate_cover_letter(job, our_price, est_hours)

    bid_record = {
        "job_id":        job["id"],
        "cover_letter":  cover_letter,
        "our_price":     our_price,
        "est_profit_usd": est_profit,
        "analyzer_score": score,
        "llm_backend":   llm_backend,
    }

    bid_id = insert_bid(bid_record)
    set_job_status(job["id"], "analyzed")

    return {**bid_record, "id": bid_id, "approved": 0}
