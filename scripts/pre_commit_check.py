#!/usr/bin/env python3
"""
ADRION 369 — Pre-commit quality gate
Run: python scripts/pre_commit_check.py
All checks must pass before committing. Used as git pre-commit hook.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
PYTHON_DIRS = ["arbitrage", "uap", "tests"]
COVERAGE_THRESHOLD = 80


def run(cmd: list[str], label: str) -> bool:
    """Run a command and return True if it passed."""
    print(f"\n{'─' * 60}")
    print(f"  ▶  {label}")
    print(f"{'─' * 60}")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"\n  ✗  FAILED: {label}\n")
        return False
    print(f"\n  ✓  PASSED: {label}")
    return True


def main() -> int:
    results: dict[str, bool] = {}

    # 1. Ruff lint
    results["Ruff lint"] = run(
        ["python", "-m", "ruff", "check", *PYTHON_DIRS, "--ignore=E501"],
        "Ruff lint (E, F, W, I)"
    )

    # 2. Black format check
    results["Black format"] = run(
        ["python", "-m", "black", "--check", "--line-length=100", *PYTHON_DIRS],
        "Black format check (line-length 100)"
    )

    # 3. MyPy strict type check
    results["MyPy types"] = run(
        ["python", "-m", "mypy", "arbitrage", "--ignore-missing-imports"],
        "MyPy strict type checking"
    )

    # 4. Bandit security scan
    results["Bandit security"] = run(
        ["python", "-m", "bandit", "-r", "arbitrage", "-ll", "-q"],
        "Bandit security scan (low threshold)"
    )

    # 5. Unit tests with coverage
    results["pytest coverage"] = run(
        [
            "python", "-m", "pytest", "tests/", "-q",
            f"--cov=arbitrage",
            f"--cov-fail-under={COVERAGE_THRESHOLD}",
            "--ignore=tests/integration",
            "--ignore=tests/mcp",
            "-m", "not e2e and not runtime and not ragas",
            "--tb=short",
        ],
        f"pytest unit tests (coverage ≥ {COVERAGE_THRESHOLD}%)"
    )

    # Summary
    print(f"\n{'═' * 60}")
    print("  PRE-COMMIT SUMMARY")
    print(f"{'═' * 60}")
    all_passed = True
    for name, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"  {status}  {name}")
        if not passed:
            all_passed = False

    print(f"{'═' * 60}")
    if all_passed:
        print("  ✅  ALL CHECKS PASSED — safe to commit")
        return 0
    else:
        failed = [name for name, ok in results.items() if not ok]
        print(f"  ❌  BLOCKED: {len(failed)} check(s) failed — {', '.join(failed)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
