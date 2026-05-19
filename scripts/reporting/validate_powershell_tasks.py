from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_TASKS_PATH = Path(".vscode/tasks.json")
REQUIRED_PREFIX = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
REQUIRED_ARGS = ["-NoProfile", "-ExecutionPolicy", "Bypass"]


def is_powershell_task(task: dict) -> bool:
    command = str(task.get("command", "")).strip().lower()
    return "powershell" in command


def validate_task(task: dict, index: int) -> list[str]:
    issues: list[str] = []
    label = str(task.get("label", f"task#{index}"))
    command = str(task.get("command", "")).strip()
    args = [str(arg) for arg in task.get("args", [])]

    if command != REQUIRED_PREFIX:
        issues.append(f"{label}: command must be '{REQUIRED_PREFIX}'")

    for req in REQUIRED_ARGS:
        if req not in args:
            issues.append(f"{label}: missing required arg {req}")

    # At least one execution mode should be explicit.
    if "-Command" not in args and "-File" not in args:
        issues.append(f"{label}: missing execution mode arg (-Command or -File)")

    return issues


def validate_tasks_file(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = data.get("tasks", [])

    errors: list[str] = []
    for idx, task in enumerate(tasks, start=1):
        if is_powershell_task(task):
            errors.extend(validate_task(task, idx))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PowerShell task hardening in .vscode/tasks.json")
    parser.add_argument("--tasks-file", default=str(DEFAULT_TASKS_PATH), help="Path to tasks.json")
    args = parser.parse_args()

    tasks_path = Path(args.tasks_file)
    if not tasks_path.exists():
        print(f"FAIL: tasks file not found: {tasks_path}")
        return 1

    errors = validate_tasks_file(tasks_path)
    if errors:
        print("FAIL: PowerShell task validation errors detected")
        for err in errors:
            print(f" - {err}")
        return 1

    print("OK: PowerShell task validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())