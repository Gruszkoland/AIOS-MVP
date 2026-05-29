from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULT_CONTEXT_PATH = Path("REPO_CONTEXT_STATUS.txt")
DEFAULT_VERSION_PATH = Path("VERSION")
DEFAULT_PROJECT_STATE_PATH = Path("PROJECT_STATE.json")
DEFAULT_MANIFEST_PATH = Path("MANIFEST.md")

REQUIRED_SECTION_HEADERS = [
    "## repository_identity",
    "## architecture_model",
    "## version_alignment",
    "## governance_status",
    "## security_hygiene",
    "## migration_status",
    "## ci_gates",
    "## known_risks",
    "## next_actions",
]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _read_version(path: Path) -> str:
    return _read_text(path).strip()


def _extract_manifest_project_version(text: str) -> str | None:
    match = re.search(r"^>\s*\*\*Project Version:\*\*\s*([0-9]+\.[0-9]+\.[0-9]+)\s*$", text, flags=re.MULTILINE)
    if not match:
        return None
    return match.group(1)


def validate_context_file(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing file: {path}"]

    content = _read_text(path)
    for section in REQUIRED_SECTION_HEADERS:
        if section not in content:
            errors.append(f"missing section: {section}")

    if "status: ACTIVE" not in content:
        errors.append("missing status: ACTIVE")

    return errors


def validate_version_alignment(
    version_path: Path,
    project_state_path: Path,
    manifest_path: Path,
) -> list[str]:
    errors: list[str] = []

    if not version_path.exists():
        return [f"missing file: {version_path}"]
    if not project_state_path.exists():
        return [f"missing file: {project_state_path}"]
    if not manifest_path.exists():
        return [f"missing file: {manifest_path}"]

    version_value = _read_version(version_path)
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version_value):
        errors.append("VERSION must match semantic format X.Y.Z")

    project_state = json.loads(_read_text(project_state_path))
    project_version = project_state.get("project_version")
    if project_version != version_value:
        errors.append(
            f"PROJECT_STATE project_version mismatch: expected {version_value}, got {project_version}"
        )

    manifest_project_version = _extract_manifest_project_version(_read_text(manifest_path))
    if manifest_project_version != version_value:
        errors.append(
            f"MANIFEST Project Version mismatch: expected {version_value}, got {manifest_project_version}"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate REPO_CONTEXT_STATUS structure and version alignment"
    )
    parser.add_argument("--context", default=str(DEFAULT_CONTEXT_PATH), help="Path to REPO_CONTEXT_STATUS file")
    parser.add_argument("--version", default=str(DEFAULT_VERSION_PATH), help="Path to VERSION file")
    parser.add_argument(
        "--project-state",
        default=str(DEFAULT_PROJECT_STATE_PATH),
        help="Path to PROJECT_STATE.json file",
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH), help="Path to MANIFEST.md file")
    args = parser.parse_args()

    context_path = Path(args.context)
    version_path = Path(args.version)
    project_state_path = Path(args.project_state)
    manifest_path = Path(args.manifest)

    errors: list[str] = []
    errors.extend(validate_context_file(context_path))
    errors.extend(validate_version_alignment(version_path, project_state_path, manifest_path))

    if errors:
        print("FAIL: repo context validation failed")
        for error in errors:
            print(f" - {error}")
        return 1

    print("OK: repo context and version alignment validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
