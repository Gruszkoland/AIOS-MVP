from __future__ import annotations

import argparse
import re
from pathlib import Path


DEFAULT_BASE_DIR = Path(__file__).parents[2] / "Genesis Record" / "10_RAPORTY_DZIALANIA_SYSTEMU"
LAST_SESSION_FILENAME = ".session_reports_last.txt"

REQUIRED_PLAN = [
    "## Cel glowny",
    "## Kroki wykonawcze",
]

REQUIRED_PROGRESS = [
    "## Wpisy dzialan (append-only)",
    "## Stan krokow",
]

REQUIRED_REPORT = [
    "## Co wykonano",
    "## Co pozostalo",
    "## Co blokuje",
    "## Uzyskane efekty",
    "## Rekomendacje kolejnych krokow",
    "## Mikro-streszczenie",
]

STATUS_MARKERS = ["status: planned", "status: in-progress", "status: done", "status: blocked"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_required_sections(text: str, required: list[str]) -> list[str]:
    return [section for section in required if section not in text]


def check_micro_summary(text: str) -> list[str]:
    issues: list[str] = []
    marker = "## Mikro-streszczenie"
    if marker not in text:
        return ["Brak sekcji Mikro-streszczenie."]

    tail = text.split(marker, 1)[1]
    bullets = [line.strip()[1:].strip() for line in tail.splitlines() if line.strip().startswith("-")]

    if len(bullets) > 9:
        issues.append("Mikro-streszczenie ma wiecej niz 9 punktow.")

    for idx, bullet in enumerate(bullets, start=1):
        words = re.findall(r"\b\w+\b", bullet)
        if len(words) != 3:
            issues.append(f"Punkt {idx} mikro-streszczenia nie ma dokladnie 3 slow.")

    return issues


def validate_triplet(base_dir: Path, filename: str) -> list[str]:
    errors: list[str] = []

    plan_file = base_dir / "PLAN" / filename
    progress_file = base_dir / "PROGRESS" / filename
    report_file = base_dir / "REPORTS" / filename

    for file_path in (plan_file, progress_file, report_file):
        if not file_path.exists():
            errors.append(f"Brak pliku: {file_path}")

    if errors:
        return errors

    plan_text = read_text(plan_file)
    progress_text = read_text(progress_file)
    report_text = read_text(report_file)

    missing_plan = check_required_sections(plan_text, REQUIRED_PLAN)
    missing_progress = check_required_sections(progress_text, REQUIRED_PROGRESS)
    missing_report = check_required_sections(report_text, REQUIRED_REPORT)

    for section in missing_plan:
        errors.append(f"PLAN: brak sekcji {section}")
    for section in missing_progress:
        errors.append(f"PROGRESS: brak sekcji {section}")
    for section in missing_report:
        errors.append(f"REPORTS: brak sekcji {section}")

    if not any(marker in plan_text for marker in STATUS_MARKERS):
        errors.append("PLAN: brak statusow krokow (planned/in-progress/done/blocked).")

    errors.extend(check_micro_summary(report_text))

    return errors


def find_latest_triplet(base_dir: Path) -> str | None:
    state_file = base_dir / LAST_SESSION_FILENAME
    if state_file.exists():
        value = state_file.read_text(encoding="utf-8").strip()
        if value:
            return value

    plan_files = sorted((base_dir / "PLAN").glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not plan_files:
        return None
    # New format: Title_Case_Topic_DD-MM-YYYY.md
    # Old format: YYYY-MM-DD_slug_shortid.md
    # Both are valid — just return the newest by mtime
    return plan_files[0].name


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PLAN/PROGRESS/REPORTS required sections.")
    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Base path containing PLAN/PROGRESS/REPORTS directories",
    )
    parser.add_argument(
        "--filename",
        default=None,
        help="Exact filename to validate; when omitted, latest PLAN file is used",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    filename = args.filename or find_latest_triplet(base_dir)

    if not filename:
        print("FAIL: Nie znaleziono zadnego pliku do walidacji.")
        return 1

    errors = validate_triplet(base_dir, filename)
    if errors:
        print(f"FAIL: Walidacja nieudana dla {filename}")
        for err in errors:
            print(f" - {err}")
        return 1

    print(f"OK: Walidacja poprawna dla {filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
