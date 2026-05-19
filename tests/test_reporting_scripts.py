"""
Tests for scripts/reporting/reconcile_reports.py and normalize_filenames.py.

Uses pytest tmp_path fixture to create mock directory structures so no real
Genesis Record files are touched.
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path so the scripts can be imported
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "reporting"))

from reconcile_reports import (
    FileInfo,
    TopicRecord,
    _extract_date,
    _extract_topic,
    _is_canonical,
    _normalise_topic_key,
    build_topic_map,
    generate_json_report,
    generate_text_report,
    main as reconcile_main,
    scan_directory,
)
from normalize_filenames import (
    RenameProposal,
    SkippedFile,
    analyse_file,
    execute_renames,
    generate_report,
    scan_directory as norm_scan_directory,
)


# ---------------------------------------------------------------------------
# Helper: build a mock Genesis Record directory tree
# ---------------------------------------------------------------------------


def _make_genesis(tmp_path: Path, files: dict[str, list[str]]) -> Path:
    """Create a Genesis Record with ``10_RAPORTY_DZIALANIA_SYSTEMU/{stage}`` dirs.

    Args:
        tmp_path: pytest temporary directory.
        files: mapping of stage name to list of filenames to create.

    Returns:
        The base_dir (Genesis Record root).
    """
    base = tmp_path / "Genesis Record"
    for stage, fnames in files.items():
        stage_dir = base / "10_RAPORTY_DZIALANIA_SYSTEMU" / stage
        stage_dir.mkdir(parents=True, exist_ok=True)
        for fname in fnames:
            (stage_dir / fname).write_text("# placeholder", encoding="utf-8")
    return base


# ═══════════════════════════════════════════════════════════════════════════
# reconcile_reports.py
# ═══════════════════════════════════════════════════════════════════════════


class TestExtractTopic:
    """Unit tests for _extract_topic helper."""

    def test_canonical_dd_mm_yyyy(self):
        assert _extract_topic("Session_Report_15-04-2026.md") == "Session_Report"

    def test_yyyy_mm_dd_prefix(self):
        assert _extract_topic("2026-04-15_Session_Report.md") == "Session_Report"

    def test_yyyy_mm_dd_suffix(self):
        assert _extract_topic("Session_Report_2026-04-15.md") == "Session_Report"

    def test_no_date(self):
        assert _extract_topic("README.md") == "README"


class TestIsCanonical:
    """Tests for _is_canonical: must match Topic_DD-MM-YYYY.md exactly."""

    def test_valid_canonical(self):
        assert _is_canonical("Phase_C_Report_05-04-2026.md") is True

    def test_lowercase_not_canonical(self):
        assert _is_canonical("phase-c-report_05-04-2026.md") is False

    def test_no_date_not_canonical(self):
        assert _is_canonical("README.md") is False

    def test_yyyy_mm_dd_not_canonical(self):
        assert _is_canonical("Report_2026-04-15.md") is False


class TestReconcileScanAndBuild:
    """Integration tests: scan a mock directory and build topic map."""

    def test_complete_triad_detected(self, tmp_path):
        base = _make_genesis(tmp_path, {
            "PLAN": ["Sprint1_05-04-2026.md"],
            "PROGRESS": ["Sprint1_05-04-2026.md"],
            "REPORTS": ["Sprint1_05-04-2026.md"],
        })
        all_files = []
        for stage in ("PLAN", "PROGRESS", "REPORTS"):
            all_files.extend(scan_directory(base, stage))
        topic_map = build_topic_map(all_files)
        assert len(topic_map) == 1
        rec = list(topic_map.values())[0]
        assert rec.is_complete is True

    def test_missing_reports_detected(self, tmp_path):
        base = _make_genesis(tmp_path, {
            "PLAN": ["Feature_X_10-04-2026.md"],
            "PROGRESS": ["Feature_X_10-04-2026.md"],
            "REPORTS": [],
        })
        all_files = []
        for stage in ("PLAN", "PROGRESS", "REPORTS"):
            all_files.extend(scan_directory(base, stage))
        topic_map = build_topic_map(all_files)
        rec = list(topic_map.values())[0]
        assert rec.has_plan is True
        assert rec.has_progress is True
        assert rec.has_reports is False
        assert rec.is_complete is False

    def test_orphaned_reports_detected(self, tmp_path):
        base = _make_genesis(tmp_path, {
            "PLAN": [],
            "PROGRESS": [],
            "REPORTS": ["Orphan_Topic_01-01-2026.md"],
        })
        all_files = []
        for stage in ("PLAN", "PROGRESS", "REPORTS"):
            all_files.extend(scan_directory(base, stage))
        topic_map = build_topic_map(all_files)
        rec = list(topic_map.values())[0]
        assert rec.has_reports is True
        assert rec.has_plan is False

    def test_json_report_structure(self, tmp_path):
        base = _make_genesis(tmp_path, {
            "PLAN": ["Alpha_05-04-2026.md", "Beta_06-04-2026.md"],
            "PROGRESS": ["Alpha_05-04-2026.md"],
            "REPORTS": ["Alpha_05-04-2026.md"],
        })
        all_files = []
        for stage in ("PLAN", "PROGRESS", "REPORTS"):
            all_files.extend(scan_directory(base, stage))
        topic_map = build_topic_map(all_files)
        report = generate_json_report(topic_map, all_files)
        assert "total_topics" in report
        assert report["total_topics"] == 2
        assert "complete_triads" in report
        assert "naming" in report

    def test_text_report_contains_header(self, tmp_path):
        base = _make_genesis(tmp_path, {
            "PLAN": ["Demo_01-01-2026.md"],
            "PROGRESS": [],
            "REPORTS": [],
        })
        all_files = []
        for stage in ("PLAN", "PROGRESS", "REPORTS"):
            all_files.extend(scan_directory(base, stage))
        topic_map = build_topic_map(all_files)
        text = generate_text_report(topic_map, all_files)
        assert "RECONCILIATION REPORT" in text


# ═══════════════════════════════════════════════════════════════════════════
# normalize_filenames.py
# ═══════════════════════════════════════════════════════════════════════════


class TestAnalyseFile:
    """Unit tests for analyse_file: detects date formats and proposes renames."""

    def test_already_canonical_skipped(self):
        result = analyse_file("Phase_C_Report_05-04-2026.md")
        assert isinstance(result, SkippedFile)
        assert result.reason == "already correct"

    def test_yyyy_mm_dd_prefix_renamed(self):
        result = analyse_file("2026-04-15_sprint-report.md")
        assert isinstance(result, RenameProposal)
        assert result.date_dd_mm_yyyy == "15-04-2026"
        assert "Sprint" in result.proposed  # title-cased

    def test_yyyy_mm_dd_suffix_renamed(self):
        result = analyse_file("session_notes_2026-03-20.md")
        assert isinstance(result, RenameProposal)
        assert result.date_dd_mm_yyyy == "20-03-2026"
        assert result.proposed.endswith(".md")

    def test_mon_dd_yyyy_suffix_renamed(self):
        result = analyse_file("Phase_Report_Apr8_2026.md")
        assert isinstance(result, RenameProposal)
        assert result.date_dd_mm_yyyy == "08-04-2026"

    def test_no_date_skipped(self):
        result = analyse_file("README.md")
        assert isinstance(result, SkippedFile)
        assert result.reason == "no date detected"

    def test_non_md_skipped(self):
        result = analyse_file("data.csv")
        assert isinstance(result, SkippedFile)
        assert result.reason == "not a markdown file"


class TestExecuteRenames:
    """Tests for the execute_renames function using tmp_path."""

    def test_renames_applied(self, tmp_path):
        (tmp_path / "old_name_2026-04-15.md").write_text("content", encoding="utf-8")
        proposal = RenameProposal(
            original="old_name_2026-04-15.md",
            proposed="Old_Name_15-04-2026.md",
            date_dd_mm_yyyy="15-04-2026",
            format_family="YYYY-MM-DD suffix",
        )
        successes, errors = execute_renames(tmp_path, [proposal])
        assert successes == 1
        assert errors == 0
        assert (tmp_path / "Old_Name_15-04-2026.md").exists()
        assert not (tmp_path / "old_name_2026-04-15.md").exists()

    def test_skip_when_target_exists(self, tmp_path):
        (tmp_path / "src.md").write_text("a", encoding="utf-8")
        (tmp_path / "dst.md").write_text("b", encoding="utf-8")
        proposal = RenameProposal(
            original="src.md",
            proposed="dst.md",
            date_dd_mm_yyyy="01-01-2026",
            format_family="test",
        )
        successes, errors = execute_renames(tmp_path, [proposal])
        assert successes == 0
        assert errors == 1
        # Original untouched
        assert (tmp_path / "src.md").read_text(encoding="utf-8") == "a"


class TestNormScanDirectory:
    """Integration test for scan_directory in normalize_filenames."""

    def test_scan_mixed_files(self, tmp_path):
        (tmp_path / "Good_Report_01-01-2026.md").write_text("ok", encoding="utf-8")
        (tmp_path / "2026-04-15_bad-name.md").write_text("fix", encoding="utf-8")
        (tmp_path / "no-date-here.md").write_text("skip", encoding="utf-8")
        (tmp_path / "data.csv").write_text("ignore", encoding="utf-8")

        renames, correct, no_date = norm_scan_directory(tmp_path)
        assert len(correct) == 1  # Good_Report_01-01-2026.md
        assert len(renames) == 1  # 2026-04-15_bad-name.md
        # no-date-here.md matches kebab / no date
        assert len(no_date) >= 1
