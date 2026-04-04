# DATABASE MIGRATION GUIDE — UAP v4.0

**Version**: 4.0.0
**Last Updated**: 2026-04-04
**Migration System**: Version tracking with SHA-256 hashes

---

## Overview

UAP uses a **declarative migration system** with:

- **Version tracking**: `schema_versions` table stores applied migrations
- **Rollback support**: Each migration tracks `up` and `down` SQL
- **Hash verification**: SHA-256 checksums prevent tampering
- **Atomic execution**: Transactions ensure consistency

---

## Migration Files Structure

```
db/migrations/
├── 001_initial_schema.sql        # Core tables
├── 002_add_indexes.sql           # Performance indexes
├── 003_multi_tenant.sql          # org_id scoping
├── 004_auth_tables.sql           # JWT + RBAC
└── migration_manifest.json       # Version tracking
```

---

## Running Migrations

### 1. Apply All Pending Migrations

```bash
cd uap
python scripts/migrate.py up --all
```

**Output**:

```
✅ Migration 001: initial_schema (0.234s)
✅ Migration 002: add_indexes (0.156s)
✅ Migration 003: multi_tenant (0.089s)
✅ Migration 004: auth_tables (0.123s)
✅ All migrations applied successfully (Total: 0.602s)
```

### 2. Apply Single Migration

```bash
python scripts/migrate.py up -1
```

### 3. Rollback Last Migration

```bash
python scripts/migrate.py down -1
```

### 4. List Applied Migrations

```bash
python scripts/migrate.py list
```

**Output**:

```
Applied Migrations:
  ✅ 001 | initial_schema | 2026-04-04 10:00:00 | Hash: a1b2c3...
  ✅ 002 | add_indexes | 2026-04-04 10:00:10 | Hash: d4e5f6...
  ✅ 003 | multi_tenant | 2026-04-04 10:00:20 | Hash: g7h8i9...
```

---

## Migration Manifest

**migration_manifest.json**:

```json
{
  "version": "4.0.0",
  "last_applied": "2026-04-04T10:00:20Z",
  "migrations": [
    {
      "id": "001",
      "name": "initial_schema",
      "description": "Core tables: tasks, genesis_logs, checkpoints, agent_metrics",
      "file": "001_initial_schema.sql",
      "checksum": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
      "applied_at": "2026-04-04T10:00:00Z"
    },
    {
      "id": "002",
      "name": "add_indexes",
      "description": "Add performance indexes on genesis_logs, tasks",
      "file": "002_add_indexes.sql",
      "checksum": "d4e5f6g7h8i9j0k1l2m3n4o5p6a1b2c3",
      "applied_at": "2026-04-04T10:00:10Z"
    }
  ]
}
```

---

## Migration 001 — Initial Schema

**File**: `db/migrations/001_initial_schema.sql`

```sql
-- ─────────────────────────────────────────────────────────────
-- INITIAL SCHEMA — Core Tables for UAP v4.0
-- ─────────────────────────────────────────────────────────────

-- Tasks table (operational state)
CREATE TABLE IF NOT EXISTS tasks (
  task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL,
  description TEXT NOT NULL,
  agent_hint VARCHAR(100),
  assigned_agent VARCHAR(100) NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed
  trust_score NUMERIC(3, 2) DEFAULT 0.6,
  dry_run BOOLEAN DEFAULT FALSE,
  budget_max INT DEFAULT 1000,
  result JSONB,
  error_msg TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Genesis logs (immutable audit trail)
CREATE TABLE IF NOT EXISTS genesis_logs (
  id BIGSERIAL PRIMARY KEY,
  task_id UUID NOT NULL REFERENCES tasks(task_id),
  org_id UUID NOT NULL,
  agent VARCHAR(100) NOT NULL,
  action VARCHAR(100) NOT NULL,
  status VARCHAR(50) NOT NULL,  -- completed, failed, pending
  guards_passed INT DEFAULT 0,
  guards_total INT DEFAULT 9,
  notes TEXT,
  metadata JSONB,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Checkpoints (state snapshots for rollback)
CREATE TABLE IF NOT EXISTS checkpoints (
  checkpoint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL,
  label VARCHAR(255),
  state_snapshot JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent metrics (EBDI PAD telemetry)
CREATE TABLE IF NOT EXISTS agent_metrics (
  id BIGSERIAL PRIMARY KEY,
  org_id UUID NOT NULL,
  agent VARCHAR(100) NOT NULL,
  pleasure NUMERIC(3, 2),
  arousal NUMERIC(3, 2),
  dominance NUMERIC(3, 2),
  trust_score NUMERIC(3, 2),
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_versions (
  id SERIAL PRIMARY KEY,
  version INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  checksum VARCHAR(64) NOT NULL,
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create composite indexes
CREATE INDEX idx_tasks_org_status ON tasks(org_id, status);
CREATE INDEX idx_genesis_org_timestamp ON genesis_logs(org_id, timestamp DESC);
CREATE INDEX idx_agent_metrics_org_agent ON agent_metrics(org_id, agent);
```

---

## Migration 002 — Performance Indexes

**File**: `db/migrations/002_add_indexes.sql`

```sql
-- ─────────────────────────────────────────────────────────────
-- PERFORMANCE INDEXES — Optimize Query Performance
-- ─────────────────────────────────────────────────────────────

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_genesis_agent
  ON genesis_logs(agent);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_genesis_action
  ON genesis_logs(action);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_agent
  ON tasks(assigned_agent);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_checkpoints_org
  ON checkpoints(org_id, created_at DESC);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_genesis_search
  ON genesis_logs USING gin(to_tsvector('english', notes));

-- UUID indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_tasks_id
  ON tasks(task_id);

CREATE INDEX IF NOT EXISTS idx_genesis_task_id
  ON genesis_logs(task_id);
```

---

## Migration 003 — Multi-Tenant Support

**File**: `db/migrations/003_multi_tenant.sql`

```sql
-- ─────────────────────────────────────────────────────────────
-- MULTI-TENANT SUPPORT — Authentication & RBAC
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS organizations (
  org_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(org_id),
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) DEFAULT 'operator',  -- admin, operator, viewer, healer
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_users_email_org ON users(email, org_id);

CREATE TABLE IF NOT EXISTS permissions (
  id SERIAL PRIMARY KEY,
  org_id UUID NOT NULL REFERENCES organizations(org_id),
  role VARCHAR(50) NOT NULL,
  resource VARCHAR(100) NOT NULL,
  action VARCHAR(50) NOT NULL,
  UNIQUE(org_id, role, resource, action)
);

-- Add org_id to existing tables
ALTER TABLE tasks ADD COLUMN org_id UUID;
ALTER TABLE genesis_logs ADD COLUMN org_id UUID;
ALTER TABLE checkpoints ADD COLUMN org_id UUID;
ALTER TABLE agent_metrics ADD COLUMN org_id UUID;

-- Create row-level security policy
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE genesis_logs ENABLE ROW LEVEL SECURITY;
```

---

## Migration 004 — Rate Limiting

**File**: `db/migrations/004_rate_limits.sql`

```sql
-- ─────────────────────────────────────────────────────────────
-- RATE LIMITING — Per-User & Per-Endpoint Quotas
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS rate_limits (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL,
  endpoint VARCHAR(255) NOT NULL,
  request_count INT DEFAULT 0,
  window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  window_end TIMESTAMP,
  UNIQUE(user_id, endpoint, window_start)
);

CREATE INDEX idx_rate_limits_user_endpoint
  ON rate_limits(user_id, endpoint, window_start DESC);

CREATE TABLE IF NOT EXISTS user_tasks_quota (
  user_id UUID PRIMARY KEY,
  tasks_submitted INT DEFAULT 0,
  quota_window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  quota_window_end TIMESTAMP
);
```

---

## Backup Strategy

### 1. Before Migration

```bash
# Full backup
pg_dump -h localhost -U uap_admin uap_genesis \
  > backups/uap_genesis_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
pg_dump -h localhost -U uap_admin uap_genesis | gzip \
  > backups/uap_genesis_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 2. Restore from Backup

```bash
# Restore database
psql -h localhost -U uap_admin uap_genesis < backup.sql

# Or from compressed
gunzip -c backup.sql.gz | psql -h localhost -U uap_admin uap_genesis
```

---

## Monitoring Migrations

### 1. Track Applied Time

```bash
# Query applied migrations
SELECT * FROM schema_versions ORDER BY id;
```

### 2. Verify Data Integrity

```bash
-- Check schema consistency
SELECT COUNT(*) as task_count FROM tasks;
SELECT COUNT(*) as genesis_count FROM genesis_logs;
SELECT COUNT(*) as checkpoint_count FROM checkpoints;

-- Verify indexes
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname='public';
```

### 3. Performance After Migration

```bash
-- Analyze query performance
ANALYZE;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

---

## Rollback Checklist

Before rolling back:

- [ ] Verify backup exists and is valid
- [ ] Stop API service
- [ ] Notify team of maintenance window
- [ ] Test rollback procedure in staging
- [ ] Have rollback command ready

**Quick Rollback**:

```bash
python scripts/migrate.py down -1  # Undo last migration
python scripts/migrate.py list     # Verify state
```

---

## Common Issues

### Migration Takes Too Long

```sql
-- Check long-running operations
SELECT * FROM pg_stat_activity
WHERE state != 'idle';

-- Increase statement timeout
SET statement_timeout = 600000;  -- 10 minutes
```

### Schema Mismatch Error

```bash
# Force reapply checksum
python scripts/migrate.py verify --fix
```

### Duplicate Key Error

```sql
-- Find duplicates
SELECT email, COUNT(*) FROM users
GROUP BY email HAVING COUNT(*) > 1;

-- Clean duplicates
DELETE FROM users WHERE id NOT IN (
  SELECT MIN(id) FROM users GROUP BY email
);
```

---

**Version**: 4.0.0
**Database**: PostgreSQL 14+
**Last Migration**: 2026-04-04
