from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Show rollout alert file")
    parser.add_argument(
        "--alert-path",
        default="monitoring/llm_rollout_alert.json",
        help="Path to rollout alert JSON file.",
    )
    args = parser.parse_args()

    path = Path(args.alert_path)
    if not path.exists():
        print(f"NO_ALERT_FILE: {path}")
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"INVALID_ALERT_FILE: {path}")
        return 1

    print("LLM Rollout Alert")
    print(f" - path: {path}")
    print(f" - ts: {data.get('ts')}")
    print(f" - status: {data.get('status')}")
    print(f" - ready_for_promotion: {data.get('ready_for_promotion')}")
    print(f" - count: {data.get('count')}")
    print(f" - min_events: {data.get('min_events')}")
    print(f" - message: {data.get('message')}")

    reasons = data.get("reasons")
    if reasons:
        print(f" - reasons: {', '.join(reasons)}")

    promotion = data.get("promotion")
    if isinstance(promotion, dict):
        print(" - promotion:")
        print(f"   - enabled: {promotion.get('enabled')}")
        print(f"   - percent: {promotion.get('percent')}")
        print(f"   - backend: {promotion.get('backend')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
