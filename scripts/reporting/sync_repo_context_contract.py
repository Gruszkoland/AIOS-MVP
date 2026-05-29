from pathlib import Path
import re
import sys

MARKER_START = "<!-- BEGIN:REPO_CONTEXT_CONTRACT -->"
MARKER_END = "<!-- END:REPO_CONTEXT_CONTRACT -->"

REPO_ROOT = Path(__file__).resolve().parents[2]
COPILOT_PATH = REPO_ROOT / ".github" / "copilot-instructions.md"
CLAUDE_PATH = REPO_ROOT / "CLAUDE.md"


def extract_contract_block(text: str) -> str:
    pattern = re.compile(
        rf"{re.escape(MARKER_START)}\\n(.*?)\\n{re.escape(MARKER_END)}",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError("Contract markers not found in source file")
    return match.group(1)


def replace_contract_block(text: str, new_block: str) -> str:
    pattern = re.compile(
        rf"{re.escape(MARKER_START)}\\n(.*?)\\n{re.escape(MARKER_END)}",
        re.DOTALL,
    )
    replacement = f"{MARKER_START}\\n{new_block}\\n{MARKER_END}"
    updated, count = pattern.subn(replacement, text)
    if count != 1:
        raise ValueError("Contract markers missing or duplicated in target file")
    return updated


def sync_contract() -> int:
    if not COPILOT_PATH.exists() or not CLAUDE_PATH.exists():
        print("sync_repo_context_contract: required files are missing")
        return 2

    copilot_text = COPILOT_PATH.read_text(encoding="utf-8")
    claude_text = CLAUDE_PATH.read_text(encoding="utf-8")

    contract_block = extract_contract_block(copilot_text)
    updated_claude = replace_contract_block(claude_text, contract_block)

    if updated_claude != claude_text:
        CLAUDE_PATH.write_text(updated_claude, encoding="utf-8")
        print("sync_repo_context_contract: CLAUDE.md updated")
    else:
        print("sync_repo_context_contract: already in sync")

    return 0


if __name__ == "__main__":
    sys.exit(sync_contract())
