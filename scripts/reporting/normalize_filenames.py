#!/usr/bin/env python3
"""Normalize Genesis Record filenames to the ``Topic_DD-MM-YYYY.md`` convention.

Detects five date-format families, extracts topic and date parts, and
proposes (or executes) renames to the canonical format.

Usage:
    python normalize_filenames.py                        # dry-run, default dir
    python normalize_filenames.py --execute              # apply renames
    python normalize_filenames.py --git                  # use git mv
    python normalize_filenames.py --target-dir some/dir  # custom directory
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MONTH_MAP: dict[str, str] = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
}
MONTH_NAMES = "|".join(MONTH_MAP.keys())

# Regex patterns for each date family (ordered by specificity)
RE_CANONICAL = re.compile(
    r"^[A-Z][A-Za-z0-9]+(?:_[A-Za-z0-9]+)*_\d{2}-\d{2}-\d{4}\.md$"
)
RE_FMT1_DD_MM_YYYY_SUFFIX = re.compile(
    r"^(.+?)_(\d{2})-(\d{2})-(\d{4})\.md$"
)
RE_FMT2_YYYY_MM_DD_PREFIX = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})_(.+)\.md$"
)
RE_FMT3_YYYY_MM_DD_SUFFIX = re.compile(
    r"^(.+?)_(\d{4})-(\d{2})-(\d{2})\.md$"
)
RE_FMT4_MON_D_YYYY_SUFFIX = re.compile(
    rf"^(.+?)_({MONTH_NAMES})(\d{{1,2}})(?:_(\d{{4}}))?\.md$"
)

DEFAULT_TARGET = (
    Path(__file__).resolve().parents[2]
    / "Genesis Record"
    / "10_RAPORTY_DZIALANIA_SYSTEMU"
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class RenameProposal:
    """A proposed rename operation for a single file."""

    original: str
    proposed: str
    date_dd_mm_yyyy: str
    format_family: str


@dataclass
class SkippedFile:
    """A file that was skipped (no date or already correct)."""

    filename: str
    reason: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _title_case_underscores(raw: str) -> str:
    """Convert a raw topic string to ``Title_Case_With_Underscores``.

    Handles kebab-case, ALL_CAPS, mixed separators, and Polish characters.
    """
    # Replace hyphens and spaces with underscores
    normalised = raw.replace("-", "_").replace(" ", "_")
    # Collapse multiple underscores
    normalised = re.sub(r"_+", "_", normalised).strip("_")
    # Title-case each segment
    parts = normalised.split("_")
    titled = [p.capitalize() if p.islower() or p.isupper() else p for p in parts]
    return "_".join(titled)


def _format_date(day: str, month: str, year: str) -> str:
    """Return ``DD-MM-YYYY`` with zero-padded day/month."""
    return f"{day.zfill(2)}-{month.zfill(2)}-{year}"


def analyse_file(filename: str) -> RenameProposal | SkippedFile:
    """Determine the target filename for *filename*.

    Returns a ``RenameProposal`` when a rename is needed, or a
    ``SkippedFile`` when the file is already correct or has no date.
    """
    # Only process .md files
    if not filename.lower().endswith(".md"):
        return SkippedFile(filename=filename, reason="not a markdown file")

    # Already canonical?
    if RE_CANONICAL.match(filename):
        return SkippedFile(filename=filename, reason="already correct")

    # Format 1: Topic_DD-MM-YYYY.md  (correct date position, bad casing)
    m = RE_FMT1_DD_MM_YYYY_SUFFIX.match(filename)
    if m:
        topic_raw, dd, mm, yyyy = m.group(1), m.group(2), m.group(3), m.group(4)
        topic = _title_case_underscores(topic_raw)
        date_str = _format_date(dd, mm, yyyy)
        proposed = f"{topic}_{date_str}.md"
        if proposed == filename:
            return SkippedFile(filename=filename, reason="already correct")
        return RenameProposal(
            original=filename,
            proposed=proposed,
            date_dd_mm_yyyy=date_str,
            format_family="DD-MM-YYYY suffix (casing fix)",
        )

    # Format 2: YYYY-MM-DD_Topic.md
    m = RE_FMT2_YYYY_MM_DD_PREFIX.match(filename)
    if m:
        yyyy, mm, dd, topic_raw = m.group(1), m.group(2), m.group(3), m.group(4)
        topic = _title_case_underscores(topic_raw)
        date_str = _format_date(dd, mm, yyyy)
        return RenameProposal(
            original=filename,
            proposed=f"{topic}_{date_str}.md",
            date_dd_mm_yyyy=date_str,
            format_family="YYYY-MM-DD prefix",
        )

    # Format 3: Topic_YYYY-MM-DD.md
    m = RE_FMT3_YYYY_MM_DD_SUFFIX.match(filename)
    if m:
        topic_raw, yyyy, mm, dd = m.group(1), m.group(2), m.group(3), m.group(4)
        topic = _title_case_underscores(topic_raw)
        date_str = _format_date(dd, mm, yyyy)
        return RenameProposal(
            original=filename,
            proposed=f"{topic}_{date_str}.md",
            date_dd_mm_yyyy=date_str,
            format_family="YYYY-MM-DD suffix",
        )

    # Format 4: Topic_MonDD_YYYY.md  or  Topic_MonDD.md
    m = RE_FMT4_MON_D_YYYY_SUFFIX.match(filename)
    if m:
        topic_raw = m.group(1)
        month_abbr = m.group(2)
        day = m.group(3)
        year = m.group(4) if m.group(4) else "2026"
        mm = MONTH_MAP[month_abbr]
        topic = _title_case_underscores(topic_raw)
        date_str = _format_date(day, mm, year)
        return RenameProposal(
            original=filename,
            proposed=f"{topic}_{date_str}.md",
            date_dd_mm_yyyy=date_str,
            format_family=f"Mon{day}_{year} suffix",
        )

    # Format 5: kebab-case or other with no recognisable date
    return SkippedFile(filename=filename, reason="no date detected")


def scan_directory(target_dir: Path) -> tuple[list[RenameProposal], list[SkippedFile], list[SkippedFile]]:
    """Scan *target_dir* (recursively through subdirectories) for .md files.

    Returns three lists: renames, already_correct, no_date.
    """
    renames: list[RenameProposal] = []
    already_correct: list[SkippedFile] = []
    no_date: list[SkippedFile] = []

    for dirpath, _dirnames, filenames in os.walk(target_dir):
        for fname in sorted(filenames):
            if not fname.lower().endswith(".md"):
                continue
            result = analyse_file(fname)
            if isinstance(result, RenameProposal):
                # Attach relative path info for nested dirs
                rel = Path(dirpath).relative_to(target_dir)
                if str(rel) != ".":
                    result.original = str(rel / result.original)
                    result.proposed = str(rel / result.proposed)
                renames.append(result)
            elif result.reason == "already correct":
                already_correct.append(result)
            else:
                no_date.append(result)

    return renames, already_correct, no_date


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def execute_renames(
    target_dir: Path,
    renames: list[RenameProposal],
    *,
    use_git: bool = False,
) -> tuple[int, int]:
    """Apply rename operations. Returns (success_count, error_count)."""
    successes = 0
    errors = 0

    for r in renames:
        src = target_dir / r.original
        dst = target_dir / r.proposed

        # Safety: do not overwrite existing files
        if dst.exists():
            print(f"  SKIP (target exists): {r.proposed}", file=sys.stderr)
            errors += 1
            continue

        # Ensure parent directory exists
        dst.parent.mkdir(parents=True, exist_ok=True)

        try:
            if use_git:
                subprocess.run(
                    ["git", "mv", str(src), str(dst)],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=str(target_dir),
                )
            else:
                os.rename(src, dst)
            successes += 1
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"  ERROR renaming {r.original}: {exc}", file=sys.stderr)
            errors += 1

    return successes, errors


# ---------------------------------------------------------------------------
# Text report
# ---------------------------------------------------------------------------


def generate_report(
    renames: list[RenameProposal],
    already_correct: list[SkippedFile],
    no_date: list[SkippedFile],
    *,
    dry_run: bool = True,
) -> str:
    """Produce the human-readable normalization report."""
    mode = "DRY RUN" if dry_run else "EXECUTED"
    lines: list[str] = [f"=== FILENAME NORMALIZATION ({mode}) ===\n"]

    # Renames
    verb = "WILL RENAME" if dry_run else "RENAMED"
    lines.append(f"\n{verb} ({len(renames)} files):\n")
    if not renames:
        lines.append("  (none)\n")
    else:
        for r in renames:
            lines.append(f"  {r.original}\n")
            lines.append(f"    -> {r.proposed}\n")
            lines.append(f"       [{r.format_family}]\n")
            lines.append("\n")

    # Already correct
    lines.append(f"ALREADY CORRECT ({len(already_correct)} files):\n")
    for s in already_correct:
        lines.append(f"  v {s.filename}\n")
    if not already_correct:
        lines.append("  (none)\n")

    # No date
    lines.append(f"\nNO DATE DETECTED ({len(no_date)} files):\n")
    for s in no_date:
        lines.append(f"  ! {s.filename}\n")
    if not no_date:
        lines.append("  (none)\n")

    if dry_run and renames:
        lines.append("\nRun with --execute to apply changes.\n")

    return "".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Normalize Genesis Record filenames to Topic_DD-MM-YYYY.md.",
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=DEFAULT_TARGET,
        help="Directory to scan for .md files (default: 10_RAPORTY_DZIALANIA_SYSTEMU).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually rename files (default is dry-run).",
    )
    parser.add_argument(
        "--git",
        action="store_true",
        default=False,
        help="Use 'git mv' instead of os.rename (implies --execute).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    args = parse_args(argv)
    target_dir: Path = args.target_dir.resolve()

    if not target_dir.is_dir():
        print(f"ERROR: directory not found: {target_dir}", file=sys.stderr)
        return 1

    execute = args.execute or args.git
    use_git = args.git

    renames, already_correct, no_date = scan_directory(target_dir)

    # Print the report first
    print(generate_report(renames, already_correct, no_date, dry_run=not execute))

    if execute and renames:
        successes, errors = execute_renames(
            target_dir, renames, use_git=use_git
        )
        method = "git mv" if use_git else "os.rename"
        print(f"\nDone: {successes} renamed, {errors} errors (via {method}).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
