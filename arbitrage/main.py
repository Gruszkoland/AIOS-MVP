"""
ADRION 369 — Main CLI Orchestrator
Autonomous content-arbitrage pipeline targeting 1000 XRP.

Usage:
    python -m arbitrage.main status
    python -m arbitrage.main scout
    python -m arbitrage.main analyze
    python -m arbitrage.main review          # human approval loop
    python -m arbitrage.main earn <amount>   # manually record USD earning
    python -m arbitrage.main run             # full pipeline (scout→analyze→review)
"""

import sys
import logging
import sys

# Force UTF-8 output on Windows to support emoji/Unicode in logs
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from arbitrage.database import init_db, get_jobs, get_pending_bids, approve_bid, get_totals
from arbitrage.scout    import run_scout
from arbitrage.analyzer import analyze_job
from arbitrage.bidder   import create_bid
from arbitrage.xrp      import get_progress, print_progress, record_earning
from arbitrage.config   import MIN_ANALYZER_SCORE, DAILY_BID_LIMIT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline steps
# ──────────────────────────────────────────────────────────────────────────────

def cmd_status():
    """Show XRP progress + pipeline stats."""
    print_progress()
    totals = get_totals()
    print("📊 Pipeline Stats:")
    print(f"   Total jobs scouted : {totals.get('total_jobs', 0)}")
    print(f"   Bids sent          : {totals.get('bids_sent', 0)}")
    print(f"   Total profit (USD) : ${totals.get('total_profit', 0):.2f}")


def cmd_scout():
    """Discover new freelance jobs and store in DB."""
    print("\n🔍 SCOUT — Scanning platforms for content writing jobs...")
    result = run_scout()
    print(f"✅ Scout complete: {result['new_jobs']} new jobs found (mode={result['mode']})")
    jobs = result["jobs"]
    if jobs:
        print("\nTop discoveries:")
        for j in jobs[:5]:
            budget = f"${j.get('budget_min',0):.0f}–${j.get('budget_max',0):.0f}"
            print(f"  [{j.get('platform','?'):10s}] {j.get('title','')[:60]:<60} {budget}")


def cmd_analyze():
    """Score all new jobs with LLM and create bids for high-scorers."""
    new_jobs = get_jobs(status="new", limit=50)
    if not new_jobs:
        print("⚠️  No new jobs to analyze. Run 'scout' first.")
        return

    print(f"\n🧠 ANALYZER — Processing {len(new_jobs)} jobs...")
    bids_created = 0

    for job in new_jobs:
        if bids_created >= DAILY_BID_LIMIT:
            print(f"⏸️  Daily bid limit ({DAILY_BID_LIMIT}) reached.")
            break
        try:
            analysis = analyze_job(job)
            score    = analysis.get("score", 0)
            profit   = analysis.get("est_profit", 0)

            flag = "✅" if score >= MIN_ANALYZER_SCORE else "⏭️ "
            print(f"  {flag} [{score:2d}/10] ${profit:5.0f} profit — {job.get('title','')[:55]}")

            if score >= MIN_ANALYZER_SCORE:
                create_bid(job, analysis)
                bids_created += 1
        except Exception as exc:
            logger.warning("Analyze error for job %s: %s", job.get("id", "?"), exc)

    print(f"\n✅ Analyzer done: {bids_created} bids queued for review")


def cmd_review():
    """Human-in-the-loop approval for queued bids."""
    pending = get_pending_bids()
    if not pending:
        print("✅ No pending bids to review.")
        return

    print(f"\n📋 REVIEW — {len(pending)} bids awaiting your approval\n")

    for bid in pending:
        print("─" * 70)
        print(f"Job    : {bid.get('title', '')}")
        print(f"Platform: {bid.get('platform', '')}")
        print(f"URL    : {bid.get('url', '')}")
        print(f"Score  : {bid.get('analyzer_score', 0)}/10  |  Bid: ${bid.get('our_price', 0):.2f}  |  Est profit: ${bid.get('est_profit_usd', 0):.2f}")
        print(f"\nCover letter:\n{bid.get('cover_letter', '')}\n")

        while True:
            choice = input("Approve? [y=yes / n=no / q=quit]: ").strip().lower()
            if choice in ("y", "n", "q"):
                break

        if choice == "q":
            print("Review paused.")
            break
        elif choice == "y":
            approve_bid(bid["id"], approved=True)
            print(f"✅ Bid #{bid['id']} approved — copy the cover letter and submit on the platform.")
        else:
            approve_bid(bid["id"], approved=False)
            print(f"⏭️  Bid #{bid['id']} skipped.")


def cmd_earn(amount_str: str):
    """Manually record a USD earning (e.g. after completing a job)."""
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError as exc:
        print(f"❌ Invalid amount: {exc}")
        sys.exit(1)

    record_earning(amount, source="manual")
    print(f"✅ Recorded earning: ${amount:.2f} USD")
    print_progress()


def cmd_run():
    """Full autonomous pipeline: scout → analyze → show review prompt."""
    print("\n🚀 ADRION 369 — Full Pipeline Starting")
    print("=" * 50)
    cmd_scout()
    cmd_analyze()
    print("\n🔔 Run 'python -m arbitrage.main review' to approve bids interactively.")
    cmd_status()


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

COMMANDS = {
    "status":  (cmd_status,  []),
    "scout":   (cmd_scout,   []),
    "analyze": (cmd_analyze, []),
    "review":  (cmd_review,  []),
    "run":     (cmd_run,     []),
    "earn":    (cmd_earn,    ["amount_usd"]),
}

HELP = """\
ADRION 369 — XRP Arbitrage Orchestrator
Target: 1000 XRP via content writing arbitrage

Commands:
  status             Show XRP progress + pipeline stats
  scout              Discover new freelance jobs
  analyze            Score & prepare bids for new jobs
  review             Human approval loop for queued bids
  earn <amount_usd>  Record a USD earning manually
  run                Full pipeline (scout → analyze → status)

Example:
  python -m arbitrage.main run
  python -m arbitrage.main earn 150
"""


def main():
    init_db()

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(HELP)
        return

    cmd = sys.argv[1].lower()
    if cmd not in COMMANDS:
        print(f"❌ Unknown command: '{cmd}'\n")
        print(HELP)
        sys.exit(1)

    func, _ = COMMANDS[cmd]
    if cmd == "earn":
        if len(sys.argv) < 3:
            print("❌ Usage: earn <amount_usd>")
            sys.exit(1)
        func(sys.argv[2])
    else:
        func()


if __name__ == "__main__":
    main()
