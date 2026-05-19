#!/usr/bin/env python3
"""
ADRION 369 — Install git hooks
Run once after cloning:  python scripts/install_hooks.py
"""

import shutil
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
GIT_HOOKS_DIR = ROOT / ".git" / "hooks"
HOOK_SOURCE = Path(__file__).parent / "pre-commit.hook"
HOOK_DEST = GIT_HOOKS_DIR / "pre-commit"


def main() -> int:
    if not GIT_HOOKS_DIR.exists():
        print(f"❌  .git/hooks not found at {GIT_HOOKS_DIR}")
        print("    Run this script from the repo root.")
        return 1

    if not HOOK_SOURCE.exists():
        print(f"❌  Hook source not found: {HOOK_SOURCE}")
        return 1

    shutil.copy2(HOOK_SOURCE, HOOK_DEST)

    # Make executable (Unix/macOS)
    current_mode = HOOK_DEST.stat().st_mode
    HOOK_DEST.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"✅  Pre-commit hook installed → {HOOK_DEST}")
    print("")
    print("    Every commit will now run:")
    print("      1. Ruff lint         (ruff check arbitrage/ uap/ tests/)")
    print("      2. Black format      (black --check)")
    print("      3. MyPy types        (mypy arbitrage/)")
    print("      4. Bandit security   (bandit -r arbitrage/ -ll)")
    print("      5. pytest coverage   (≥80%)")
    print("")
    print("    To skip (not recommended): git commit --no-verify")
    return 0


if __name__ == "__main__":
    sys.exit(main())
