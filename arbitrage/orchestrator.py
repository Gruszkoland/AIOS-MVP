"""
ADRION 369 - SAP Orchestrator
Main cycle: Scout → Analyze → Bid → Track XRP progress.

Run once:        python -m arbitrage.orchestrator
Run continuous:  python -m arbitrage.orchestrator --loop --interval 30
"""
import argparse
import logging
import time
from datetime import datetime

from .analyzer import analyze_job
from .bidder import create_bid
from .config import (
    DAILY_BID_LIMIT,
    MAX_BIDS_PER_CLIENT_PER_DAY,
    MAX_DAILY_EST_COST_USD,
    MAX_EST_COST_PER_BID_USD,
    MIN_ANALYZER_SCORE,
)
from .database import (
    get_client_bid_count_today,
    get_conn,
    get_stream_kpis,
    init_db,
    record_kpi_event,
    set_job_status,
)
from .guardian import build_context as build_guardian_context
from .guardian import evaluate_guardians
from .scout import run_scout
from .trinity import evaluate_trinity
from .xrp_tracker import get_progress, update_xrp_snapshot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("orchestrator")


def _count_bids_today() -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM bids WHERE DATE(created_at)=DATE('now')"
        ).fetchone()
        return row["c"] if row else 0


def run_cycle(dry_run: bool = False) -> dict:
    """
    One full Scout → Analyze → Bid cycle.
    Returns a summary dict.
    """
    init_db()
    ts = datetime.now().isoformat(timespec="seconds")
    log.info("=== ADRION 369 Cycle started at %s ===", ts)

    # 1. Scout
    log.info("[SCOUT] Fetching jobs...")
    scout_result = run_scout()
    raw_jobs = scout_result.get("jobs", [])
    new_count = int(scout_result.get("new_jobs", 0))
    log.info("[SCOUT] %d new / %d fetched (mode=%s)", new_count, len(raw_jobs), scout_result.get("mode"))

    # 2. Analyze & Bid
    bids_today = _count_bids_today()
    bids_created = 0
    analyzed_count = 0
    trinity_denied_count = 0
    guardian_denied_count = 0
    stream_kpis = get_stream_kpis()
    daily_est_cost = float(stream_kpis.get("daily_est_cost_usd", 0))

    with get_conn() as conn:
        pending = conn.execute(
            "SELECT * FROM jobs WHERE status='new' ORDER BY scouted_at DESC LIMIT 20"
        ).fetchall()

    for row in pending:
        job = dict(row)
        if bids_today + bids_created >= DAILY_BID_LIMIT:
            log.info("[BID] Daily limit %d reached — stopping", DAILY_BID_LIMIT)
            break

        log.info("[ANALYZE] %s | %s", job["platform"], job["title"][:60])
        analysis = analyze_job(job)
        analyzed_count += 1
        score = analysis.get("score", 0)
        our_price = analysis.get("our_price", 0)
        est_profit = analysis.get("est_profit", 0)
        est_cost = float(analysis.get("est_cost", 0) or 0)
        client_name = (job.get("client") or "").strip()
        set_job_status(job["id"], "analyzed")
        record_kpi_event(
            stream="b2b",
            event_type="analyzed",
            amount_usd=0,
            est_cost_usd=est_cost,
            meta={"job_id": job["id"], "score": score},
        )
        daily_est_cost += est_cost

        if score < MIN_ANALYZER_SCORE:
            log.info("  ↳ Score %d < %d — skipping", score, MIN_ANALYZER_SCORE)
            set_job_status(job["id"], "ignored")
            continue

        if est_cost > MAX_EST_COST_PER_BID_USD:
            log.info("  ↳ Est. cost %.2f > %.2f — skipping", est_cost, MAX_EST_COST_PER_BID_USD)
            set_job_status(job["id"], "ignored")
            continue

        if daily_est_cost > MAX_DAILY_EST_COST_USD:
            log.info("[GUARDRAIL] Daily est. cost %.2f > %.2f — stopping", daily_est_cost, MAX_DAILY_EST_COST_USD)
            break

        bids_for_client_today = 0
        if client_name:
            bids_for_client_today = get_client_bid_count_today(client_name)
            if bids_for_client_today >= MAX_BIDS_PER_CLIENT_PER_DAY:
                log.info(
                    "  ↳ Client '%s' reached daily bid cap %d — skipping",
                    client_name,
                    MAX_BIDS_PER_CLIENT_PER_DAY,
                )
                set_job_status(job["id"], "ignored")
                continue

        # ── Trinity Score — 3 perspectives: Material / Intellectual / Essential ──
        trinity_eval = evaluate_trinity(job, analysis)
        if not trinity_eval.approved:
            log.info(
                "  ↳ [TRINITY DENIED] M=%.2f I=%.2f E=%.2f combined=%.2f",
                trinity_eval.material, trinity_eval.intellectual,
                trinity_eval.essential, trinity_eval.combined,
            )
            set_job_status(job["id"], "trinity_denied")
            record_kpi_event(
                stream="b2b",
                event_type="trinity_denied",
                amount_usd=0,
                est_cost_usd=0,
                meta={
                    "job_id": job["id"],
                    "material": trinity_eval.material,
                    "intellectual": trinity_eval.intellectual,
                    "essential": trinity_eval.essential,
                    "combined": trinity_eval.combined,
                },
            )
            trinity_denied_count += 1
            continue
        log.info(
            "  ↳ [TRINITY APPROVED] M=%.2f I=%.2f E=%.2f → combined=%.2f",
            trinity_eval.material, trinity_eval.intellectual,
            trinity_eval.essential, trinity_eval.combined,
        )

        # ── Guardian Laws — 9 ethical laws validated sequentially ──
        guardian_eval = evaluate_guardians(
            job,
            analysis,
            build_guardian_context(
                bids_today=bids_today + bids_created,
                daily_est_cost=daily_est_cost,
                bids_for_client_today=bids_for_client_today,
            ),
        )
        if not guardian_eval.approved:
            log.info("  ↳ [GUARDIAN DENIED] %s", guardian_eval.denial_reason)
            set_job_status(job["id"], "guardian_denied")
            record_kpi_event(
                stream="b2b",
                event_type="guardian_denied",
                amount_usd=0,
                est_cost_usd=0,
                meta={"job_id": job["id"], "denial": guardian_eval.denial_reason},
            )
            guardian_denied_count += 1
            continue
        log.info("  ↳ [GUARDIAN APPROVED] %d/9 laws passed", guardian_eval.compliance)

        log.info("  ↳ Score %d | $%.0f | profit $%.0f", score, our_price, est_profit)
        if not dry_run:
            bid = create_bid(job, analysis)
            if bid:
                bids_created += 1
                record_kpi_event(
                    stream="b2b",
                    event_type="bid_created",
                    amount_usd=float(bid.get("our_price", 0) or 0),
                    est_cost_usd=est_cost,
                    meta={"job_id": job["id"], "bid_id": bid.get("id")},
                )
                log.info("  ↳ Bid created (pending approval)")

    # 3. XRP Snapshot
    snap = update_xrp_snapshot()
    progress = get_progress()

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO kpis (jobs_scouted, bids_sent) VALUES (?,?)",
            (new_count, bids_created),
        )

    summary = {
        "timestamp": ts,
        "jobs_scouted": len(raw_jobs),
        "new_jobs": new_count,
        "analyzed": analyzed_count,
        "trinity_denied": trinity_denied_count,
        "guardian_denied": guardian_denied_count,
        "bids_created": bids_created,
        "bids_today": bids_today + bids_created,
        "xrp_price": snap.get("xrp_price_usd", 0),
        "xrp_earned": progress.get("xrp_earned", 0),
        "xrp_target": progress.get("xrp_target", 1000),
        "pct_complete": progress.get("pct_complete", 0),
        "total_earned_usd": progress.get("total_earned_usd", 0),
    }

    log.info(
        "=== Done | new=%d analyzed=%d bids=%d XRP=%.4f/%.0f (%.1f%%) ===",
        new_count, analyzed_count, bids_created,
        summary["xrp_earned"], summary["xrp_target"], summary["pct_complete"],
    )
    return summary


def run_continuous(interval_minutes: int = 30):
    log.info("Continuous mode — cycle every %d min. Ctrl-C to stop.", interval_minutes)
    while True:
        try:
            run_cycle()
        except Exception as exc:
            log.error("Cycle error: %s", exc, exc_info=True)
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ADRION 369 Arbitrage Orchestrator")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=30, help="Minutes between cycles")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, no bids")
    args = parser.parse_args()

    if args.loop:
        run_continuous(args.interval)
    else:
        result = run_cycle(dry_run=args.dry_run)
        print("\n--- Summary ---")
        for k, v in result.items():
            print(f"  {k}: {v}")
