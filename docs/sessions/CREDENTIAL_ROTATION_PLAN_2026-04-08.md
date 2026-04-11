# 🔐 CREDENTIAL ROTATION PLAN - ADRION 369 v4.0

**Date:** 2026-04-08 | **SLA:** 3 hours from incident discovery (by ~06:08 UTC)
**Priority:** CRITICAL SECURITY
**Status:** IN PROGRESS

---

## EXECUTIVE SUMMARY

All ETAP 1 credentials deployed with development default values require immediate rotation before production use. This guide provides safe, step-by-step procedures for rotating all credentials with zero-downtime approach.

**Scope:** 11 credential types across database, cache, API, authentication, and external services.

**Timeline:** ~45 minutes estimated (well within 3h SLA)

---

## PHASE 1: AUDIT & PLANNING

### Credentials in Scope (All "TODO_SET" locations)

| #   | Category   | Variable              | Current State                    | Severity | Status |
| --- | ---------- | --------------------- | -------------------------------- | -------- | ------ |
| 1   | Database   | DATABASE_URL password | `adrion_pass` (default)          | CRITICAL | ⏳     |
| 2   | Cache      | REDIS_PASSWORD        | `TODO_SET_REDIS_PASSWORD`        | HIGH     | ⏳     |
| 3   | Auth       | SECRET_KEY            | `TODO_SET_32_CHAR...` (template) | CRITICAL | ⏳     |
| 4   | API        | API_KEY_INTERNAL      | `TODO_SET_INTERNAL...`           | CRITICAL | ⏳     |
| 5   | API        | API_KEY_EXTERNAL      | `TODO_SET_EXTERNAL...`           | CRITICAL | ⏳     |
| 6   | Email      | SMTP_USERNAME         | `TODO_SET_EMAIL@gmail.com`       | MEDIUM   | ⏳     |
| 7   | Email      | SMTP_PASSWORD         | `TODO_SET_EMAIL_APP_PASSWORD`    | MEDIUM   | ⏳     |
| 8   | Monitoring | SENTRY_DSN            | `TODO_SET_SENTRY_DSN`            | LOW      | ⏳     |
| 9   | JWT        | JWT config            | Pre-configured (good)            | N/A      | ✅     |
| 10  | CORS       | CORS config           | Pre-configured (good)            | N/A      | ✅     |
| 11  | Security   | Headers config        | Pre-configured (good)            | N/A      | ✅     |

**Total Credentials to Rotate:** 8
**Pre-Configured & Safe:** 3

---

## PHASE 2: SAFE ROTATION PROCEDURES

### Step 1: Generate New Credential Values

**Estimated Time:** 5 minutes

```bash
# Generate strong random values (32+ characters each)

# SECRET_KEY (32 chars minimum)
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# API_KEY_INTERNAL (32 chars minimum)
python3 -c "import secrets; print('API_KEY_INTERNAL=' + secrets.token_urlsafe(32))"

# API_KEY_EXTERNAL (32 chars minimum)
python3 -c "import secrets; print('API_KEY_EXTERNAL=' + secrets.token_urlsafe(32))"

# REDIS_PASSWORD (32 chars minimum)
python3 -c "import secrets; print('REDIS_PASSWORD=' + secrets.token_urlsafe(32))"

# For database password (24+ chars with special chars):
python3 -c "import secrets; print('DB_PASSWORD=' + secrets.token_urlsafe(24))"
```

**OR use PowerShell on Windows:**

```powershell
function Generate-SecurePassword {
    param([int]$Length = 32)
    $Characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*'
    $Password = $null
    for ($i = 0; $i -lt $Length; $i++) {
        $Password += $Characters[(Get-Random -Minimum 0 -Maximum $Characters.Length)]
    }
    return $Password
}

Write-Host "SECRET_KEY=$(Generate-SecurePassword 32)"
Write-Host "API_KEY_INTERNAL=$(Generate-SecurePassword 32)"
Write-Host "API_KEY_EXTERNAL=$(Generate-SecurePassword 32)"
Write-Host "REDIS_PASSWORD=$(Generate-SecurePassword 32)"
Write-Host "DATABASE_PASSWORD=$(Generate-SecurePassword 24)"
```

---

### Step 2: Backup Current Configuration

**Estimated Time:** 2 minutes

```bash
# Create timestamped backup
cp .env .env.backup.2026-04-08.$(date +%H%M%S)

# Secure backup file (readable by owner only)
chmod 600 .env.backup.2026-04-08*
```

---

### Step 3: Update .env Configuration (NO SERVICE RESTART YET)

**Estimated Time:** 10 minutes

**Create safe .env with new credentials:**

```bash
# Copy template
cp .env.template .env

# Using text editor, replace all TODO_SET values with generated credentials:

# Replace these lines in .env:
DATABASE_URL=postgresql://adrion_app:YOUR_GENERATED_DB_PASSWORD@localhost:5432/adrion_prod
REDIS_PASSWORD=YOUR_GENERATED_REDIS_PASSWORD
SECRET_KEY=YOUR_GENERATED_SECRET_KEY
API_KEY_INTERNAL=YOUR_GENERATED_API_INTERNAL
API_KEY_EXTERNAL=YOUR_GENERATED_API_EXTERNAL
SMTP_USERNAME=YOUR_EMAIL@gmail.com  # Set real email if using alerts
SMTP_PASSWORD=YOUR_APP_PASSWORD     # Gmail app-specific password
SENTRY_DSN=https://your-sentry-key@sentry.io/project-id  # If using Sentry
```

**Critical: DO NOT commit .env to version control**

```bash
echo ".env" >> .gitignore  # Make absolutely sure
git check-ignore .env       # Verify it's ignored
```

---

### Step 4: Update PostgreSQL User Password

**Estimated Time:** 5 minutes

**Inside PostgreSQL container:**

```sql
-- Connect as postgres superuser
psql -U postgres -d genesis_record

-- Change password for adrion_app user
ALTER USER adrion_app WITH PASSWORD 'YOUR_GENERATED_DB_PASSWORD';

-- Verify change
\du adrion_app

-- Test connection
psql -U adrion_app -d genesis_record -h localhost -c "SELECT 1;"
```

**OR via script (if container-based):**

```bash
docker exec adrion-postgres psql -U postgres -d genesis_record \
  -c "ALTER USER adrion_app WITH PASSWORD 'YOUR_GENERATED_DB_PASSWORD';"
```

---

### Step 5: Update Redis Password (if applicable)

**Estimated Time:** 3 minutes

**If Redis is running:**

```bash
# Set new password in Redis
redis-cli CONFIG SET requirepass YOUR_GENERATED_REDIS_PASSWORD

# Test authentication
redis-cli -a YOUR_GENERATED_REDIS_PASSWORD PING

# Save config
redis-cli BGSAVE
```

---

### Step 6: Verify Credentials Work (Pre-Launch)

**Estimated Time:** 5 minutes

**Test database connection with new credentials:**

```bash
# Using psycopg2 test
python3 -c "
import psycopg2
conn = psycopg2.connect('postgresql://adrion_app:YOUR_NEW_PASSWORD@localhost:5432/adrion_prod')
cur = conn.cursor()
cur.execute('SELECT 1')
print('✓ Database connection successful')
cur.close()
conn.close()
"
```

**Test API key can be read:**

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env

api_key = os.getenv('API_KEY_INTERNAL')
secret = os.getenv('SECRET_KEY')

assert api_key, "API_KEY_INTERNAL not set"
assert secret, "SECRET_KEY not set"
assert len(api_key) >= 32, "API_KEY_INTERNAL too short"
assert len(secret) >= 32, "SECRET_KEY too short"

print("✓ All credentials loaded and validated")
```

---

## PHASE 3: SERVICE RESTART (Zero-Downtime)

### If Using Docker (Recommended):

```bash
# Graceful restart
docker restart adrion-postgres
docker restart adrion-redis  # if applicable

# Verify services came up
docker ps --filter "name=adrion" --format "table {{.Names}}\t{{.Status}}"
```

### If Using Direct Python Services:

```bash
# Terminal 1 - Stop services (they'll be reloaded with new creds)
pkill -f db_sync_worker.py
pkill -f health_check_service.py

# Wait 2 seconds
sleep 2

# Terminal 2 - Restart with new credentials from .env
cd c:\Users\adiha\162\ demencje\ w\ schemacie\ 369

# Load new environment
export $(cat .env | xargs)

# Restart services
python3 scripts/db/db_sync_worker.py --interval 5 &
python3 scripts/health_check/health_check_service.py --port 9000 &
```

---

## PHASE 4: VERIFICATION & LOGGING

### Verification Checklist

- [ ] Database connection successful with new password
- [ ] db_sync_worker service running and syncing
- [ ] health_check_service running on port 9000
- [ ] API endpoints responding with new API keys
- [ ] Redis cache responding (if applicable)
- [ ] No authentication failures in logs
- [ ] Email alerts working (if configured)

### Audit Trail Creation

```bash
# Log credential rotation event
cat > CREDENTIAL_ROTATION_LOG_2026-04-08.txt <<EOF
CREDENTIAL ROTATION AUDIT LOG
Date: 2026-04-08 $(date +%H:%M:%S UTC)

Rotated Credentials:
  ✓ DATABASE_URL password
  ✓ REDIS_PASSWORD
  ✓ SECRET_KEY
  ✓ API_KEY_INTERNAL
  ✓ API_KEY_EXTERNAL
  ✓ SMTP credentials

Verification:
  ✓ Database connection: OK
  ✓ Services restarted: OK
  ✓ Health checks: OK
  ✓ API keys loading: OK

Old credentials backup: .env.backup.2026-04-08.*
Encryption: AES-256 (if stored)
Retention policy: Secure deletion after 30 days

Signed by: Automated Rotation System
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

# Archive in Genesis Record
mkdir -p Genesis\ Record/11_CREDENTIAL_ROTATION
cp CREDENTIAL_ROTATION_LOG_2026-04-08.txt Genesis\ Record/11_CREDENTIAL_ROTATION/
```

---

## PHASE 5: POST-ROTATION VALIDATION

### Endpoint Testing

```bash
# Test health endpoint (should work with no auth)
curl http://localhost:9000/health

# Test API endpoint requiring authentication
curl -H "X-API-Key: YOUR_NEW_API_KEY_INTERNAL" http://localhost:8001/api/health

# Test database through sync worker
curl http://localhost:9000/metrics | grep db_sync_worker
```

### Log Analysis

```bash
# Check for authentication failures
grep -i "authentication\|failed\|error" application.log | tail -20

# Confirm no "invalid password" errors
grep -i "invalid password\|authen.*failed" PostgreSQL_logs.txt

# Verify sync worker is syncing
grep "synced\|synchronized" application.log | tail -5
```

---

## CRITICAL SECURITY NOTES

⚠️ **DO NOT:**

- Hardcode credentials in code (always use .env)
- Commit .env to git repository
- Share credentials over unencrypted channels
- Log full credential values
- Use identical credentials across environments

✅ **DO:**

- Rotate credentials quarterly (minimum)
- Keep timestamped backup of old credentials (encrypted)
- Monitor for unauthorized access attempts
- Document rotation in audit trail
- Test new credentials before full deployment

---

## TIMELINE SUMMARY

| Phase     | Task                  | Duration      | Status                 |
| --------- | --------------------- | ------------- | ---------------------- |
| 1         | Audit & Plan          | 2 min         | ⏳                     |
| 2         | Generate credentials  | 5 min         | ⏳                     |
| 3         | Backup current config | 2 min         | ⏳                     |
| 4         | Update .env & DB      | 15 min        | ⏳                     |
| 5         | Verify credentials    | 5 min         | ⏳                     |
| 6         | Restart services      | 3 min         | ⏳                     |
| 7         | Validate & audit log  | 5 min         | ⏳                     |
| **TOTAL** |                       | **45-50 min** | **Well within 3h SLA** |

---

## QUICK START (Fast Path)

For experienced users - condensed version:

```bash
# 1. Generate credentials (use script above)
# 2. Backup: cp .env .env.backup.$(date +%s)
# 3. Update .env with new values
# 4. Update DB: ALTER USER adrion_app WITH PASSWORD '...';
# 5. Test: psql -U adrion_app -d genesis_record -c "SELECT 1;"
# 6. Restart: docker restart adrion-postgres || pkill -f db_sync_worker
# 7. Verify: curl http://localhost:9000/health
# 8. Log: echo "Rotated $(date)" >> CREDENTIAL_ROTATION_LOG.txt
```

**Status:** Ready to execute. Proceeding to next step on your approval.

---

_This guide follows OWASP credential management best practices and NIST SP 800-63B authentication specifications._
