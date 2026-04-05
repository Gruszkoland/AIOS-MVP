# ADRION 369 — Database Migration Guide

## Overview

Migrations are versioned SQL files stored in `db/migrations/`. The runner `scripts/migrate.py`
applies (UP) or rolls back (DOWN) migrations and records every change in a `migrations_applied`
tracking table. SHA-256 hashes detect file tampering between runs.

Works against both SQLite (dev / mobile offline-first) and PostgreSQL (server production);
the active engine is determined by `arbitrage/config.py` (`DB_ENGINE`, `DB_URL`, `DB_PATH`).

---

## File Naming Convention

```
db/migrations/NNN_short_description.sql
```

- `NNN` — zero-padded version number, e.g. `001`, `002`, `010`
- Filenames are scanned with glob pattern `[0-9][0-9][0-9]_*.sql`
- Versions are applied **in ascending order** and rolled back in **descending order**

---

## Migration File Format

Each file contains two sections:

### UP (forward migration)
Regular `CREATE TABLE`, `ALTER TABLE`, `CREATE INDEX` statements.

### DOWN (rollback)
Lines prefixed with `-- DOWN:` — the part after the prefix is extracted and executed on rollback.

**Example:**

```sql
-- UP
CREATE TABLE IF NOT EXISTS widgets (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT    NOT NULL,
    value   REAL    DEFAULT 0.0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_widgets_name ON widgets (name);

-- DOWN: DROP INDEX IF EXISTS idx_widgets_name;
-- DOWN: DROP TABLE IF EXISTS widgets;
```

> **Important:** DOWN statements are executed in the order they appear in the file.
> Put `DROP INDEX` before `DROP TABLE` to avoid constraint errors.

---

## Tracking Table

`migrations_applied` is auto-created on first run:

```sql
CREATE TABLE IF NOT EXISTS migrations_applied (
    version     INTEGER PRIMARY KEY,
    filename    TEXT    NOT NULL,
    file_hash   TEXT    NOT NULL,    -- SHA-256 of migration file bytes
    applied_at  TEXT    DEFAULT (CURRENT_TIMESTAMP)
);
```

---

## CLI Reference

```bash
# Show current status of all migrations
python scripts/migrate.py list

# Apply all migrations up to and including version 005
python scripts/migrate.py up --target 5

# Apply all available migrations
python scripts/migrate.py up --target 999

# Roll back migration 005 (keeps 001-004 applied)
python scripts/migrate.py down --target 4

# Roll back everything (use with caution!)
python scripts/migrate.py down --target 0
```

---

## Creating a New Migration

1. **Determine the next version number:**
   ```bash
   python scripts/migrate.py list
   ```

2. **Create the migration file:**
   ```bash
   # Example: adding a jobs_archive table (version 003)
   touch db/migrations/003_add_jobs_archive.sql
   ```

3. **Write UP + DOWN statements:**
   ```sql
   CREATE TABLE IF NOT EXISTS jobs_archive (
       id          TEXT PRIMARY KEY,
       original_id TEXT,
       archived_at TEXT DEFAULT (datetime('now'))
   );
   -- DOWN: DROP TABLE IF EXISTS jobs_archive;
   ```

4. **Test locally — apply:**
   ```bash
   python scripts/migrate.py up --target 3
   python scripts/migrate.py list   # should show 003 as applied
   ```

5. **Test rollback:**
   ```bash
   python scripts/migrate.py down --target 2
   python scripts/migrate.py list   # should show 003 as pending
   ```

6. **Re-apply and verify data integrity before committing.**

---

## Deployment Procedure

### Development (SQLite)

```bash
# 1. Set DB_ENGINE=sqlite (default) in .env or environment
# 2. Run migrations
python scripts/migrate.py up --target 999
```

### Production (PostgreSQL)

```bash
# 1. Set env vars
export DB_ENGINE=postgres
export DB_URL=postgresql://adrion:password@localhost:5432/genesis_record

# 2. (Optional) Create a backup before migrating
bash scripts/backup/backup-postgres.sh

# 3. Apply migrations in staging first
python scripts/migrate.py list
python scripts/migrate.py up --target NNN

# 4. Validate the result
psql $DB_URL -c "SELECT version, filename, applied_at FROM migrations_applied ORDER BY version"

# 5. Deploy application
```

---

## Rollback Procedure

```bash
# Roll back the last migration (e.g., from 003 → 002)
python scripts/migrate.py down --target 2

# Verify
python scripts/migrate.py list
```

> **Special case — migration 001:** Rolling back migration 001 drops the `migrations_applied`
> table itself. The runner handles this safely by removing the tracking record **before**
> executing the DOWN SQL.

---

## Adding Migrations to Existing Tables (ALTER TABLE)

SQLite has limited `ALTER TABLE` support. When you need to add a column:

```sql
-- Preferred for SQLite compatibility:
ALTER TABLE jobs ADD COLUMN priority INTEGER DEFAULT 0;
-- DOWN: No rollback possible in SQLite; document the manual step:
-- DOWN: -- SQLite: manually recreate table without column if needed
```

For complex schema changes on PostgreSQL, use a multi-step migration:
1. `001_add_column.sql` — add the column as nullable
2. `002_backfill.sql` — backfill existing rows
3. `003_add_constraint.sql` — add NOT NULL constraint once data is clean

---

## Safety Rules

| Rule | Reason |
|------|--------|
| Always test in staging before production | Catch data issues early |
| Keep migrations small and idempotent | Easier rollback |
| Never edit an applied migration file | Hash check will detect it |
| Always include a DOWN section | Rollback must always be possible |
| Take a database backup before production runs | Last-resort recovery |

---

## Current Migrations

| Version | File | Description |
|---------|------|-------------|
| 001 | `001_initial_schema.sql` | Full schema: all 13 core tables |
| 002 | `002_add_indexes.sql` | Performance indexes for deals, alerts, jobs, bids, kpi_events, payment_events |
