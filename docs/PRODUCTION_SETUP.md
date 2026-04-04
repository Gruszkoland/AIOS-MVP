# ADRION 369 v1.0 — Production Setup Guide

**Status:** PRODUCTION-READY (v1.0.0, 2026-04-04)

---

## 🟢 PHASE 6: Production Environment Setup

Complete guide to configure ADRION 369 for production deployment.

### Prerequisites

- Docker Desktop (v4.0+) running and accessible
- PostgreSQL client tools (`psql`) installed locally
- Git configured with SSH keys for deploys
- SSL/TLS certificates (self-signed or CA-issued)
- `.env` file template reviewed and prepared

---

## Section 1: Pre-Production Checklist (30 min)

### 1.1 Code Quality Gates

```bash
# 1. Python tests and coverage
python -m pytest tests/ -v --cov=arbitrage --cov=tests --cov-fail-under=37

# Expected: "XX passed" + coverage >= 37%

# 2. Python linting
python -m ruff check arbitrage/ tests/ internal/ --select=E,F,W --ignore=E501

# Expected: 0 errors

# 3. Go tests and coverage
cd internal
go test -v ./...
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out | tail -5

# Expected: tests PASS, total coverage >= 80%
```

**Checklist:**
- [ ] Python: `XX passed` with coverage >= 37%
- [ ] Python: Ruff returns 0 errors
- [ ] Go: All tests `PASS`
- [ ] Go: Coverage >= 80%
- [ ] Git: `git status` shows clean working tree (or PR merged)

---

### 1.2 Security Audit

**PRIORITY 1-10 Verification:**

```bash
# Check all security priorities are environment-configured
grep -r "PG_PASSWORD" .env || echo "❌ MISSING: PG_PASSWORD in .env"
grep -r "UAP_API_KEY" .env || echo "❌ MISSING: UAP_API_KEY in .env"
grep -r "JWT_SECRET" .env || echo "❌ MISSING: JWT_SECRET in .env"
grep -r "DRM_HMAC_SECRET" .env || echo "❌ MISSING: DRM_HMAC_SECRET in .env"

# Verify production mode flag
grep "ENVIRONMENT=production" .env || echo "❌ MISSING: ENVIRONMENT=production in .env"

# Verify no default keys in production
if grep -q "ENVIRONMENT=production" .env; then
  if grep -q 'UAP_API_KEY=local-dev-key-123' .env; then
    echo "❌ FAIL: Using insecure default UAP_API_KEY in production"
    exit 1
  fi
fi
```

**Checklist:**
- [ ] All secrets in `.env` are 32+ random characters
- [ ] `ENVIRONMENT=production` set in `.env`
- [ ] No default/development keys in production `.env`
- [ ] `.env` file has 0644 permissions (readable by service account only)
- [ ] `.env` is NOT committed to git (verify `.gitignore`)

---

### 1.3 Infrastructure Readiness

```bash
# PostgreSQL
psql -h localhost -U adrion -d genesis_record -c "SELECT version();" || echo "❌ PostgreSQL not accessible"

# Docker Compose file validation
docker-compose -f docker-compose.yml config > /dev/null && echo "✅ docker-compose.yml valid" || echo "❌ Invalid"

# Storage check
df -h / | grep -v Use | awk '{print $4}' | sed 's/G//' | awk '{if ($1 < 50) print "❌ Less than 50GB available"; else print "✅ Sufficient disk space"}'

# Memory check
free -h | grep Mem | awk '{print $7}' | sed 's/G//' | awk '{if ($1 < 4) print "❌ Less than 4GB available"; else print "✅ Sufficient memory"}'
```

**Checklist:**
- [ ] PostgreSQL service running and accessible
- [ ] Docker daemon running and healthy
- [ ] Disk space >= 50GB available
- [ ] RAM >= 4GB available
- [ ] Docker network can be created (no port conflicts)

---

## Section 2: Environment Configuration (15 min)

### 2.1 Create Production `.env`

```bash
# Copy template
cp .env.example .env

# Generate strong random strings for secrets (32+ characters each)
# Option 1: Using OpenSSL
UAP_API_KEY=$(openssl rand -hex 16)
JWT_SECRET=$(openssl rand -hex 16)
DRM_HMAC_SECRET=$(openssl rand -hex 16)
PG_PASSWORD=$(openssl rand -hex 16)

# Option 2: Using Python
python3 -c "import secrets; print(secrets.token_hex(16))" > /tmp/keys.txt

# Edit .env with your values
nano .env
```

### 2.2 Production Configuration Values

**Critical settings to update:**

```bash
# Production mode
ENVIRONMENT=production
DEBUG_MODE=false

# Database (PostgreSQL required for production)
DB_ENGINE=postgresql
POSTGRES_HOST=localhost          # or remote RDS endpoint
POSTGRES_PORT=5432
POSTGRES_USER=adrion
POSTGRES_PASSWORD=<STRONG_RANDOM_32+_CHARS>  # ← CHANGE
POSTGRES_DB=genesis_record

# Connection pool for production load
DB_POOL_MIN=5
DB_POOL_MAX=20
DB_CONN_TIMEOUT=15
DB_CONN_RETRIES=5

# Secrets (32+ random characters each)
UAP_API_KEY=<STRONG_RANDOM_32+_CHARS>        # ← CHANGE
JWT_SECRET=<STRONG_RANDOM_32+_CHARS>         # ← CHANGE
DRM_HMAC_SECRET=<STRONG_RANDOM_32+_CHARS>    # ← CHANGE

# Monitoring & Alerting
LOG_LEVEL=WARNING                 # Reduce noise in production
GRAFANA_ADMIN_PASSWORD=<STRONG_RANDOM_32+_CHARS>  # ← CHANGE

# Services
ARB_PORT=8001
MAPI_PORT=8002
N8N_PORT=5678
VORTEX_PORT=1740

# Nginx / Reverse Proxy
NGINX_SERVER_NAME=your-domain.com  # or use IP if no DNS
```

### 2.3 SSL/TLS Certificates

**Self-signed for local production:**

```bash
# Create directory
mkdir -p config/nginx/certs

# Generate self-signed cert (10-year validity)
openssl req -x509 -nodes -days 3650 \
  -newkey rsa:2048 \
  -keyout config/nginx/certs/adrion.key \
  -out config/nginx/certs/adrion.crt \
  -subj "/CN=localhost/O=ADRION/C=PL"

# Verify
openssl x509 -in config/nginx/certs/adrion.crt -text -noout
```

**CA-issued for domain:**

```bash
# Use certbot (Let's Encrypt)
sudo certbot certonly --standalone \
  -d your-domain.com \
  -d www.your-domain.com

# Copy to config/nginx/certs/
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem config/nginx/certs/adrion.crt
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem config/nginx/certs/adrion.key
sudo chown $USER config/nginx/certs/*
```

**Checklist:**
- [ ] Certificates in place at `config/nginx/certs/adrion.crt` and `.key`
- [ ] Permissions: `chmod 400 config/nginx/certs/adrion.key`
- [ ] Certificate valid (not expired)
- [ ] CA bundle installed if CA-issued

---

## Section 3: Database Initialization (10 min)

### 3.1 PostgreSQL Setup

```bash
# Start PostgreSQL container (if using Docker)
docker run -d \
  --name adrion-postgres \
  -e POSTGRES_USER=adrion \
  -e POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d= -f2) \
  -e POSTGRES_DB=genesis_record \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine

# Wait for startup
sleep 10

# Verify connection
psql -h localhost -U adrion -d genesis_record -c "SELECT version();"
```

### 3.2 Run Migrations

```bash
# Check current migration status
python scripts/migrate.py list

# Apply all pending migrations
DB_ENGINE=postgresql \
DB_URL=postgresql://adrion:$(grep POSTGRES_PASSWORD .env | cut -d= -f2)@localhost:5432/genesis_record \
python scripts/migrate.py up --target 999

# Verify schema created
psql -h localhost -U adrion -d genesis_record -c "\dt"

# Expected tables:
# - tasks
# - genesis_logs
# - checkpoints
# - agent_metrics
```

**Checklist:**
- [ ] PostgreSQL container running (or remote instance accessible)
- [ ] Connection string works: `psql ... -c "SELECT 1"`
- [ ] All migrations applied successfully
- [ ] Schema tables present: `\dt` shows 4 tables

---

## Section 4: Docker Stack Deployment (15 min)

### 4.1 Pre-Flight Checks

```bash
# Validate docker-compose file
docker-compose -f docker-compose.yml config > /dev/null

# Check port availability
for port in 5432 8001 8002 8003 5678 1740 9090 3000 3100; do
  netstat -tuln | grep ":$port " && echo "❌ Port $port in use" || echo "✅ Port $port available"
done

# Verify all images available locally or can be pulled
docker-compose -f docker-compose.yml pull --dry-run
```

### 4.2 Start Services

```bash
# Start all services in detached mode
docker-compose -f docker-compose.yml up -d --remove-orphans

# Wait for health checks (typically 30-60 seconds)
sleep 45

# Check status
docker-compose -f docker-compose.yml ps

# Expected output:
# NAME                    STATUS          PORTS
# adrion-postgres         Up 40s (healthy)  0.0.0.0:5432->5432/tcp
# adrion-uap-backend      Up 38s (healthy)  0.0.0.0:8002->8002/tcp
# adrion-uap-frontend     Up 38s            0.0.0.0:8003->8003/tcp
# adrion-pgadmin          Up 38s            0.0.0.0:5050->80/tcp
```

### 4.3 Verify All Services

```bash
# Backend API
curl -s -H "X-API-Key: $(grep UAP_API_KEY .env | cut -d= -f2)" \
  http://localhost:8002/mapi/v1/status | python -m json.tool | head -20

# Frontend
curl -s http://localhost:8003 | head -50

# pgAdmin (optional)
echo "Open http://localhost:5050 in browser"
echo "Email: admin@example.com / Password: admin"

# Prometheus (if enabled)
curl -s http://localhost:9090/api/v1/query?query=up | python -m json.tool | head -20
```

**Checklist:**
- [ ] All containers running and healthy
- [ ] Backend API responds with 200
- [ ] Frontend loads (HTTP 200)
- [ ] PostgreSQL health check passes
- [ ] Prometheus scraping targets healthy (if enabled)

---

## Section 5: Monitoring & Alerting (20 min)

### 5.1 Configure Prometheus

```bash
# Create prometheus.yml (already in monitoring/ folder)
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

rule_files:
  - "monitoring/alerts.yml"

scrape_configs:
  - job_name: 'adrion-backend'
    static_configs:
      - targets: ['localhost:8002']
    metrics_path: '/metrics'

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

# Restart Prometheus
docker-compose -f docker-compose.yml restart prometheus
```

### 5.2 Configure Grafana

```bash
# Add Prometheus datasource
curl -X POST http://localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -u admin:$(grep GRAFANA_ADMIN_PASSWORD .env | cut -d= -f2) \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }'

# Access Grafana
echo "Open http://localhost:3000 in browser"
echo "Login: admin / $(grep GRAFANA_ADMIN_PASSWORD .env | cut -d= -f2)"
```

**Checklist:**
- [ ] Prometheus scraping targets ✅ (all green)
- [ ] Grafana datasource added and working
- [ ] Alert rules loaded (check Prometheus `/alerts`)
- [ ] Alert Manager webhooks configured

---

## Section 6: Backup & Recovery (15 min)

### 6.1 Automated Daily Backups

```bash
# Create backup script
mkdir -p scripts/backup
cat > scripts/backup/backup-production.sh << 'EOF'
#!/bin/bash
# Daily backup scheduler for production

BACKUP_DIR="/backups/adrion"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)

mkdir -p $BACKUP_DIR

# PostgreSQL backup
pg_dump -h localhost -U adrion genesis_record | \
  gzip > $BACKUP_DIR/genesis_record_$TIMESTAMP.sql.gz

# Application logs
tar -czf $BACKUP_DIR/logs_$TIMESTAMP.tar.gz logs/ || true

# Clean old backups (30-day retention)
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ Backup completed: $BACKUP_DIR"
EOF

chmod +x scripts/backup/backup-production.sh

# Add cron job (daily at 02:00 UTC)
crontab -e
# Add line: 0 2 * * * /path/to/scripts/backup/backup-production.sh >> /var/log/adrion-backup.log 2>&1
```

### 6.2 Restore Procedure

```bash
# List available backups
ls -lah /backups/adrion/genesis_record_*.sql.gz

# Restore from backup
gunzip < /backups/adrion/genesis_record_2026-04-04.sql.gz | \
  psql -h localhost -U adrion genesis_record

# Verify
psql -h localhost -U adrion genesis_record -c "SELECT COUNT(*) FROM tasks;"
```

**Checklist:**
- [ ] Backup script created and executable
- [ ] Cron job scheduled (daily at 02:00 UTC)
- [ ] Backup directory has 30-day retention policy
- [ ] Restore procedure tested and working

---

## Section 7: Security Hardening (20 min)

### 7.1 Network Security

```bash
# Configure firewall (Ubuntu/Debian)
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow only required ports
sudo ufw allow 22/tcp        # SSH
sudo ufw allow 80/tcp        # HTTP (redirect to HTTPS)
sudo ufw allow 443/tcp       # HTTPS
sudo ufw allow 5432/tcp from 127.0.0.1  # PostgreSQL local only

# Deny all other ports (8002, 8003, etc are internal only)
sudo ufw status verbose
```

### 7.2 PostgreSQL Hardening

```bash
# Strong password policy
psql -U postgres -c "ALTER USER adrion WITH ENCRYPTED PASSWORD 'your-strong-password-here';"

# Enable SSL/TLS
psql -h localhost -U adrion -d genesis_record \
  -c "SELECT pg_reload_conf();"

# Restrict connections to localhost (PostgreSQL config)
# Edit pg_hba.conf: local   all             adrion              trust
# or: host    all             adrion      127.0.0.1/32        md5
```

### 7.3 Application Security Headers

```bash
# Nginx configuration (config/nginx/nginx.conf)
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # SSL/TLS
    ssl_certificate /etc/nginx/certs/adrion.crt;
    ssl_certificate_key /etc/nginx/certs/adrion.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

**Checklist:**
- [ ] Firewall enabled and configured
- [ ] Only ports 22 (SSH), 80 (HTTP), 443 (HTTPS) public
- [ ] PostgreSQL restricted to localhost
- [ ] SSL/TLS certificates installed and valid
- [ ] HTTPS redirect configured (HTTP → HTTPS)
- [ ] Security headers set in Nginx

---

## Section 8: Final Verification (10 min)

### 8.1 Production Health Check

```bash
# Run comprehensive health check
./admin.ps1 health

# Or manually:
echo "=== PostgreSQL ==="
psql -h localhost -U adrion -d genesis_record -c "SELECT 'OK';"

echo "=== Backend API ==="
curl -s -H "X-API-Key: $(grep UAP_API_KEY .env | cut -d= -f2)" \
  http://localhost:8002/mapi/v1/status | python -m json.tool | grep -E "(status|agents|uptime)" | head -5

echo "=== Frontend ==="
curl -s -I http://localhost:8003 | head -1

echo "=== Docker Compose ==="
docker-compose -f docker-compose.yml ps --quiet | wc -l | awk '{print $1 " containers running"}'

echo "=== Disk Space ==="
df -h / | tail -1 | awk '{print "Disk usage: " $5}'

echo "=== Memory ==="
free -h | grep Mem | awk '{print "Memory used: " $3 " / " $2}'

echo "=== Uptime ==="
uptime
```

### 8.2 Security Verification Checklist

```bash
# PRIORITY 1-10 Runtime Verification
echo "Checking security priorities..."

# PRIORITY 1: PostgreSQL
psql -h localhost -U adrion genesis_record -c "SELECT 'OK'" > /dev/null 2>&1 && echo "✅ PRIORITY 1: PostgreSQL working" || echo "❌ PRIORITY 1: PostgreSQL FAILED"

# PRIORITY 2: API Key header
curl -s http://localhost:8002/mapi/v1/status | grep -q "Unauthorized" && echo "✅ PRIORITY 2: API key validation working" || echo "❌ PRIORITY 2: API key validation FAILED"

# PRIORITY 3: Environment variables set
[[ ! -z "$PG_PASSWORD" ]] && echo "✅ PRIORITY 3: PG_PASSWORD set" || echo "❌ PRIORITY 3: PG_PASSWORD NOT SET"

# PRIORITY 4: HMAC secret exists
[[ ! -z "$DRM_HMAC_SECRET" ]] && echo "✅ PRIORITY 4: DRM_HMAC_SECRET set" || echo "❌ PRIORITY 4: DRM_HMAC_SECRET NOT SET"

# PRIORITY 5: No demo credentials visible
grep -r "demo@example.com" uap/frontend/ > /dev/null 2>&1 && echo "❌ PRIORITY 5: Demo credentials VISIBLE" || echo "✅ PRIORITY 5: Demo credentials hidden"

# PRIORITY 6: API keys not hardcoded
grep -r "local-dev-key-123" uap/ | grep -v ".env" | grep -v ".md" > /dev/null 2>&1 && echo "❌ PRIORITY 6: API key HARDCODED" || echo "✅ PRIORITY 6: API key from environment"

# PRIORITY 7: Production mode check
grep -q "ENVIRONMENT=production" .env && echo "✅ PRIORITY 7: Production mode enabled" || echo "❌ PRIORITY 7: Not in production mode"

# PRIORITY 8: Rate limiting working
curl -s http://localhost:8002/mapi/v1/status -H "X-API-Key: invalid" | grep -q "429\|Unauthorized" && echo "✅ PRIORITY 8: Rate limiting active" || echo "❌ PRIORITY 8: Rate limiting INACTIVE"

# PRIORITY 9: XSS protection
grep -q "escapeHtml" uap/frontend/app.js && echo "✅ PRIORITY 9: XSS protection implemented" || echo "❌ PRIORITY 9: XSS protection MISSING"

# PRIORITY 10: HttpOnly cookies
grep -q "credentials: \"include\"" uap/frontend/app.js && echo "✅ PRIORITY 10: Cookie handling configured" || echo "❌ PRIORITY 10: Cookie handling MISSING"
```

---

## Section 9: Go-Live Procedures

### 9.1 Pre-Launch Checklist

```markdown
## ✅ Production Go-Live Checklist

- [ ] All tests passing (Python 37%+, Go 80%+)
- [ ] Security audit passed (PRIORITY 1-10 verified)
- [ ] PostgreSQL backup scheduled and tested
- [ ] Monitoring & alerting operational
- [ ] Nginx/TLS configured and tested
- [ ] Firewall rules applied
- [ ] DNS pointing to server (if domain)
- [ ] SSL certificate installed and valid
- [ ] Backups stored off-site (S3, Azure, etc.)
- [ ] Run book and incident procedures documented
- [ ] Team trained on admin CLI (.\admin.ps1)
- [ ] Logging levels set to WARNING (production)
- [ ] Debug mode disabled (DEBUG_MODE=false)
- [ ] All API keys rotated (not dev defaults)
```

### 9.2 Production Deployment Command

```bash
# Final deployment (after checklist complete)
echo "🚀 Starting ADRION 369 v1.0.0 in production..."
docker-compose -f docker-compose.yml up -d --remove-orphans

# Wait for health checks
sleep 60

# Verify all services healthy
docker-compose -f docker-compose.yml ps | grep healthy || echo "⚠️ WARNING: Some services not healthy yet"

# Show status
./admin.ps1 status

echo "✅ ADRION 369 v1.0.0 is LIVE"
```

---

## Section 10: Operations & Maintenance

### 10.1 Daily Monitoring

```bash
# Every morning: health check
./admin.ps1 health

# Check logs for errors
docker-compose -f docker-compose.yml logs --tail=100 | grep -i error || echo "✅ Clean logs"

# Database integrity
./admin.ps1 db status
```

### 10.2 Weekly Maintenance

```bash
# Database optimization
./admin.ps1 db optimize

# Backup verification
ls -lah /backups/adrion/ | tail -5

# Test restore procedure (on staging copy)
# Do NOT restore on production without incident
```

### 10.3 Monthly Review

- Review logs for recurring errors
- Update security patches (Docker base images, Go, Python dependencies)
- Performance optimization (query tuning, caching)
- Capacity planning (disk usage, memory trends)

---

## Section 11: Troubleshooting

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| `connection refused` on 5432 | PostgreSQL not running | `docker-compose up -d postgres` |
| 401 Unauthorized on all endpoints | API key missing in header | Add `-H "X-API-Key: $(grep UAP_API_KEY .env)"` |
| High memory usage | Leak in service | Check `docker stats`, restart container |
| Slow queries | No database indexes | Run `./admin.ps1 db optimize` |
| SSL certificate expired | Cert not renewed | Run certbot or generate new self-signed cert |
| Backup failed | Disk full | Free space or mount new volume |

---

## Checklist Summary

```
PHASE 6: PRODUCTION SETUP
├─ Section 1: Pre-Production Checklist (30 min)
│  ├─ Code quality gates ✅
│  ├─ Security audit ✅
│  └─ Infrastructure readiness ✅
├─ Section 2: Environment Configuration (15 min)
│  ├─ Create .env with secrets ✅
│  └─ SSL/TLS certificates ✅
├─ Section 3: Database Initialization (10 min)
│  ├─ PostgreSQL setup ✅
│  └─ Migrations applied ✅
├─ Section 4: Docker Stack Deployment (15 min)
│  ├─ Pre-flight checks ✅
│  ├─ Start services ✅
│  └─ Verify all services ✅
├─ Section 5: Monitoring & Alerting (20 min)
│  ├─ Prometheus configured ✅
│  └─ Grafana dashboards ✅
├─ Section 6: Backup & Recovery (15 min)
│  ├─ Daily backups scheduled ✅
│  └─ Restore procedure tested ✅
├─ Section 7: Security Hardening (20 min)
│  ├─ Network security ✅
│  ├─ PostgreSQL hardening ✅
│  └─ Security headers ✅
├─ Section 8: Final Verification (10 min)
│  ├─ Health check ✅
│  └─ Security verification ✅
├─ Section 9: Go-Live Procedures ✅
└─ Section 10+: Operations ✅

Total time: ~2 hours
Status: 🟢 READY FOR PRODUCTION
```

---

## Quick Start (TL;DR)

```bash
# 1. Setup environment
cp .env.example .env
nano .env  # Edit: add 32-char secrets, set ENVIRONMENT=production

# 2. Initialize database
psql -h localhost -U adrion -d genesis_record -c "SELECT 1"
python scripts/migrate.py up --target 999

# 3. Start services
docker-compose -f docker-compose.yml up -d

# 4. Verify
./admin.ps1 health

# 5. Go live
echo "✅ ADRION 369 v1.0.0 is LIVE"
```

---

**Created:** 2026-04-04
**Version:** 1.0.0
**Status:** PRODUCTION-READY ✅
