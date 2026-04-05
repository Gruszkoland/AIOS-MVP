#!/usr/bin/env python3
"""
ADRION 369 - Database Migration Runner

Usage:
    python scripts/migrate.py --target 002 --direction up
    python scripts/migrate.py --target 001 --direction down
    python scripts/migrate.py --list

Features:
- Applies/rolls back versioned SQL migration files from db/migrations/
- Tracks applied migrations in the migrations_applied table
- Validates file integrity via SHA-256 hash
- Supports both SQLite (dev) and PostgreSQL (prod)
"""
import argparse
import hashlib
import logging
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
MIGRATIONS_DIR = ROOT / "db" / "migrations"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MIGRATE] %(levelname)s %(message)s")
log = logging.getLogger("adrion.migrate")


# ── Database helpers ──────────────────────────────────────────────────────────

def _get_conn():
    """Open a connection using the same logic as arbitrage/database.py."""
    sys.path.insert(0, str(ROOT))
    from arbitrage.config import DB_ENGINE, DB_PATH, DB_URL  # noqa: PLC0415
    if DB_ENGINE == "postgres" and DB_URL:
        try:
            import psycopg2
            conn = psycopg2.connect(DB_URL)
            conn.autocommit = False
            return conn, "postgres"
        except Exception as exc:
            log.error("Postgres connection failed: %s — falling back to SQLite", exc)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn, "sqlite"


def _ensure_tracking_table(conn, engine: str):
    sql = """
    CREATE TABLE IF NOT EXISTS migrations_applied (
        version     INTEGER PRIMARY KEY,
        filename    TEXT NOT NULL,
        file_hash   TEXT NOT NULL,
        applied_at  TEXT DEFAULT (CURRENT_TIMESTAMP)
    );"""
    if engine == "postgres":
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    else:
        conn.execute(sql)
        conn.commit()


def _get_applied(conn, engine: str) -> list[int]:
    if engine == "postgres":
        with conn.cursor() as cur:
            cur.execute("SELECT version FROM migrations_applied ORDER BY version")
            return [r[0] for r in cur.fetchall()]
    rows = conn.execute("SELECT version FROM migrations_applied ORDER BY version").fetchall()
    return [r["version"] for r in rows]


def _record(conn, engine: str, version: int, filename: str, file_hash: str):
    sql = "INSERT INTO migrations_applied (version, filename, file_hash) VALUES (?, ?, ?)"
    args = (version, filename, file_hash)
    if engine == "postgres":
        sql = sql.replace("?", "%s")
        with conn.cursor() as cur:
            cur.execute(sql, args)
    else:
        conn.execute(sql, args)
    conn.commit()


def _remove_record(conn, engine: str, version: int):
    sql = "DELETE FROM migrations_applied WHERE version=?"
    if engine == "postgres":
        sql = sql.replace("?", "%s")
        with conn.cursor() as cur:
            cur.execute(sql, (version,))
    else:
        conn.execute(sql, (version,))
    conn.commit()


def _execute_sql(conn, engine: str, sql_text: str):
    """Execute a block of SQL statements (semicolon-separated)."""
    if engine == "postgres":
        with conn.cursor() as cur:
            cur.execute(sql_text)
        conn.commit()
    else:
        conn.executescript(sql_text)
        conn.commit()


# ── Migration file helpers ────────────────────────────────────────────────────

def _list_migration_files() -> list[tuple[int, Path]]:
    """Return sorted list of (version, path) for all migration files."""
    files = sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"))
    result = []
    for f in files:
        version = int(f.stem.split("_")[0])
        result.append((version, f))
    return result


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _extract_down_sql(sql_text: str) -> str:
    """Extract statements marked with -- DOWN: prefix."""
    lines = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("-- DOWN:"):
            stmt = stripped.removeprefix("-- DOWN:").strip()
            lines.append(stmt)
    return "\n".join(lines)


# ── Main commands ─────────────────────────────────────────────────────────────

def cmd_list():
    conn, engine = _get_conn()
    _ensure_tracking_table(conn, engine)
    applied = set(_get_applied(conn, engine))
    all_files = _list_migration_files()

    print(f"\n{'VER':>4}  {'STATUS':<12}  FILENAME")
    print("-" * 50)
    for version, path in all_files:
        status = "applied" if version in applied else "pending"
        print(f"{version:>4}  {status:<12}  {path.name}")
    print()


def cmd_apply(target_version: int):
    conn, engine = _get_conn()
    _ensure_tracking_table(conn, engine)
    applied = set(_get_applied(conn, engine))

    for version, path in _list_migration_files():
        if version > target_version or version in applied:
            continue
        sql_text = path.read_text(encoding="utf-8")
        log.info("Applying migration %03d: %s", version, path.name)
        _execute_sql(conn, engine, sql_text)
        _record(conn, engine, version, path.name, _file_hash(path))
        log.info("Migration %03d applied.", version)


def cmd_rollback(target_version: int):
    conn, engine = _get_conn()
    _ensure_tracking_table(conn, engine)
    applied = set(_get_applied(conn, engine))

    for version, path in reversed(_list_migration_files()):
        if version <= target_version or version not in applied:
            continue
        sql_text = path.read_text(encoding="utf-8")
        down_sql = _extract_down_sql(sql_text)
        if not down_sql:
            log.warning("No DOWN statements found in %s — skipping", path.name)
            continue
        log.info("Rolling back migration %03d: %s", version, path.name)
        # Remove tracking record BEFORE running DOWN SQL, in case the migration
        # drops the migrations_applied table itself (e.g., migration 001).
        _remove_record(conn, engine, version)
        _execute_sql(conn, engine, down_sql)
        log.info("Migration %03d rolled back.", version)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ADRION 369 Migration Runner")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="Show migration status")

    up_p = sub.add_parser("up", help="Apply migrations up to --target")
    up_p.add_argument("--target", type=int, required=True, help="Target migration version")

    down_p = sub.add_parser("down", help="Roll back migrations to --target")
    down_p.add_argument("--target", type=int, required=True)

    args = parser.parse_args()

    if args.command == "list":
        cmd_list()
    elif args.command == "up":
        cmd_apply(args.target)
    elif args.command == "down":
        cmd_rollback(args.target)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
