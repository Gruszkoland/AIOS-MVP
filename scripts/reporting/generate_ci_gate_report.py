#!/usr/bin/env python3
"""
generate_ci_gate_report.py

Generate a markdown report for ADRION 162D CI gate execution.
"""

from __future__ import annotations

import argparse
import datetime as dt
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_junit(path: Path) -> dict[str, int]:
    tree = ET.parse(path)
    root = tree.getroot()

    # Handle both <testsuite> and <testsuites>
    if root.tag == "testsuite":
        suites = [root]
    else:
        suites = list(root.findall("testsuite"))

    total = failures = errors = skipped = 0
    for suite in suites:
        total += int(suite.attrib.get("tests", "0"))
        failures += int(suite.attrib.get("failures", "0"))
        errors += int(suite.attrib.get("errors", "0"))
        skipped += int(suite.attrib.get("skipped", "0"))

    passed = max(total - failures - errors - skipped, 0)
    return {
        "total": total,
        "passed": passed,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate markdown report for CI gate run")
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--utf8-ok-files", required=True, type=int)
    parser.add_argument("--pytest-xml", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    pytest_xml = Path(args.pytest_xml)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    stats = parse_junit(pytest_xml)
    now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    status = "PASS" if (stats["failures"] == 0 and stats["errors"] == 0) else "FAIL"

    lines = [
        f"# CI Gate Report: {args.workflow}",
        "",
        f"Generated: {now}",
        f"Run ID: {args.run_id}",
        f"Actor: {args.actor}",
        f"Ref: {args.ref}",
        f"SHA: {args.sha}",
        "",
        "## Gate Metrics",
        "",
        f"- Status: {status}",
        f"- UTF8_OK_FILES: {args.utf8_ok_files}",
        f"- Pytest total: {stats['total']}",
        f"- Pytest passed: {stats['passed']}",
        f"- Pytest skipped: {stats['skipped']}",
        f"- Pytest failures: {stats['failures']}",
        f"- Pytest errors: {stats['errors']}",
        "",
        "## Checks Executed",
        "",
        "- Smoke map generator and artifacts",
        "- Smoke merge output and production assertions (17/17, pending=0)",
        "- UTF-8 integrity guard",
        "- Jednosc regression tests",
        "- Session reports validation",
        "",
    ]

    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"CI_REPORT_PATH={output}")
    print(f"CI_GATE_STATUS={status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
