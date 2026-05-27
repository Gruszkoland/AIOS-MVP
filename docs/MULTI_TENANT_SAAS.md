# Multi-Tenant SaaS Architecture — ADRION 369

## Executive Summary

**Isolation Model:** Row-Level Security (RLS) + Schema Separation
**Tenant Identification:** Header (X-Tenant-ID), Subdomain, or JWT claim
**Database Segregation:** Per-tenant columns with PostgreSQL RLS policies
**Billing Model:** Subscription tiers (free, pro, enterprise)
**API Surface:** 6 new tenant management endpoints

---

## 1. MULTI-TENANCY MODEL

### Logical Architecture

```
Public APIs (no tenant context required)
  ├── POST /api/v1/tenant/ — Create new tenant
  └── GET /api/v1/tenant/my-tenants — List user's tenants

Protected APIs (tenant_required decorator)
  ├── GET /api/v1/jobs — Tenant-scoped jobs
  ├── POST /api/v1/jobs — Create tenant job
  ├── GET /api/v1/bids — Tenant-scoped bids
  ├── POST /api/v1/bids — Create tenant bid
  ├── GET /api/v1/tenant/ — Tenant details
  ├── GET /api/v1/tenant/members — List members
  ├── POST /api/v1/tenant/members — Invite member
  └── GET /api/v1/tenant/usage — Usage stats
```

### Tenant Context Flow

```
1. Request arrives with:
   - X-Tenant-ID header: "550e8400-e29b-41d4-a716-446655440000"
   OR subdomain: "acme.adrion369.dev" → lookup tenants.slug='acme'
   OR JWT claim: { tenant_id: "..." }

2. Middleware:
   - Validates tenant exists & active
   - Sets PostgreSQL: SET app.current_tenant_id = '550e8400-...'
   - Sets Flask g.tenant_context

3. All queries:
   - RLS policies filter by current_tenant_id
   - Implicit row filtering (no app-level logic needed)

4. Data is isolated at DB layer:
   SELECT * FROM jobs;  -- Returns only current tenant's jobs
   -- (RLS automatically applies WHERE tenant_id = current_tenant_id)
```

---

## 2. ROW-LEVEL SECURITY (RLS) POLICIES

### PostgreSQL RLS Setup

```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE bids ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy: users can only see/modify their own tenant's data
CREATE POLICY jobs_tenant_isolation ON jobs
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY jobs_tenant_insert ON jobs
  WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Same for bids, users, etc.
```

### Security Guarantees

- **No Cross-Tenant Data Leakage:** Even if app bug bypasses middleware, RLS prevents row access
- **No Schema Pollution:** Single schema, but logically separated per tenant
- **Audit Trail:** All access logged via PostgreSQL's audit trigger
- **Cost Efficient:** Single DB instance (no per-tenant DBs)
- **Scalable:** RLS policies scale to 1000s of tenants

---

## 3. TENANT IDENTIFICATION STRATEGIES

### Option 1: X-Tenant-ID Header (API-first)

```bash
curl -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  http://localhost:8003/api/v1/jobs
```

**Pros:** Explicit, RESTful
**Cons:** Client must pass header (stateless)

### Option 2: Subdomain Routing (SaaS-traditional)

```
acme.adrion369.dev/api/v1/jobs
  ↓ (lookup tenants WHERE slug='acme')
  ↓ tenant_id = 550e8400-...
  ↓ RLS filters data
```

**Pros:** User-friendly, multiple workspaces per user
**Cons:** DNS/routing overhead, wildcard certs needed

### Option 3: JWT Claim (Authenticated)

```json
{
  "sub": "user-123",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "alice@acme.com"
}
```

**Pros:** Integrated with auth, stateless
**Cons:** Requires JWT middleware

### Priority (Extraction Order)

1. Header (explicit)
2. Subdomain (implicit)
3. JWT (fallback)
4. Query param `?_debug_tenant_id=` (dev only)

---

## 4. DATABASE SCHEMA

### Tenants Table

```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE,           -- "ACME Corp"
    slug VARCHAR(255) UNIQUE,           -- "acme"
    subscription_tier VARCHAR(50),      -- "free", "pro", "enterprise"
    created_at TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);
```

### Tenant Members (Roles)

```sql
CREATE TABLE tenant_members (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants,
    user_id UUID,
    role VARCHAR(50),                   -- "owner", "admin", "member", "viewer"
    UNIQUE(tenant_id, user_id)
);
```

### Tenant-Scoped Tables

```sql
ALTER TABLE jobs ADD COLUMN tenant_id UUID REFERENCES tenants;
ALTER TABLE bids ADD COLUMN tenant_id UUID REFERENCES tenants;
ALTER TABLE users ADD COLUMN tenant_id UUID REFERENCES tenants;

-- Indexes for query performance
CREATE INDEX idx_jobs_tenant ON jobs(tenant_id);
CREATE INDEX idx_bids_tenant ON bids(tenant_id);
```

---

## 5. BILLING & QUOTAS

### Subscription Tiers

| Feature              | Free   | Pro    | Enterprise |
|----------------------|--------|--------|-----------|
| **Jobs/month**       | 10     | 500    | Unlimited |
| **Team members**     | 1      | 10     | 50+       |
| **API rate limit**   | 100/hr | 10k/hr | Custom    |
| **Data retention**   | 30 d   | 1 year | Unlimited |
| **Support**          | Email  | Slack  | Dedicated |
| **Custom integrations** | ✗ | ✓ | ✓ |

### Enforcement (Application Layer)

```python
@tenant_required
def create_job():
    tenant = get_tenant()

    # Check quota
    job_count = get_job_count_this_month(tenant.id)
    quota = get_quota(tenant.subscription_tier)['jobs_per_month']

    if job_count >= quota:
        return {"error": "Job quota exceeded"}, 429

    # Create job with tenant_id
    create_job(tenant_id=tenant.id, ...)
```

---

## 6. API ENDPOINTS

### Tenant Management

| Endpoint                    | Method | Auth | Purpose                     |
|-----------------------------|--------|------|---------------------------|
| `/api/v1/tenant/`           | GET    | Yes  | Get current tenant details |
| `/api/v1/tenant/`           | POST   | Yes  | Create new tenant         |
| `/api/v1/tenant/my-tenants` | GET    | Yes  | List user's tenants       |
| `/api/v1/tenant/members`    | GET    | Yes  | List tenant members       |
| `/api/v1/tenant/members`    | POST   | Yes  | Invite member (owner/admin)|
| `/api/v1/tenant/members/{uid}` | DELETE | Yes | Remove member (owner/admin)|
| `/api/v1/tenant/usage`      | GET    | Yes  | Usage stats (jobs, cost)  |

### Example: Create Tenant

```bash
curl -X POST http://localhost:8003/api/v1/tenant/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ACME Corp",
    "slug": "acme"
  }'

# Response
{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "ACME Corp",
  "slug": "acme",
  "created_at": "2026-05-27T10:30:00Z"
}
```

### Example: Invite Member

```bash
curl -X POST http://localhost:8003/api/v1/tenant/members \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-456",
    "role": "admin"
  }'
```

---

## 7. DATA ISOLATION GUARANTEES

### Scenario: Malicious Query

```python
# Developer writes unsafe query
jobs = db.execute("SELECT * FROM jobs WHERE status='active'")
# WITHOUT tenant filter
```

**Without RLS:** Returns ALL jobs from ALL tenants ✗ SECURITY BREACH

**With RLS:** Returns only current tenant's jobs ✓ PROTECTED

```sql
SELECT * FROM jobs WHERE status='active';
-- PostgreSQL internally adds:
-- WHERE status='active' AND tenant_id = current_setting('app.current_tenant_id')::uuid
```

### Scenario: Database Compromise

If attacker gains DB access:
- Can see all rows with `app.current_tenant_id=NULL` (super-admin view)
- RLS superuser bypass requires PostgreSQL `ROLE` with `BYPASSRLS` (rare)
- Audit log tracks all access (`audit_log` table)

---

## 8. MIGRATION GUIDE

### Step 1: Apply Schema Migration

```bash
cd arbitrage
alembic upgrade head  # Applies multi_tenant_rls migration

# Or manually
psql -d adrion_prod < migrations/0006_multi_tenant_rls.py
```

### Step 2: Register Tenant Blueprint

```python
# arbitrage/app.py
from arbitrage.blueprints.tenant_bp import tenant_bp

def create_app():
    ...
    app.register_blueprint(tenant_bp)  # Register /api/v1/tenant/* routes
    return app
```

### Step 3: Add Tenant Middleware

```python
# arbitrage/app.py
from arbitrage.tenant import extract_tenant_from_request, set_tenant_context

@app.before_request
def set_tenant_context_middleware():
    tenant_id, source = extract_tenant_from_request()
    if tenant_id:
        # Set PostgreSQL session var
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT set_tenant_context(%s)", (tenant_id,))
        cursor.close()
```

### Step 4: Update Existing Endpoints

```python
# Add @tenant_required to protected routes
from arbitrage.tenant import tenant_required

@jobs_bp.route("/", methods=["GET"])
@tenant_required
def list_jobs():
    # tenant_id automatically filtered via RLS
    ...
```

### Step 5: Migrate Existing Data (one-time)

```sql
-- Assign all existing data to "default" tenant
INSERT INTO tenants (id, name, slug, active)
  VALUES ('550e8400-default', 'Default Tenant', 'default', TRUE);

UPDATE jobs SET tenant_id = '550e8400-default' WHERE tenant_id IS NULL;
UPDATE bids SET tenant_id = '550e8400-default' WHERE tenant_id IS NULL;
UPDATE users SET tenant_id = '550e8400-default' WHERE tenant_id IS NULL;
```

---

## 9. MONITORING & AUDITING

### Audit Log Query

```sql
SELECT tenant_id, user_id, action, table_name, created_at
FROM audit_log
WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY created_at DESC
LIMIT 100;
```

### Tenant Usage Dashboard

```bash
curl -H "X-Tenant-ID: 550e8400-..." \
  http://localhost:8003/api/v1/tenant/usage

# Response
{
  "jobs": 42,
  "bids": 156,
  "members": 5,
  "total_cost": 2400.00,
  "quota": {
    "jobs_per_month": 500,
    "team_members": 10
  }
}
```

---

## 10. SCALING CONSIDERATIONS

### Single DB (Current: < 1000 tenants)

- All tenants in one PostgreSQL instance
- RLS handles isolation
- Backups/recovery for entire SaaS
- **Cost:** ~$500/mo (shared infrastructure)

### Multi-Database (Future: > 10k tenants)

- Tenant routing layer
- Each tier (free, pro, enterprise) on separate DB
- Sharding by `tenant_id % shard_count`
- **Cost:** ~$5k/mo (dedicated infrastructure)

### Migration Path

1. Document tenant → shard mapping
2. Add routing layer (e.g., Apache Kafka consumer)
3. Dual-write to new DB during cutover
4. Validate data sync
5. DNS failover

---

## 11. KNOWN LIMITATIONS

- **RLS Overhead:** ~5-10% latency increase (negligible for most apps)
- **Complex Queries:** Subqueries must include tenant context
- **Cross-Tenant Reports:** Requires superuser role (not in app)
- **No Multi-Tenant Transactions:** Each tenant isolation is independent

---

## 12. TESTING

### Unit Tests

```python
def test_tenant_isolation():
    tenant_a_id = create_tenant("A", "a")
    tenant_b_id = create_tenant("B", "b")

    set_tenant_context(tenant_a_id)
    create_job(tenant_id=tenant_a_id, name="Job A")

    set_tenant_context(tenant_b_id)
    jobs = list_jobs()  # Should only see Job B, not Job A
    assert len(jobs) == 0
```

### Integration Tests

```python
def test_rls_enforcement():
    # Connect as user in Tenant A
    conn_a = connect(tenant_id=tenant_a_id)

    # Should see only Tenant A data
    assert job_count(conn_a) == 5

    # Switch to Tenant B
    conn_b = connect(tenant_id=tenant_b_id)
    assert job_count(conn_b) == 3
```

---

**Last Updated:** 2026-05-27
**Next Phase:** Multi-region tenant failover (Q3 2026)
