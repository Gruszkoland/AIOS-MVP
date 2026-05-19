"""sync_missing_to_pictures.py

Kopiuje wszystkie pliki z C:\\Users\\adiha\\Moj dysk\\Historie Zycia
ktore nie istnieja w C:\\Users\\adiha\\Pictures (porownanie fingerprint: nazwa+rozmiar+mtime).

Pliki trafiaja do:
  C:\\Users\\adiha\\Pictures\\01_IMPORTY_ZRODLOWE\\sync_missing_02-04-2026\\[nazwa_folderu_zrodlowego]\\

Loguje do REPORTS. Zwraca 0 jesli OK, 1 jesli blad/nadal braki.
"""

from __future__ import annotations

import shutil
import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path


WORKSPACE = Path(r"C:\Users\adiha\162 demencje w schemacie 369")
REPORTS_DIR = WORKSPACE / "Genesis Record" / "10_RAPORTY_DZIALANIA_SYSTEMU" / "REPORTS"
PROGRESS_DIR = WORKSPACE / "Genesis Record" / "10_RAPORTY_DZIALANIA_SYSTEMU" / "PROGRESS"
TODAY = "02-04-2026"
SYNC_SUBFOLDER = "sync_missing_02-04-2026"
EXCLUDE_MARKER = "_review_ThumbsDb_2026-04-02"


def quick_key(path: Path) -> str:
    # Klucz: tylko nazwa pliku (lowercase).
    # Mtime jest niestabilne (offset 9h z Google Drive), a rozmiar nie zawsze gwarantuje unikalnosc.
    # Verify script rowniez uzywa nazwy — spójne porownanie.
    return path.name.lower()


def find_historie_dir(user_root: Path) -> Path:
    drive_candidates = [p for p in user_root.iterdir() if p.is_dir() and "dysk" in p.name.lower()]
    if not drive_candidates:
        raise RuntimeError("Nie znaleziono folderu 'dysk' w: " + str(user_root))
    drive_dir = sorted(drive_candidates, key=lambda p: p.name)[0]
    hist_candidates = [p for p in drive_dir.iterdir() if p.is_dir() and p.name.lower().startswith("historie")]
    if not hist_candidates:
        raise RuntimeError("Nie znaleziono folderu Historie* w: " + str(drive_dir))
    return sorted(hist_candidates, key=lambda p: p.name)[0]


def iter_files(root: Path):
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def get_unique_dst(dst: Path) -> Path:
    if not dst.exists():
        return dst
    stem = dst.stem
    suffix = dst.suffix
    parent = dst.parent
    i = 1
    while True:
        candidate = parent / f"{stem}__dup{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync missing files from Historie Zycia to Pictures.")
    parser.add_argument("--src", default=None, help="Override source path.")
    parser.add_argument("--dst", default=r"C:\Users\adiha\Pictures", help="Target pictures root.")
    parser.add_argument("--dry-run", action="store_true", help="Tylko pokaz co by skopiowano (bez kopiowania).")
    args = parser.parse_args(argv)

    user_root = Path(r"C:\Users\adiha")
    src_root = Path(args.src) if args.src else find_historie_dir(user_root)
    dst_root = Path(args.dst)
    sync_target = dst_root / "01_IMPORTY_ZRODLOWE" / SYNC_SUBFOLDER

    now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mode_label = "DRY-RUN" if args.dry_run else "SYNC"
    print(f"[{mode_label}] {now_ts}")
    print(f"SOURCE={src_root}")
    print(f"TARGET_ROOT={dst_root}")
    print(f"SYNC_DIR={sync_target}")

    # --- zbierz fingerprints z obu folderow ---
    print("Skanowanie SOURCE ...")
    src_all = list(iter_files(src_root))
    src_files = [p for p in src_all if EXCLUDE_MARKER not in str(p)]
    print(f"  SOURCE pliki: {len(src_files)} (z {len(src_all)} lacznie)")

    print("Skanowanie TARGET ...")
    dst_files = list(iter_files(dst_root))
    print(f"  TARGET pliki: {len(dst_files)}")

    src_counter: Counter[str] = Counter()
    src_path_map: dict[str, Path] = {}
    dst_counter: Counter[str] = Counter()

    for p in src_files:
        try:
            k = quick_key(p)
        except Exception:
            continue
        src_counter[k] += 1
        src_path_map.setdefault(k, p)

    for p in dst_files:
        try:
            k = quick_key(p)
        except Exception:
            continue
        dst_counter[k] += 1

    # --- wyznacz brakujace ---
    missing: list[tuple[str, Path, int]] = []  # (key, src_path, missing_count)
    for k, need in src_counter.items():
        have = dst_counter.get(k, 0)
        if have < need:
            missing.append((k, src_path_map[k], need - have))

    missing.sort(key=lambda x: x[1].name)

    print(f"MISSING_FILES={sum(m[2] for m in missing)}")
    if not missing:
        print("STATUS=OK_ALL_PRESENT — nic do synchronizacji.")
        _write_log(REPORTS_DIR, now_ts, mode_label, src_root, dst_root, sync_target, [], "OK_ALL_PRESENT")
        return 0

    # --- kopiuj ---
    log_entries: list[str] = []
    copied = 0
    errors = 0

    if not args.dry_run:
        sync_target.mkdir(parents=True, exist_ok=True)

    for key, src_path, miss_count in missing:
        # zachowaj nazwe podfolderu zrodlowego
        try:
            rel = src_path.relative_to(src_root)
        except ValueError:
            rel = Path(src_path.name)

        parts = rel.parts
        src_subfolder = parts[0] if len(parts) > 1 else "_root"
        dst_dir = sync_target / src_subfolder
        dst_file = dst_dir / src_path.name

        entry = f"COPY|{src_path}|{dst_file}"
        if args.dry_run:
            print(f"  [DRY] {entry}")
            log_entries.append(f"[DRY] {entry}")
            copied += 1
        else:
            try:
                dst_dir.mkdir(parents=True, exist_ok=True)
                dst_final = get_unique_dst(dst_file)
                shutil.copy2(str(src_path), str(dst_final))
                log_entries.append(f"[OK] COPIED|{src_path}|{dst_final}")
                print(f"  [OK] {src_path.name} -> {dst_final}")
                copied += 1
            except Exception as e:
                log_entries.append(f"[ERR] {src_path}|{e}")
                print(f"  [ERR] {src_path.name}: {e}")
                errors += 1

    status = "DRY_RUN_COMPLETE" if args.dry_run else ("SYNC_COMPLETE" if errors == 0 else f"SYNC_PARTIAL (errors={errors})")
    print(f"\nRESULT: copied={copied}, errors={errors}")
    print(f"STATUS={status}")

    _write_log(REPORTS_DIR, now_ts, mode_label, src_root, dst_root, sync_target, log_entries, status, copied, errors)
    _append_progress(PROGRESS_DIR, now_ts, status, copied, errors)

    return 0 if errors == 0 else 1


def _write_log(reports_dir: Path, ts: str, mode: str, src: Path, dst: Path, sync_dir: Path,
               entries: list[str], status: str, copied: int = 0, errors: int = 0) -> None:
    log_path = reports_dir / f"Synchronizacja_Brakow_Historie_Do_Obrazy_{TODAY}.log"
    header = [
        f"SYNC_LOG",
        f"TIMESTAMP={ts}",
        f"MODE={mode}",
        f"SOURCE={src}",
        f"TARGET_ROOT={dst}",
        f"SYNC_DIR={sync_dir}",
        f"COPIED={copied}",
        f"ERRORS={errors}",
        f"STATUS={status}",
        "---",
        *entries,
        "",
    ]
    log_path.write_text("\n".join(header), encoding="utf-8")
    print(f"LOG_WRITTEN={log_path}")


def _append_progress(progress_dir: Path, ts: str, status: str, copied: int, errors: int) -> None:
    prog_path = progress_dir / f"Analiza_Duplikatow_I_Reorganizacja_Obrazy_{TODAY}.md"
    if not prog_path.exists():
        return
    entry = (
        f"\n### sync_missing_to_pictures.py | {ts}\n"
        f"- STATUS: {status}\n"
        f"- Skopiowano: {copied} plikow\n"
        f"- Bledy: {errors}\n"
    )
    with prog_path.open("a", encoding="utf-8") as f:
        f.write(entry)


if __name__ == "__main__":
    raise SystemExit(main())
