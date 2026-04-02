from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from arbitrage import llm


def write_alert(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check LLM KPI gate for canary rollout (PASS/FAIL)."
    )
    parser.add_argument(
        "--window",
        type=int,
        default=200,
        help="Number of latest KPI events to evaluate.",
    )
    parser.add_argument(
        "--min-events",
        type=int,
        default=30,
        help="Minimum events required to make a rollout decision.",
    )
    parser.add_argument(
        "--rollback-on-fail",
        action="store_true",
        help="Force canary rollback (0%) when gate fails.",
    )
    parser.add_argument(
        "--reset-rollout-state",
        action="store_true",
        help="Delete runtime rollout state and return to ENV defaults.",
    )
    parser.add_argument(
        "--warmup-ok",
        action="store_true",
        help="Treat insufficient events as warmup (PENDING) and return exit code 0.",
    )
    parser.add_argument(
        "--promote-on-pass",
        action="store_true",
        help="Promote canary rollout when KPI gate passes.",
    )
    parser.add_argument(
        "--promote-percent",
        type=float,
        default=5.0,
        help="Canary percentage to set when promotion is enabled.",
    )
    parser.add_argument(
        "--promote-backend",
        default="openrouter",
        help="Backend for promoted canary traffic: openrouter|ollama.",
    )
    parser.add_argument(
        "--alert-on-ready",
        action="store_true",
        help="Write rollout alert JSON file with current gate status.",
    )
    parser.add_argument(
        "--alert-path",
        default="monitoring/llm_rollout_alert.json",
        help="Path to rollout alert JSON file.",
    )
    args = parser.parse_args()
    alert_path = Path(args.alert_path)

    if args.reset_rollout_state:
        state_path = Path(llm.LLM_ROLLOUT_STATE_PATH)
        if state_path.exists():
            state_path.unlink()
            print(f"OK: removed rollout state override at {state_path}")
        else:
            print(f"OK: no rollout state override found at {state_path}")

    settings = llm.get_effective_canary_settings()
    print("Canary settings")
    print(f" - source: {settings.get('source')}")
    print(f" - enabled: {settings.get('canary_enabled')}")
    print(f" - percent: {settings.get('canary_percent')}")
    print(f" - backend: {settings.get('canary_backend')}")

    snapshot = llm.get_kpi_snapshot(max_events=args.window)
    count = int(snapshot.get("count", 0))

    print("LLM KPI Snapshot")
    print(f" - count: {count}")
    print(f" - error_rate: {snapshot.get('error_rate', 0.0):.4f}")
    print(f" - p95_latency_ms: {snapshot.get('p95_latency_ms', 0.0):.2f}")
    print(f" - threshold_error_rate: {llm.LLM_KPI_MAX_ERROR_RATE:.4f}")
    print(f" - threshold_p95_ms: {llm.LLM_KPI_MAX_P95_MS:.2f}")

    if count < args.min_events:
        if args.rollback_on_fail and not args.warmup_ok:
            rollback_state = llm.force_canary_rollback(reason="kpi_gate_failed:insufficient_events")
            print("ROLLBACK: canary disabled")
            print(f" - state_file: {llm.LLM_ROLLOUT_STATE_PATH}")
            print(f" - reason: {rollback_state.get('reason')}")
        if args.warmup_ok:
            if args.alert_on_ready:
                write_alert(
                    alert_path,
                    {
                        "ts": int(time.time()),
                        "status": "WARMUP",
                        "ready_for_promotion": False,
                        "count": count,
                        "min_events": args.min_events,
                        "message": f"insufficient events ({count} < {args.min_events})",
                    },
                )
            print(f"PENDING: insufficient events ({count} < {args.min_events})")
            return 2
        if args.alert_on_ready:
            write_alert(
                alert_path,
                {
                    "ts": int(time.time()),
                    "status": "FAIL",
                    "ready_for_promotion": False,
                    "count": count,
                    "min_events": args.min_events,
                    "message": f"insufficient events ({count} < {args.min_events})",
                },
            )
        print(f"FAIL: insufficient events ({count} < {args.min_events})")
        return 1

    passed, reasons = llm.kpi_gate_passed(snapshot)
    if passed:
        if args.promote_on_pass:
            promoted = llm.set_canary_rollout(
                percent=args.promote_percent,
                backend=args.promote_backend,
                reason="kpi_gate_passed",
            )
            print("PROMOTION: canary updated")
            print(f" - enabled: {promoted.get('canary_enabled')}")
            print(f" - percent: {promoted.get('canary_percent')}")
            print(f" - backend: {promoted.get('canary_backend')}")
        if args.alert_on_ready:
            write_alert(
                alert_path,
                {
                    "ts": int(time.time()),
                    "status": "READY_FOR_PROMOTION",
                    "ready_for_promotion": True,
                    "count": count,
                    "min_events": args.min_events,
                    "message": "KPI gate passed and promotion conditions met",
                    "promotion": {
                        "enabled": bool(args.promote_on_pass),
                        "percent": args.promote_percent,
                        "backend": args.promote_backend,
                    },
                },
            )
        print("PASS: KPI gate passed")
        return 0

    if args.rollback_on_fail:
        rollback_state = llm.force_canary_rollback(reason=f"kpi_gate_failed:{','.join(reasons)}")
        print("ROLLBACK: canary disabled")
        print(f" - state_file: {llm.LLM_ROLLOUT_STATE_PATH}")
        print(f" - reason: {rollback_state.get('reason')}")

    if args.alert_on_ready:
        write_alert(
            alert_path,
            {
                "ts": int(time.time()),
                "status": "GATE_BLOCKED",
                "ready_for_promotion": False,
                "count": count,
                "min_events": args.min_events,
                "message": f"kpi gate failed ({', '.join(reasons)})",
                "reasons": reasons,
            },
        )

    print(f"FAIL: KPI gate failed ({', '.join(reasons)})")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
