from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from arbitrage import llm


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show current LLM rollout state and KPI readiness."
    )
    parser.add_argument(
        "--window",
        type=int,
        default=200,
        help="Number of latest KPI events to inspect.",
    )
    parser.add_argument(
        "--min-events",
        type=int,
        default=30,
        help="Minimum events required before promotion is allowed.",
    )
    args = parser.parse_args()

    settings = llm.get_effective_canary_settings()
    snapshot = llm.get_kpi_snapshot(max_events=args.window)
    gate_passed, reasons = llm.kpi_gate_passed(snapshot)

    count = int(snapshot.get("count", 0))
    ready_for_gate = count >= args.min_events
    ready_for_promotion = ready_for_gate and gate_passed

    print("LLM Rollout Status")
    print(f" - state_source: {settings.get('source')}")
    print(f" - canary_enabled: {settings.get('canary_enabled')}")
    print(f" - canary_percent: {settings.get('canary_percent')}")
    print(f" - canary_backend: {settings.get('canary_backend')}")
    print(f" - event_count: {count}")
    print(f" - min_events_required: {args.min_events}")
    print(f" - error_rate: {snapshot.get('error_rate', 0.0):.4f}")
    print(f" - p95_latency_ms: {snapshot.get('p95_latency_ms', 0.0):.2f}")
    print(f" - gate_passed: {gate_passed}")
    print(f" - ready_for_gate: {ready_for_gate}")
    print(f" - ready_for_promotion: {ready_for_promotion}")

    if reasons:
        print(f" - gate_fail_reasons: {', '.join(reasons)}")

    if not ready_for_gate:
        print(f"STATUS: WARMUP ({count}/{args.min_events})")
        return 0

    if ready_for_promotion:
        print("STATUS: READY_FOR_PROMOTION")
        return 0

    print("STATUS: GATE_BLOCKED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
