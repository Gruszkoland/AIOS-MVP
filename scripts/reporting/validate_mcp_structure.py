from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    canonical = REPO_ROOT / "mcp_servers"
    forbidden_root_alias = REPO_ROOT / "mcp-servers"

    if not canonical.exists():
        print("validate_mcp_structure: missing canonical root directory 'mcp_servers'")
        return 1

    if forbidden_root_alias.exists():
        print("validate_mcp_structure: root alias 'mcp-servers' is forbidden; use 'mcp_servers'")
        return 1

    print("validate_mcp_structure: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
