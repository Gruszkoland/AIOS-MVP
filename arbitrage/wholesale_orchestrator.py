"""
ADRION 369 — Wholesale Pipeline Orchestrator ("The Singularity Run")
End-to-end cycle: Scout → Oracle → Quantum → Execute → Dashboard.

Based on PROGRAMATOR #15 "PROTOKÓŁ AUTOMATYZACJI":
  Punkt 3 (Sentinel Scan)  → Wholesale Scout scans feeds/hurtownie
  Punkt 6 (Quantum Filter)  → Oracle + Quantum decide filter
  Punkt 9 (Financial Resonance) → Execute & persist results

Usage:
  python -m arbitrage.wholesale_orchestrator              # one-shot
  python -m arbitrage.wholesale_orchestrator --loop 60    # every 60s
"""
import logging
import time
from datetime import datetime

from .database import (
    get_deals,
    init_db,
    record_kpi_event,
    update_deal_status,
)
from .oracle import oracle_scan_products
from .quantum import get_autopojeza_status
from .wholesale_scout import scout_wholesale

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("wholesale_orchestrator")


def run_wholesale_cycle(
    feed_data=None,
    feed_format: str = "json",
    channel_filter: str | None = None,
    min_margin: float = 0.15,
    use_mock: bool = True,
    auto_execute: bool = False,
) -> dict:
    """
    One full wholesale pipeline cycle.

    Phase 1 (Punkt 3 — SENTINEL SCAN):
      Wholesale Scout parses feeds → enriches with Vortex → persists to DB.

    Phase 2 (Punkt 6 — QUANTUM FILTER):
      Oracle scans all new deals → predictions (BUY/HOLD/WAIT).

    Phase 3 (Punkt 9 — FINANCIAL RESONANCE):
      High-confidence BUY signals → mark as "execute" or queue for approval.

    Returns: summary dict with all phase results.
    """
    init_db()
    started_at = datetime.now().isoformat(timespec="seconds")
    log.info("═══ SINGULARITY RUN started at %s ═══", started_at)

    # ── Phase 1: SENTINEL SCAN (Punkt 3 — Impuls) ──────────────────────────
    log.info("[PUNKT 3] Wholesale Scout scanning...")
    scout_result = scout_wholesale(
        feed_data=feed_data,
        feed_format=feed_format,
        channel_filter=channel_filter,
        min_margin=min_margin,
        use_mock=use_mock,
    )
    new_deals = scout_result["new_deals"]
    total_qualified = scout_result["total_qualified"]
    log.info(
        "[PUNKT 3] Parsed: %d | Qualified: %d | New: %d | Mode: %s",
        scout_result["total_parsed"], total_qualified,
        new_deals, scout_result["mode"],
    )

    # ── Phase 2: QUANTUM FILTER (Punkt 6 — Stabilizacja) ───────────────────
    log.info("[PUNKT 6] Oracle scanning deals...")
    deals_for_oracle = []
    for d in scout_result["deals"]:
        deals_for_oracle.append({
            "name": d["product_name"],
            "wholesale_price": d["wholesale_price"],
            "retail_price": d["retail_price_de"],
        })

    oracle_result = oracle_scan_products(deals_for_oracle, channel_filter or "AUDIO_PREMIUM")
    summary_oracle = oracle_result["summary"]
    log.info(
        "[PUNKT 6] Singularities: %d | Buys: %d | Holds: %d | Waits: %d",
        summary_oracle["singularities"], summary_oracle["buys"],
        summary_oracle["holds"], summary_oracle["waits"],
    )

    # ── Phase 3: FINANCIAL RESONANCE (Punkt 9 — Osobliwość) ────────────────
    log.info("[PUNKT 9] Evaluating execution targets...")
    executed = 0
    held = 0
    rejected = 0

    # Match oracle predictions back to deals by index
    for i, prediction in enumerate(oracle_result["predictions"]):
        if i >= len(scout_result["deals"]):
            break

        deal = scout_result["deals"][i]
        action = prediction["action"]
        is_sing = prediction["is_singularity"]

        if action == "BUY" and is_sing:
            if auto_execute:
                # Auto-execute: mark deal as "executed" in DB
                db_deals = get_deals(
                    channel_id=deal.get("channel_id"),
                    status="new",
                    min_margin=deal.get("margin_pct", 0) - 0.01,
                    limit=1,
                )
                if db_deals:
                    update_deal_status(db_deals[0]["id"], "executed")
                    executed += 1
                    record_kpi_event(
                        stream="wholesale",
                        event_type="deal_executed",
                        amount_usd=deal.get("retail_price_de", 0) - deal.get("wholesale_price", 0),
                        meta={
                            "sku": deal["sku"],
                            "signal": prediction["signal"],
                            "confidence": prediction["confidence"],
                            "solfeggio_hz": prediction["solfeggio_hz"],
                        },
                    )
                    log.info(
                        "  ⚡ EXECUTE: %s | margin=%.1f%% | signal=%s | confidence=%.2f",
                        deal["product_name"], deal["margin_pct"] * 100,
                        prediction["signal"], prediction["confidence"],
                    )
            else:
                # Queue for approval
                db_deals = get_deals(
                    channel_id=deal.get("channel_id"),
                    status="new",
                    limit=1,
                )
                if db_deals:
                    update_deal_status(db_deals[0]["id"], "pending_approval")
                held += 1
                log.info(
                    "  📋 QUEUED: %s | margin=%.1f%% | signal=%s",
                    deal["product_name"], deal["margin_pct"] * 100,
                    prediction["signal"],
                )

        elif action == "BUY":
            held += 1
        elif action == "HOLD":
            held += 1
        else:
            rejected += 1

    # ── Autopojeza Status ───────────────────────────────────────────────────
    autopojeza = get_autopojeza_status()

    finished_at = datetime.now().isoformat(timespec="seconds")
    result = {
        "started_at": started_at,
        "finished_at": finished_at,
        "phase_1_scout": {
            "total_parsed": scout_result["total_parsed"],
            "total_qualified": total_qualified,
            "new_deals": new_deals,
            "updated_deals": scout_result["updated_deals"],
            "mode": scout_result["mode"],
        },
        "phase_2_oracle": {
            "singularities": summary_oracle["singularities"],
            "buys": summary_oracle["buys"],
            "holds": summary_oracle["holds"],
            "waits": summary_oracle["waits"],
        },
        "phase_3_execute": {
            "executed": executed,
            "held": held,
            "rejected": rejected,
            "auto_execute": auto_execute,
        },
        "autopojeza": autopojeza,
    }

    log.info(
        "═══ SINGULARITY RUN complete | Scout=%d Oracle=%d/%d/%d Execute=%d ═══",
        total_qualified, summary_oracle["singularities"],
        summary_oracle["buys"], summary_oracle["holds"], executed,
    )

    return result


def run_continuous(interval_seconds: int = 60, **kwargs):
    """Run wholesale pipeline in a loop."""
    log.info("Continuous wholesale mode — cycle every %ds. Ctrl-C to stop.", interval_seconds)
    while True:
        try:
            run_wholesale_cycle(**kwargs)
        except Exception as exc:
            log.error("Wholesale cycle error: %s", exc, exc_info=True)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ADRION 369 Wholesale Pipeline")
    parser.add_argument("--loop", type=int, default=0,
                        help="Loop interval in seconds (0=single run)")
    parser.add_argument("--channel", type=str, default=None,
                        help="Filter by channel_id (e.g. AUDIO_PREMIUM)")
    parser.add_argument("--min-margin", type=float, default=0.15,
                        help="Minimum margin threshold (default: 0.15)")
    parser.add_argument("--auto-execute", action="store_true",
                        help="Auto-execute singularity deals (no approval needed)")
    parser.add_argument("--live", action="store_true",
                        help="Use live feeds instead of mock data")
    args = parser.parse_args()

    if args.loop > 0:
        run_continuous(
            interval_seconds=args.loop,
            channel_filter=args.channel,
            min_margin=args.min_margin,
            auto_execute=args.auto_execute,
            use_mock=not args.live,
        )
    else:
        result = run_wholesale_cycle(
            channel_filter=args.channel,
            min_margin=args.min_margin,
            auto_execute=args.auto_execute,
            use_mock=not args.live,
        )
        import json
        print(json.dumps(result, indent=2))
