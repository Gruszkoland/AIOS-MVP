from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "migration_batches" / "batch3" / "to-formula" / "canonical-core"
MANIFEST_MD = REPO_ROOT / "docs" / "guides" / "repo-organization" / "CANONICAL_EXTRACTION_MANIFEST.md"
MANIFEST_JSON = REPO_ROOT / "docs" / "guides" / "repo-organization" / "CANONICAL_EXTRACTION_MANIFEST.json"

# Initial canonical set for Formula extraction.
CANONICAL_SOURCES: list[Path] = [
    REPO_ROOT / "docs" / "GUARDIAN_LAWS_CANONICAL.json",
    REPO_ROOT / "REPO_CONTEXT_STATUS.txt",
    REPO_ROOT / "docs" / "guides" / "repo-organization" / "FINAL_GOVERNANCE_CLOSURE.md",
]

EXCLUDE_SEGMENTS = {
    ".git",
    "venv",
    ".venv",
    "node_modules",
    "__pycache__",
}


@dataclass(frozen=True)
class ExtractedFile:
    source: Path
    target: Path
    sha256: str
    size: int


@dataclass(frozen=True)
class DuplicateCandidate:
    canonical: Path
    duplicate: Path
    sha256: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_SEGMENTS for part in path.parts)


def collect_paths_by_name(name: str) -> Iterable[Path]:
    for p in REPO_ROOT.rglob(name):
        if not p.is_file():
            continue
        if is_excluded(p):
            continue
        yield p


def extract() -> tuple[list[ExtractedFile], list[DuplicateCandidate]]:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    extracted: list[ExtractedFile] = []
    duplicates: list[DuplicateCandidate] = []

    for src in CANONICAL_SOURCES:
        if not src.exists():
            raise FileNotFoundError(f"Missing canonical source: {src}")

        rel = src.relative_to(REPO_ROOT)
        target = OUTPUT_ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(src.read_bytes())

        digest = sha256_file(src)
        extracted.append(
            ExtractedFile(
                source=src,
                target=target,
                sha256=digest,
                size=src.stat().st_size,
            )
        )

        for candidate in collect_paths_by_name(src.name):
            if candidate == src:
                continue
            if candidate.resolve() == target.resolve():
                continue
            if sha256_file(candidate) == digest:
                duplicates.append(
                    DuplicateCandidate(canonical=src, duplicate=candidate, sha256=digest)
                )

    # Keep output deterministic.
    duplicates.sort(key=lambda d: str(d.duplicate))
    return extracted, duplicates


def write_manifests(extracted: list[ExtractedFile], duplicates: list[DuplicateCandidate]) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    md_lines: list[str] = [
        "# Canonical Extraction Manifest",
        "",
        "Typ dokumentu: Reference",
        "",
        f"Generated at (UTC): {ts}",
        "",
        "## Extracted Canonical Files",
        "",
        "| Source | Target (Formula staging) | SHA256 | Size (bytes) |",
        "| --- | --- | --- | ---: |",
    ]

    for item in extracted:
        src = item.source.relative_to(REPO_ROOT).as_posix()
        dst = item.target.relative_to(REPO_ROOT).as_posix()
        md_lines.append(f"| `{src}` | `{dst}` | `{item.sha256}` | {item.size} |")

    md_lines.extend(["", "## Duplicate Candidates (same hash)", ""])
    if duplicates:
        md_lines.append("| Canonical | Duplicate | SHA256 | Suggested action |")
        md_lines.append("| --- | --- | --- | --- |")
        for dup in duplicates:
            c = dup.canonical.relative_to(REPO_ROOT).as_posix()
            d = dup.duplicate.relative_to(REPO_ROOT).as_posix()
            md_lines.append(
                f"| `{c}` | `{d}` | `{dup.sha256}` | Replace with canonical reference |"
            )
    else:
        md_lines.append("No duplicate candidates found for current canonical set.")

    md_lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This is a non-destructive extraction and dedup pass.",
            "- Next step: replace duplicate payload files with references where ownership policy allows.",
        ]
    )

    MANIFEST_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    payload = {
        "generated_at_utc": ts,
        "output_root": OUTPUT_ROOT.relative_to(REPO_ROOT).as_posix(),
        "extracted": [
            {
                "source": item.source.relative_to(REPO_ROOT).as_posix(),
                "target": item.target.relative_to(REPO_ROOT).as_posix(),
                "sha256": item.sha256,
                "size": item.size,
            }
            for item in extracted
        ],
        "duplicate_candidates": [
            {
                "canonical": dup.canonical.relative_to(REPO_ROOT).as_posix(),
                "duplicate": dup.duplicate.relative_to(REPO_ROOT).as_posix(),
                "sha256": dup.sha256,
                "suggested_action": "replace_with_reference",
            }
            for dup in duplicates
        ],
    }
    MANIFEST_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main() -> int:
    extracted, duplicates = extract()
    write_manifests(extracted, duplicates)
    print(
        "extract_canonical_docs: extracted="
        f"{len(extracted)} duplicate_candidates={len(duplicates)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
