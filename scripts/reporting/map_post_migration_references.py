from __future__ import annotations

import argparse
from pathlib import Path

MAPPING = {
    "agents/": "migration_batches/batch2/to-architecture/agents/",
    "poc/": "migration_batches/batch1/review-bucket/poc/",
    "adrion-swarm/": "migration_batches/batch2/to-system/adrion-swarm/",
    "n8n-workflows/": "migration_batches/batch2/to-system/n8n-workflows/",
    "tools/": "migration_batches/batch2/to-system/tools/",
    "PROJEKTY/": "migration_batches/batch2/to-archive/PROJEKTY/",
}

SCAN_EXTENSIONS = {".md", ".py", ".yml", ".yaml", ".json", ".toml", ".ps1", ".sh", ".txt"}
EXCLUDED_PARTS = {
    ".git",
    "node_modules",
    "__pycache__",
    "archive",
    "archiwum",
    "scalanie",
}


def should_scan(path: Path) -> bool:
    if path.suffix.lower() not in SCAN_EXTENSIONS:
        return False
    parts = set(path.parts)
    if "migration_batches" in parts:
        return False
    return not any(part in parts for part in EXCLUDED_PARTS)


def map_references(root: Path) -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {}
    for file_path in root.rglob("*"):
        if not file_path.is_file() or not should_scan(file_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue

        rel = file_path.relative_to(root).as_posix()
        for old_ref, new_ref in MAPPING.items():
            if old_ref in content:
                findings.setdefault(rel, []).append(f"{old_ref} -> {new_ref}")

    return findings


def render_report(findings: dict[str, list[str]], output: Path) -> None:
    lines: list[str] = []
    lines.append("# Post-Migration Reference Mapping Report")
    lines.append("")
    lines.append("Typ dokumentu: Reference")
    lines.append("")
    lines.append("## Mapping Rules")
    lines.append("")
    for old_ref, new_ref in MAPPING.items():
        lines.append(f"- `{old_ref}` -> `{new_ref}`")
    lines.append("")

    lines.append("## Findings")
    lines.append("")
    if not findings:
        lines.append("No remaining references found in active workspace scope.")
    else:
        for file_path in sorted(findings):
            lines.append(f"- `{file_path}`")
            for ref in sorted(set(findings[file_path])):
                lines.append(f"  - {ref}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Files with references: {len(findings)}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Map post-migration references in active workspace files")
    parser.add_argument("--root", default=".", help="Workspace root path")
    parser.add_argument(
        "--output",
        default="docs/guides/repo-organization/POST_MIGRATION_REFERENCE_MAP.md",
        help="Report output path",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = (root / args.output).resolve()

    findings = map_references(root)
    render_report(findings, output)
    print(f"OK: report generated at {output}")
    print(f"Files with references: {len(findings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
