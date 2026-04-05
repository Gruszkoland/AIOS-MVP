#!/usr/bin/env python3
"""
ADRION 369 — SQLite Backup Utility

Creates a timestamped, consistent copy of the SQLite database using
SQLite's built-in online backup API (no lock contention, safe while
the application is running).

Usage:
    python scripts/backup/backup-sqlite.py
    python scripts/backup/backup-sqlite.py --db path/to/arbitrage.db --out backups/
    python scripts/backup/backup-sqlite.py --verify backups/backup_arbitrage_20260404_120000.db
"""
import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DEFAULT_DB = ROOT / "arbitrage.db"
DEFAULT_OUT = ROOT / "backups"
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", 7))


def backup(db_path: Path, out_dir: Path) -> Path:
    """Create a consistent hot-backup using sqlite3.Connection.backup()."""
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = out_dir / f"backup_{db_path.stem}_{timestamp}.db"

    print(f"[BACKUP] {db_path} → {dest}")
    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(dest))
    try:
        src.backup(dst, pages=100)
    finally:
        dst.close()
        src.close()

    size_mb = dest.stat().st_size / 1024 / 1024
    print(f"[BACKUP] Done. Size: {size_mb:.2f} MB")

    if size_mb > 5120:  # 5 GB
        print(f"[BACKUP] WARNING: backup size {size_mb:.0f} MB exceeds 5 GB threshold!", file=sys.stderr)

    return dest


def verify(backup_path: Path) -> bool:
    """Verify backup integrity via PRAGMA integrity_check."""
    print(f"[VERIFY] Checking {backup_path} ...")
    conn = sqlite3.connect(str(backup_path))
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.execute("PRAGMA quick_check")
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        conn.close()

        if result == "ok":
            print(f"[VERIFY] OK — tables: {table_names}")
            return True
        else:
            print(f"[VERIFY] FAILED — integrity check returned: {result}", file=sys.stderr)
            return False
    except Exception as exc:
        print(f"[VERIFY] ERROR — {exc}", file=sys.stderr)
        conn.close()
        return False


def prune(out_dir: Path, db_stem: str) -> int:
    """Remove backups older than RETENTION_DAYS. Returns number of files removed."""
    cutoff = datetime.now().timestamp() - (RETENTION_DAYS * 86400)
    removed = 0
    for f in out_dir.glob(f"backup_{db_stem}_*.db"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            removed += 1
            print(f"[PRUNE] Removed old backup: {f.name}")
    return removed


def main():
    parser = argparse.ArgumentParser(description="ADRION 369 SQLite backup utility")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Source SQLite file")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory")
    parser.add_argument("--verify", type=Path, metavar="BACKUP_FILE",
                        help="Verify an existing backup file instead of creating one")
    parser.add_argument("--no-verify", action="store_true",
                        help="Skip post-backup integrity check")
    args = parser.parse_args()

    if args.verify:
        ok = verify(args.verify)
        sys.exit(0 if ok else 1)

    if not args.db.exists():
        print(f"[BACKUP] ERROR: source DB not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    dest = backup(args.db, args.out)

    if not args.no_verify:
        ok = verify(dest)
        if not ok:
            sys.exit(1)

    removed = prune(args.out, args.db.stem)
    if removed:
        print(f"[PRUNE] Removed {removed} backup(s) older than {RETENTION_DAYS} days.")


if __name__ == "__main__":
    main()
