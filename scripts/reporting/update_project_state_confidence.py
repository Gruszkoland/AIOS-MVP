from __future__ import annotations

import argparse
import json
from pathlib import Path

from arbitrage.project_state_confidence import update_project_state_confidence


DEFAULT_PROJECT_STATE_PATH = Path("PROJECT_STATE.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update PROJECT_STATE confidence using dynamic metrics")
    parser.add_argument(
        "--project-state",
        default=str(DEFAULT_PROJECT_STATE_PATH),
        help="Path to PROJECT_STATE.json",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate that confidence values are dynamic (not all equal to 100), without writing",
    )
    args = parser.parse_args()

    project_state_path = Path(args.project_state)
    if not project_state_path.exists():
        print(f"FAIL: file not found: {project_state_path}")
        return 1

    state = json.loads(project_state_path.read_text(encoding="utf-8-sig"))
    updated_state = update_project_state_confidence(state)

    confidences = [agent.get("confidence", 0) for agent in updated_state.get("agents", {}).values()]
    if confidences and all(value == 100 for value in confidences):
        print("FAIL: confidence values are still static (all 100)")
        return 1

    if args.check_only:
        print("OK: PROJECT_STATE confidence is dynamic")
        return 0

    project_state_path.write_text(json.dumps(updated_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("OK: PROJECT_STATE confidence updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
