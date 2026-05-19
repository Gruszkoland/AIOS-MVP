from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def find_historie_dir(user_root: Path) -> Path:
    drive_candidates = [p for p in user_root.iterdir() if p.is_dir() and "dysk" in p.name.lower()]
    if not drive_candidates:
        raise RuntimeError("Nie znaleziono folderu zawierajacego 'dysk' w C:/Users/adiha")
    drive_dir = drive_candidates[0]
    historie_candidates = [p for p in drive_dir.iterdir() if p.is_dir() and p.name.lower().startswith("historie")]
    if not historie_candidates:
        raise RuntimeError("Nie znaleziono folderu Historie* w folderze dysku")
    return historie_candidates[0]


def iter_files(root: Path):
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def verify_by_filename(src: list[Path], dst: list[Path]) -> tuple[list[tuple[str, int, int, int]], int, int]:
    src_counter = Counter(p.name.lower() for p in src)
    dst_counter = Counter(p.name.lower() for p in dst)

    missing: list[tuple[str, int, int, int]] = []
    for name, need in src_counter.items():
        have = dst_counter.get(name, 0)
        if have < need:
            missing.append((name, need, have, need - have))

    missing.sort(key=lambda x: x[3], reverse=True)
    return missing, len(src_counter), len(dst_counter)


def verify_by_hash(src: list[Path], dst: list[Path]) -> tuple[list[tuple[str, int, int, int, str]], int, int]:
    src_counter: Counter[str] = Counter()
    dst_counter: Counter[str] = Counter()
    src_example: dict[str, str] = {}

    for p in src:
        try:
            h = sha256_file(p)
        except Exception:
            continue
        src_counter[h] += 1
        src_example.setdefault(h, str(p))

    for p in dst:
        try:
            h = sha256_file(p)
        except Exception:
            continue
        dst_counter[h] += 1

    missing: list[tuple[str, int, int, int, str]] = []
    for h, need in src_counter.items():
        have = dst_counter.get(h, 0)
        if have < need:
            missing.append((h, need, have, need - have, src_example[h]))

    missing.sort(key=lambda x: x[3], reverse=True)
    return missing, len(src_counter), len(dst_counter)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify copy coverage from Historie* to Pictures")
    parser.add_argument("--user-root", default=r"C:\Users\adiha", help="User root for dysk/Historie discovery")
    parser.add_argument("--dst-root", default=r"C:\Users\adiha\Pictures", help="Destination root")
    parser.add_argument(
        "--exclude-token",
        default="_review_ThumbsDb_2026-04-02",
        help="Substring excluded from source path",
    )
    parser.add_argument(
        "--mode",
        choices=["filename", "hash"],
        default="filename",
        help="filename = fast check by name, hash = exact byte-level check",
    )
    parser.add_argument(
        "--output",
        default=r"C:\Users\adiha\162 demencje w schemacie 369\Genesis Record\10_RAPORTY_DZIALANIA_SYSTEMU\REPORTS\Weryfikacja_Historie_Zycia_Do_Obrazy_02-04-2026.txt",
        help="Output report path",
    )
    parser.add_argument("--top", type=int, default=40, help="How many missing rows to include")
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Return exit code 1 when missing files are detected",
    )
    args = parser.parse_args()

    user_root = Path(args.user_root)
    dst_root = Path(args.dst_root)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        src_root = find_historie_dir(user_root)
    except Exception as exc:
        print(f"ERROR={exc}")
        return 2

    if not dst_root.exists():
        print(f"ERROR=Destination not found: {dst_root}")
        return 3

    src_all = list(iter_files(src_root))
    src = [p for p in src_all if args.exclude_token not in str(p)]
    dst = list(iter_files(dst_root))

    if args.mode == "filename":
        missing, src_unique, dst_unique = verify_by_filename(src, dst)
    else:
        missing, src_unique, dst_unique = verify_by_hash(src, dst)

    lines: list[str] = []
    lines.append(f"SOURCE={src_root}")
    lines.append(f"TARGET={dst_root}")
    lines.append(f"MODE={args.mode}")
    lines.append(f"SOURCE_FILES_ALL={len(src_all)}")
    lines.append(f"SOURCE_FILES_EXCL_REVIEW={len(src)}")
    lines.append(f"TARGET_FILES={len(dst)}")
    lines.append(f"SOURCE_UNIQUE_KEYS={src_unique}")
    lines.append(f"TARGET_UNIQUE_KEYS={dst_unique}")
    lines.append(f"MISSING_HASH_GROUPS={len(missing)}")
    lines.append(f"MISSING_FILE_INSTANCES={sum(m[3] for m in missing)}")
    lines.append("STATUS=" + ("OK_ALL_PRESENT" if not missing else "MISSING_DETECTED"))
    lines.append("")
    lines.append("TOP_MISSING")
    if args.mode == "filename":
        for name, need, have, miss in missing[: args.top]:
            lines.append(f"NAME={name}|need={need}|have={have}|missing={miss}")
    else:
        for h, need, have, miss, example in missing[: args.top]:
            lines.append(f"HASH={h}|need={need}|have={have}|missing={miss}")
            lines.append(f"  SRC={example}")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE={out_path}")
    if missing and args.fail_on_missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
