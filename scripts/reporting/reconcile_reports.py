#!/usr/bin/env python3
"""Reconcile Genesis Record PLAN -> PROGRESS -> REPORTS workflow.

Scans the three workflow directories under 10_RAPORTY_DZIALANIA_SYSTEMU and
reports which topics have complete triads, which are missing stages, and
which filenames violate the canonical naming convention.

Usage:
    python reconcile_reports.py
    python reconcile_reports.py --json reconciliation.json
    python reconcile_reports.py --base-dir "path/to/Genesis Record"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CANONICAL_PATTERN = re.compile(
    r"^[A-Z][A-Za-z0-9]+(?:_[A-Za-z0-9]+)*_\d{2}-\d{2}-\d{4}\.md$"
)

DATE_SUFFIX_DD_MM_YYYY = re.compile(r"_(\d{2}-\d{2}-\d{4})\.md$")
DATE_SUFFIX_YYYY_MM_DD = re.compile(r"_(\d{4}-\d{2}-\d{2})\.md$")
DATE_PREFIX_YYYY_MM_DD = re.compile(r"^(\d{4}-\d{2}-\d{2})_(.+)\.md$")
DATE_SUFFIX_MON_D_YYYY = re.compile(
    r"_(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{1,2})(?:_(\d{4}))?\.md$"
)
KEBAB_NO_DATE = re.compile(r"^[a-z][a-z0-9]+(?:-[a-z0-9]+)+\.md$")

STAGES = ("PLAN", "PROGRESS", "REPORTS")

DEFAULT_BASE = Path(__file__).resolve().parents[2] / "Genesis Record"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class FileInfo:
    """Metadata extracted from a single report filename."""

    filename: str
    stage: str
    topic: str
    date_str: str | None
    is_canonical: bool


@dataclass
class TopicRecord:
    """Aggregated information for one logical topic across stages."""

    topic: str
    stages: dict[str, list[str]] = field(default_factory=dict)

    @property
    def has_plan(self) -> bool:
        return bool(self.stages.get("PLAN"))

    @property
    def has_progress(self) -> bool:
        return bool(self.stages.get("PROGRESS"))

    @property
    def has_reports(self) -> bool:
        return bool(self.stages.get("REPORTS"))

    @property
    def is_complete(self) -> bool:
        return self.has_plan and self.has_progress and self.has_reports


# ---------------------------------------------------------------------------
# Topic extraction helpers
# ---------------------------------------------------------------------------


def _extract_topic(filename: str) -> str:
    """Strip date suffix and extension to get a normalised topic key.

    Handles multiple date formats so that the same logical topic can be
    matched across PLAN / PROGRESS / REPORTS even when the date format
    differs between directories.
    """
    stem = Path(filename).stem

    # Format 1: Topic_DD-MM-YYYY
    m = DATE_SUFFIX_DD_MM_YYYY.search(filename)
    if m:
        return stem[: stem.rfind(m.group(1)) - 1]

    # Format 2: YYYY-MM-DD_Topic
    m = DATE_PREFIX_YYYY_MM_DD.match(filename)
    if m:
        return m.group(2)

    # Format 3: Topic_YYYY-MM-DD
    m = DATE_SUFFIX_YYYY_MM_DD.search(filename)
    if m:
        return stem[: stem.rfind(m.group(1)) - 1]

    # Format 4: Topic_AprDD_YYYY  or  Topic_AprDD
    m = DATE_SUFFIX_MON_D_YYYY.search(filename)
    if m:
        suffix_start = filename.index(m.group(0))
        return stem[: suffix_start - len(Path(filename).suffix)]

    # No date -- use the whole stem, normalised
    return stem


def _normalise_topic_key(raw: str) -> str:
    """Produce a lowercase, underscore-separated key for fuzzy matching."""
    key = raw.replace("-", "_").replace(" ", "_")
    key = re.sub(r"_+", "_", key).strip("_")
    return key.lower()


def _extract_date(filename: str) -> str | None:
    """Return a date string if one can be parsed, else None."""
    m = DATE_SUFFIX_DD_MM_YYYY.search(filename)
    if m:
        return m.group(1)

    m = DATE_PREFIX_YYYY_MM_DD.match(filename)
    if m:
        parts = m.group(1).split("-")
        return f"{parts[2]}-{parts[1]}-{parts[0]}"

    m = DATE_SUFFIX_YYYY_MM_DD.search(filename)
    if m:
        parts = m.group(1).split("-")
        return f"{parts[2]}-{parts[1]}-{parts[0]}"

    m = DATE_SUFFIX_MON_D_YYYY.search(filename)
    if m:
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
        }
        month = month_map[m.group(1)]
        day = m.group(2).zfill(2)
        year = m.group(3) if m.group(3) else "2026"
        return f"{day}-{month}-{year}"

    return None


def _is_canonical(filename: str) -> bool:
    """Check whether *filename* matches ``Topic_DD-MM-YYYY.md``."""
    return bool(CANONICAL_PATTERN.match(filename))


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


def scan_directory(base_dir: Path, stage: str) -> list[FileInfo]:
    """Return ``FileInfo`` records for every ``.md`` file in *stage*."""
    stage_dir = base_dir / "10_RAPORTY_DZIALANIA_SYSTEMU" / stage
    if not stage_dir.is_dir():
        return []

    results: list[FileInfo] = []
    for path in sorted(stage_dir.iterdir()):
        if path.suffix.lower() != ".md":
            continue
        fname = path.name
        results.append(
            FileInfo(
                filename=fname,
                stage=stage,
                topic=_extract_topic(fname),
                date_str=_extract_date(fname),
                is_canonical=_is_canonical(fname),
            )
        )
    return results


def build_topic_map(
    all_files: list[FileInfo],
) -> dict[str, TopicRecord]:
    """Group files by normalised topic key."""
    topic_map: dict[str, TopicRecord] = {}
    for fi in all_files:
        key = _normalise_topic_key(fi.topic)
        if key not in topic_map:
            topic_map[key] = TopicRecord(topic=fi.topic)
        record = topic_map[key]
        record.stages.setdefault(fi.stage, []).append(fi.filename)
    return topic_map


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _section(title: str, items: list[str], marker: str = " ") -> str:
    """Format a report section with a title and indented items."""
    lines = [f"\n{title} ({len(items)}):\n"]
    if not items:
        lines.append("  (none)\n")
    else:
        for item in items:
            lines.append(f"  {marker} {item}\n")
    return "".join(lines)


def generate_text_report(
    topic_map: dict[str, TopicRecord],
    all_files: list[FileInfo],
) -> str:
    """Produce the human-readable reconciliation report."""
    complete: list[str] = []
    missing_progress: list[str] = []
    missing_reports: list[str] = []
    orphaned_reports: list[str] = []
    plan_only: list[str] = []

    for key in sorted(topic_map):
        rec = topic_map[key]
        if rec.is_complete:
            complete.append(f"{rec.topic} -- PLAN + PROGRESS + REPORTS")
        elif rec.has_plan and not rec.has_progress:
            missing_progress.append(f"{rec.topic} -- has PLAN, no PROGRESS")
        elif rec.has_progress and not rec.has_reports:
            missing_reports.append(
                f"{rec.topic} -- has PROGRESS, no REPORTS"
            )
        elif rec.has_reports and not rec.has_plan and not rec.has_progress:
            orphaned_reports.append(f"{rec.topic} -- REPORTS only, no PLAN")
        elif rec.has_plan and rec.has_progress and not rec.has_reports:
            missing_reports.append(
                f"{rec.topic} -- has PLAN + PROGRESS, no REPORTS"
            )
        elif not rec.has_plan and rec.has_progress:
            plan_only.append(f"{rec.topic} -- PROGRESS only, no PLAN")

    # Naming convention
    canonical_count = sum(1 for f in all_files if f.is_canonical)
    non_canonical = [f for f in all_files if not f.is_canonical]
    total = len(all_files)

    # Detect format families among non-canonical files
    format_families: dict[str, int] = {}
    for f in non_canonical:
        if DATE_PREFIX_YYYY_MM_DD.match(f.filename):
            family = "YYYY-MM-DD_Topic prefix"
        elif DATE_SUFFIX_YYYY_MM_DD.search(f.filename):
            family = "Topic_YYYY-MM-DD suffix"
        elif DATE_SUFFIX_MON_D_YYYY.search(f.filename):
            family = "Topic_MonDD_YYYY suffix"
        elif KEBAB_NO_DATE.match(f.filename):
            family = "kebab-case-no-date"
        else:
            family = "other / no date"
        format_families[family] = format_families.get(family, 0) + 1

    parts: list[str] = []
    parts.append("=== GENESIS RECORD RECONCILIATION REPORT ===\n")

    total_topics = len(topic_map)
    parts.append(
        _section(
            f"COMPLETE TRIADS ({len(complete)}/{total_topics})",
            complete,
            marker="v",
        )
    )
    parts.append(
        _section("MISSING PROGRESS", missing_progress, marker="!")
    )
    parts.append(
        _section("MISSING REPORTS", missing_reports, marker="!")
    )
    parts.append(
        _section("ORPHANED REPORTS", orphaned_reports, marker="x")
    )
    if plan_only:
        parts.append(
            _section("PROGRESS WITHOUT PLAN", plan_only, marker="?")
        )

    parts.append(f"\nNAMING CONVENTION:\n")
    parts.append(f"  v Compliant: {canonical_count}/{total} files\n")
    parts.append(
        f"  x Non-compliant: {len(non_canonical)}/{total} files"
        f" ({len(format_families)} different formats detected)\n"
    )
    if format_families:
        for family, count in sorted(
            format_families.items(), key=lambda x: -x[1]
        ):
            parts.append(f"      - {family}: {count} files\n")

    return "".join(parts)


def generate_json_report(
    topic_map: dict[str, TopicRecord],
    all_files: list[FileInfo],
) -> dict[str, Any]:
    """Produce a machine-readable reconciliation report."""
    complete: list[dict[str, Any]] = []
    missing_progress: list[dict[str, Any]] = []
    missing_reports: list[dict[str, Any]] = []
    orphaned_reports: list[dict[str, Any]] = []

    for key in sorted(topic_map):
        rec = topic_map[key]
        entry: dict[str, Any] = {
            "topic": rec.topic,
            "stages": {
                stage: rec.stages.get(stage, []) for stage in STAGES
            },
        }
        if rec.is_complete:
            complete.append(entry)
        elif rec.has_plan and not rec.has_progress:
            missing_progress.append(entry)
        elif rec.has_reports and not rec.has_plan and not rec.has_progress:
            orphaned_reports.append(entry)
        else:
            if not rec.has_reports:
                missing_reports.append(entry)

    canonical_count = sum(1 for f in all_files if f.is_canonical)

    return {
        "total_topics": len(topic_map),
        "total_files": len(all_files),
        "complete_triads": complete,
        "missing_progress": missing_progress,
        "missing_reports": missing_reports,
        "orphaned_reports": orphaned_reports,
        "naming": {
            "compliant": canonical_count,
            "non_compliant": len(all_files) - canonical_count,
            "non_compliant_files": [
                {"filename": f.filename, "stage": f.stage}
                for f in all_files
                if not f.is_canonical
            ],
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Reconcile PLAN / PROGRESS / REPORTS in Genesis Record.",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=DEFAULT_BASE,
        help="Path to the Genesis Record root directory.",
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        type=Path,
        default=None,
        help="Write machine-readable JSON report to this path.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    args = parse_args(argv)
    base_dir: Path = args.base_dir.resolve()

    raporty_dir = base_dir / "10_RAPORTY_DZIALANIA_SYSTEMU"
    if not raporty_dir.is_dir():
        print(
            f"ERROR: directory not found: {raporty_dir}",
            file=sys.stderr,
        )
        return 1

    # Scan all three stages
    all_files: list[FileInfo] = []
    for stage in STAGES:
        all_files.extend(scan_directory(base_dir, stage))

    if not all_files:
        print("No .md files found in PLAN / PROGRESS / REPORTS.")
        return 0

    topic_map = build_topic_map(all_files)

    # Text report to stdout
    print(generate_text_report(topic_map, all_files))

    # Optional JSON output
    if args.json_path is not None:
        report = generate_json_report(topic_map, all_files)
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nJSON report written to: {args.json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
