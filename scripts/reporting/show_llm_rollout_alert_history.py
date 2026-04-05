from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_history(path: Path) -> list[dict]:
    if not path.exists():
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
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Show rollout alert history JSONL")
    parser.add_argument(
        "--history-path",
        default="monitoring/llm_rollout_alert_history.jsonl",
        help="Path to rollout alert history JSONL.",
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=20,
        help="Number of latest history records to show.",
    )
    parser.add_argument(
        "--status",
        default="",
        help="Optional status filter (e.g. READY_FOR_PROMOTION, WARMUP, GATE_BLOCKED, FAIL).",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Return exit code 0 when no history exists.",
    )
    args = parser.parse_args()
    status_filter = args.status.strip().upper()

    path = Path(args.history_path)
    rows = load_history(path)

    if not rows:
        if status_filter:
            print(f"NO_MATCH: status={status_filter} path={path} total_records=0")
            return 0
        print(f"NO_HISTORY: {path}")
        return 0 if args.allow_empty else 1

    filtered_rows = rows
    if status_filter:
        filtered_rows = [r for r in rows if str(r.get("status", "")).upper() == status_filter]

    if not filtered_rows:
        print(
            f"NO_MATCH: status={status_filter} path={path} total_records={len(rows)}"
            if status_filter
            else f"NO_HISTORY: {path}"
        )
        return 0 if status_filter else 1

    tail_rows = filtered_rows[-max(1, args.tail):]
    print("LLM Rollout Alert History")
    print(f" - path: {path}")
    print(f" - total_records: {len(rows)}")
    if status_filter:
        print(f" - status_filter: {status_filter}")
        print(f" - filtered_records: {len(filtered_rows)}")
    print(f" - showing_last: {len(tail_rows)}")

    for row in tail_rows:
        print(
            f" ts={row.get('ts')} iter={row.get('monitor_iteration')} status={row.get('status')}"
            f" ready={row.get('ready_for_promotion')}"
            f" count={row.get('count')}/{row.get('min_events')}"
            f" msg={row.get('message')}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
