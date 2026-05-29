from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = REPO_ROOT / "VERSION"
MANIFEST_FILE = REPO_ROOT / "MANIFEST.md"
PROJECT_STATE_FILE = REPO_ROOT / "PROJECT_STATE.json"


def read_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def sync_manifest(version: str) -> bool:
    text = MANIFEST_FILE.read_text(encoding="utf-8")
    updated = re.sub(r"(\*\*Version:\*\*\s*)([^|]+)", rf"\g<1>{version}", text, count=1)
    if updated != text:
        MANIFEST_FILE.write_text(updated, encoding="utf-8")
        return True
    return False


def sync_project_state(version: str) -> bool:
    data = {}
    if PROJECT_STATE_FILE.exists():
        data = json.loads(PROJECT_STATE_FILE.read_text(encoding="utf-8"))

    changed = data.get("version") != version
    data["version"] = version
    data["last_updated"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if "confidence_model" not in data:
        data["confidence_model"] = {
            "mode": "dynamic",
            "inputs": ["success_rate", "activity_freshness_hours", "completed_tasks"],
            "formula": "round(min(100, max(0, success_rate*70 + freshness_score*20 + task_score*10)), 2)",
        }
        changed = True

    PROJECT_STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    if not VERSION_FILE.exists() or not MANIFEST_FILE.exists():
        print("sync_version_state: missing VERSION or MANIFEST.md")
        return 2

    version = read_version()
    manifest_changed = sync_manifest(version)
    state_changed = sync_project_state(version)

    if manifest_changed or state_changed:
        print("sync_version_state: files updated")
    else:
        print("sync_version_state: already in sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
