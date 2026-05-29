from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_STATE_FILE = REPO_ROOT / "PROJECT_STATE.json"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def compute_confidence(success_rate: float, freshness_hours: float, completed_tasks: int) -> float:
    freshness_score = clamp(1.0 - (freshness_hours / 72.0), 0.0, 1.0)
    task_score = clamp(completed_tasks / 20.0, 0.0, 1.0)
    return round(clamp(success_rate * 70 + freshness_score * 20 + task_score * 10, 0.0, 100.0), 2)


def main() -> int:
    if not PROJECT_STATE_FILE.exists():
        print("update_project_confidence: missing PROJECT_STATE.json")
        return 2

    data = json.loads(PROJECT_STATE_FILE.read_text(encoding="utf-8"))
    metrics = data.setdefault("metrics", {})

    success_rate = float(metrics.get("success_rate", 0.90))
    freshness_hours = float(metrics.get("activity_freshness_hours", 12.0))
    completed_tasks = int(metrics.get("completed_tasks", 5))

    confidence = compute_confidence(success_rate, freshness_hours, completed_tasks)
    data["confidence_score"] = confidence
    data["last_updated"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    PROJECT_STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"update_project_confidence: confidence_score={confidence}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
