from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from arbitrage import llm


def tail_jsonl(path: Path, limit: int) -> list[dict]:
    if limit <= 0 or not path.exists():
        return []

    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-limit:]


def fmt_bool(v: bool) -> str:
    return "yes" if v else "no"


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified LLM rollout + KPI dashboard")
    parser.add_argument("--window", type=int, default=200, help="KPI snapshot window size")
    parser.add_argument("--min-events", type=int, default=30, help="Minimum events before gate")
    parser.add_argument("--tail", type=int, default=5, help="How many latest JSONL events to show")
    args = parser.parse_args()

    settings = llm.get_effective_canary_settings()
    snapshot = llm.get_kpi_snapshot(max_events=args.window)
    passed, reasons = llm.kpi_gate_passed(snapshot)

    count = int(snapshot.get("count", 0))
    ready_for_gate = count >= args.min_events
    ready_for_promotion = ready_for_gate and passed

    kpi_path = Path(llm.LLM_KPI_LOG_PATH)
    rollout_path = Path(llm.LLM_ROLLOUT_STATE_PATH)
    latest_events = tail_jsonl(kpi_path, args.tail)

    print("=== LLM Ops Dashboard ===")
    print("[Rollout]")
    print(f" source: {settings.get('source')}")
    print(f" canary_enabled: {fmt_bool(bool(settings.get('canary_enabled')))}")
    print(f" canary_percent: {settings.get('canary_percent')}")
    print(f" canary_backend: {settings.get('canary_backend')}")
    print(f" rollout_state_path: {rollout_path}")
    print()

    print("[KPI]")
    print(f" events: {count}/{args.min_events} (window={args.window})")
    print(f" error_rate: {snapshot.get('error_rate', 0.0):.4f}")
    print(f" p95_latency_ms: {snapshot.get('p95_latency_ms', 0.0):.2f}")
    print(f" gate_passed: {fmt_bool(passed)}")
    print(f" ready_for_gate: {fmt_bool(ready_for_gate)}")
    print(f" ready_for_promotion: {fmt_bool(ready_for_promotion)}")
    if reasons:
        print(f" gate_fail_reasons: {', '.join(reasons)}")
    print(f" kpi_log_path: {kpi_path}")
    print()

    if not ready_for_gate:
        status = f"WARMUP ({count}/{args.min_events})"
    elif ready_for_promotion:
        status = "READY_FOR_PROMOTION"
    else:
        status = "GATE_BLOCKED"
    print(f"[Status] {status}")
    print()

    print(f"[Last {len(latest_events)} KPI Events]")
    if not latest_events:
        print(" no events")
    else:
        for e in latest_events:
            ts = e.get("ts", "-")
            selected = e.get("selected_backend", "-")
            success = e.get("success", False)
            latency = e.get("latency_ms", 0.0)
            canary = e.get("canary", False)
            err = e.get("error_kind", "")
            print(
                f" ts={ts} backend={selected} canary={canary} success={success} latency_ms={latency}"
                + (f" error={err}" if err else "")
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
