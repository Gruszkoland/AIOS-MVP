"""Quick test for all arbitrage modules."""
from arbitrage.database import init_db
from arbitrage.config import get_active_llm_backend
from arbitrage.scout import run_scout
from arbitrage.analyzer import analyze_job
from arbitrage.bidder import create_bid

init_db()
print("[OK] Database initialized")
print("[OK] LLM backend:", get_active_llm_backend())

result = run_scout(use_mock=True)
print("[OK] Scout: new_jobs={}, mode={}".format(result["new_jobs"], result["mode"]))

if result["jobs"]:
    job = result["jobs"][0]
    analysis = analyze_job(job)
    print("[OK] Analyzer: score={}, profit=${}".format(analysis["score"], analysis["est_profit"]))
    bid = create_bid(job, analysis)
    print("[OK] Bidder: bid id={}, approved={}".format(bid["id"], bid["approved"]))

print("\n=== All modules OK ===")
