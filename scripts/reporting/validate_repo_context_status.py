from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET = REPO_ROOT / "REPO_CONTEXT_STATUS.txt"

REQUIRED_HEADERS = [
    "REPO_GOAL",
    "DEPLOYMENT_PLAN",
    "CHANGELOG_LIVE",
    "CURRENT_RISKS",
    "NEXT_ACTIONS",
    "LAST_VERIFIED",
]


def main() -> int:
    if not TARGET.exists():
        print("validate_repo_context_status: missing REPO_CONTEXT_STATUS.txt")
        return 2

    content = TARGET.read_text(encoding="utf-8", errors="replace")

    missing = [header for header in REQUIRED_HEADERS if header not in content]
    if missing:
        print("validate_repo_context_status: missing headers:")
        for header in missing:
            print(f"- {header}")
        return 1

    print("validate_repo_context_status: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
