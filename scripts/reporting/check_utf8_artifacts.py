#!/usr/bin/env python3
"""
check_utf8_artifacts.py

Guard UTF-8 integrity for 162D markdown artifacts.

Fail conditions:
- Unicode replacement char U+FFFD appears in content.
- Typical mojibake sequences appear (e.g. "Ã…", "Ã³", "â€”", "â€").

Usage:
  python scripts/reporting/check_utf8_artifacts.py
  python scripts/reporting/check_utf8_artifacts.py --files docs/A.md docs/B.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_FILES = [
    "docs/JEDNOSC_162D_MAP.md",
    "docs/JEDNOSC_162D_APPROVED.md",
    "docs/JEDNOSC_162D_REVIEW_BACKLOG.md",
    "docs/JEDNOSC_162D_REVIEW_CHECKLIST.md",
    "docs/JEDNOSC_162D_REVIEW_PENDING.md",
    "docs/JEDNOSC_162D_FINAL.md",
    "docs/162D-DECISION-SPACE.md",
]

# Common signatures produced by encoding mismatch (UTF-8 bytes read as CP1252/Latin-1).
MOJIBAKE_TOKENS = [
    "Ã",
    "â€",
    "â€“",
    "â€”",
    "â€ś",
    "â€ť",
    "â€˜",
    "â€™",
]


def find_utf8_issues(text: str) -> list[str]:
    issues: list[str] = []
    if "\ufffd" in text:
        issues.append("contains U+FFFD replacement character")

    for token in MOJIBAKE_TOKENS:
        if token in text:
            issues.append(f"contains possible mojibake token: {token}")
            break

    return issues


def check_file(path: Path) -> list[str]:
    data = path.read_text(encoding="utf-8")
    return find_utf8_issues(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UTF-8 integrity of markdown artifacts.")
    parser.add_argument("--files", nargs="*", default=DEFAULT_FILES, help="Files to check")
    args = parser.parse_args()

    failed: list[str] = []
    checked = 0

    for raw in args.files:
        p = Path(raw)
        if not p.exists():
            failed.append(f"{p}: file not found")
            continue

        checked += 1
        issues = check_file(p)
        if issues:
            failed.append(f"{p}: " + "; ".join(issues))

    print(f"UTF8_OK_FILES={checked}")

    if failed:
        print("POTENTIAL_MOJIBAKE_START")
        for item in failed:
            print(item)
        print("POTENTIAL_MOJIBAKE_END")
        return 1

    print("POTENTIAL_MOJIBAKE=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
