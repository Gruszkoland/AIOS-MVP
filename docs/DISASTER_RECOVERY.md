# ADRION 369 — Disaster Recovery Procedures

## Overview

This document covers backup, restore, and recovery procedures for both database backends:
- **SQLite** — development, mobile offline-first (`arbitrage.db`)
- **PostgreSQL 15** — server production (`genesis_record`)

For schema migration rollbacks, see [`db/MIGRATION_GUIDE.md`](../db/MIGRATION_GUIDE.md).

---

## 1. Backup Strategy

### 1.1 SQLite (Dev / Mobile)

| Item | Value |
|------|-------|
| Tool | `python scripts/backup/backup-sqlite.py` |
| Technology | SQLite online backup API (no locking) |
| Frequency | On-demand or via task scheduler |
| Retention | 7 days rolling (configurable via `RETENTION_DAYS`) |
| Output format | `.db` file (uncompressed, ready to restore) |
| Integrity check | Automatic `PRAGMA integrity_check` after each backup |

**Quick backup with verification:**
```bash
python scripts/backup/backup-sqlite.py
# Creates: backups/backup_arbitrage_YYYYMMDD_HHMMSS.db
```

**Verify an existing backup:**
```bash
python scripts/backup/backup-sqlite.py --verify backups/backup_arbitrage_20260404_120000.db
```

### 1.2 PostgreSQL (Production)

| Item | Value |
|------|-------|
| Tool | `scripts/backup/backup-postgres.sh` |
| Technology | `pg_dump` plain SQL, gzip-9 compressed |
| Frequency | Daily (cron or CI schedule) |
| Retention | 7 days rolling |
| Output format | `.sql.gz` (human-readable, portable) |
| Alert threshold | Warning if backup > 5 GB |

**Quick backup:**
```bash
bash scripts/backup/backup-postgres.sh
# Creates: backups/backup_genesis_record_YYYYMMDD_HHMMSS.sql.gz
```

**Scheduled backup (crontab — daily at 03:00):**
```bash
0 3 * * * cd /opt/adrion && bash scripts/backup/backup-postgres.sh >> logs/backup.log 2>&1
```

**Via Docker (PostgreSQL runs in container):**
```bash
docker exec adrion-db pg_dump -U adrion genesis_record | gzip -9 > backups/backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

---

## 2. Restore Procedures

> **Warning:** Always stop application services before restoring a database to avoid
> write conflicts and data corruption.

### 2.1 SQLite Restore

```bash
# 1. Stop application
docker-compose -f adrion-swarm/docker-compose.yml stop

# 2. Back up the current (possibly corrupt) database
cp arbitrage.db arbitrage.db.broken_$(date +%Y%m%d_%H%M%S)

# 3. Restore from backup
cp backups/backup_arbitrage_YYYYMMDD_HHMMSS.db arbitrage.db

# 4. Verify integrity
python scripts/backup/backup-sqlite.py --verify arbitrage.db

# 5. Restart application
docker-compose -f adrion-swarm/docker-compose.yml up -d
```

### 2.2 PostgreSQL Restore

```bash
# 1. Stop application (keep postgres running)
docker-compose -f adrion-swarm/docker-compose.yml stop vortex-engine adrion-healer n8n

# 2. Choose backup file
ls -lh backups/backup_genesis_record_*.sql.gz | tail -5

# 3. Create test DB for validation first
docker exec adrion-db psql -U adrion -c "CREATE DATABASE genesis_record_test;"

# 4. Restore to test DB
gunzip -c backups/backup_genesis_record_YYYYMMDD_HHMMSS.sql.gz \
  | docker exec -i adrion-db psql -U adrion -d genesis_record_test

# 5. Validate data in test DB
docker exec adrion-db psql -U adrion -d genesis_record_test \
  -c "SELECT table_name, pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) AS size
      FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"

# 6. If validation passes, restore to production DB
docker exec adrion-db psql -U adrion -c "DROP DATABASE IF EXISTS genesis_record_old;"
docker exec adrion-db psql -U adrion -c "ALTER DATABASE genesis_record RENAME TO genesis_record_old;"
docker exec adrion-db psql -U adrion -c "ALTER DATABASE genesis_record_test RENAME TO genesis_record;"

# 7. Re-run pending migrations (if backup pre-dates latest migration)
DB_ENGINE=postgres DB_URL=postgresql://adrion:adrion_pass@localhost:5432/genesis_record \
  python scripts/migrate.py up --target 999

# 8. Restart application
docker-compose -f adrion-swarm/docker-compose.yml up -d

# 9. Health check
curl http://localhost:1740/health
```

---

## 3. Failure Scenarios & Playbooks

### Scenario A — Corrupt SQLite database

**Symptoms:** `sqlite3.DatabaseError: database disk image is malformed`

```bash
# Check integrity
sqlite3 arbitrage.db "PRAGMA integrity_check;"

# If failed → restore from latest backup
ls -lt backups/backup_arbitrage_*.db | head -3
cp backups/backup_arbitrage_<LATEST>.db arbitrage.db
```

### Scenario B — Accidental table drop

**Symptoms:** `sqlite3.OperationalError: no such table: jobs`

```bash
# Option 1: Rollback migration (if caused by migration)
python scripts/migrate.py down --target <PREV_VERSION>

# Option 2: Restore from backup (if not caused by migration)
cp backups/backup_arbitrage_<LATEST>.db arbitrage.db
python scripts/migrate.py up --target 999
```

### Scenario C — PostgreSQL container data loss

**Symptoms:** `adrion-db` container shows empty `postgres_data/`

```bash
# Start clean postgres container
docker-compose -f adrion-swarm/docker-compose.yml up -d postgres

# Wait for it to be healthy
docker inspect adrion-db --format='{{.State.Health.Status}}'

# Restore latest backup
gunzip -c backups/backup_genesis_record_<LATEST>.sql.gz \
  | docker exec -i adrion-db psql -U adrion -d genesis_record

# Run migrations to latest
DB_ENGINE=postgres DB_URL=postgresql://adrion:adrion_pass@localhost:5432/genesis_record \
  python scripts/migrate.py up --target 999
```

### Scenario D — Failed migration corrupted schema

**Symptoms:** Application errors on table/column access after a migration run

```bash
# 1. Roll back the failed migration
python scripts/migrate.py list
python scripts/migrate.py down --target <PREV_GOOD_VERSION>

# 2. Verify schema is clean
python scripts/migrate.py list

# 3. Fix the migration SQL in db/migrations/
# 4. Re-apply
python scripts/migrate.py up --target <VERSION>
```

---

## 4. Quarterly Drill Procedure

Run this checklist every quarter to validate that backups are actually usable:

```bash
# SQLite drill
python scripts/backup/backup-sqlite.py
cp backups/backup_arbitrage_<LATEST>.db /tmp/adrion_test_restore.db
python scripts/backup/backup-sqlite.py --verify /tmp/adrion_test_restore.db
sqlite3 /tmp/adrion_test_restore.db "SELECT count(*) FROM jobs; SELECT count(*) FROM kpis;"
rm /tmp/adrion_test_restore.db
echo "SQLite drill PASSED"

# PostgreSQL drill (requires running postgres container)
docker exec adrion-db psql -U adrion -c "CREATE DATABASE genesis_record_drill;"
gunzip -c backups/backup_genesis_record_<LATEST>.sql.gz \
  | docker exec -i adrion-db psql -U adrion -d genesis_record_drill
docker exec adrion-db psql -U adrion -d genesis_record_drill \
  -c "SELECT COUNT(*) FROM jobs; SELECT COUNT(*) FROM kpi_events;"
docker exec adrion-db psql -U adrion -c "DROP DATABASE genesis_record_drill;"
echo "PostgreSQL drill PASSED"
```

Log the drill results in `Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/REPORTS/`.

---

## 5. Recovery Time Objectives

| Component | RPO (data loss target) | RTO (recovery time target) |
|-----------|------------------------|----------------------------|
| SQLite dev | 1 day (daily backup) | < 5 minutes |
| PostgreSQL prod | 1 day (daily backup) | < 15 minutes |
| Schema-only loss | Near-zero (migrations idempotent) | < 5 minutes |

---

## 6. Related Documents

- [`db/MIGRATION_GUIDE.md`](../db/MIGRATION_GUIDE.md) — Schema migration procedures
- [`docs/DATABASE-RESTORE-PROCEDURE.md`](DATABASE-RESTORE-PROCEDURE.md) — Quick restore reference (Polish)
- [`adrion-swarm/docker-compose.yml`](../adrion-swarm/docker-compose.yml) — Container definitions
