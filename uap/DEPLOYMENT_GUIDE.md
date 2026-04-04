# DEPLOYMENT GUIDE — UAP v4.0 Production

**Version**: 4.0.0
**Status**: Production Ready
**Last Updated**: 2026-04-04

---

## 📋 Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Database Setup](#database-setup)
5. [SSL/TLS Configuration](#ssltls-configuration)
6. [Running Tests](#running-tests)
7. [Health Checks](#health-checks)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+) or macOS (Monterey+)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Memory**: 4GB minimum, 8GB recommended
- **Disk**: 20GB free space
- **Python**: 3.9+ (for local development)

### Required Services

- PostgreSQL 14+ (for Genesis Record persistence)
- Ollama 0.1+ (for local LLM)
- Redis 7+ (optional, for caching)

### Tools

```bash
# Install Docker & Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Verify
docker --version
docker-compose --version
```

---

## Environment Setup

### 1. Clone Repository

```bash
cd /opt/uap
git clone <repo-url> .
cd uap
```

### 2. Create `.env` File

```bash
# .env (do NOT commit this file)

# === AUTHENTICATION ===
JWT_SECRET=your-secret-key-min-32-chars-$(openssl rand -hex 32)
JWT_EXPIRY=86400  # 24 hours

# === DATABASE ===
PG_HOST=postgres
PG_PORT=5432
PG_USER=uap_admin
PG_PASSWORD=generated-secure-password-$(openssl rand -base64 32)
PG_DB=uap_genesis
PG_POOL_SIZE=20

# === API ===
FLASK_ENV=production
DEBUG=False
API_HOST=0.0.0.0
API_PORT=8002
API_LOG_LEVEL=INFO

# === WEBSOCKET ===
WS_HOST=0.0.0.0
WS_PORT=8004
WS_BROADCAST_INTERVAL=0.2  # 200ms for <500ms telemetry

# === OLLAMA (Local LLM) ===
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=deepseek-coder-v2

# === RATE LIMITING ===
USER_TASK_QUOTA=100  # tasks/hour
ENDPOINT_REQ_QUOTA=1000  # requests/min

# === CRISIS MODE ===
CRISIS_AROUSAL_THRESHOLD=0.7
CRISIS_RATE_LIMIT_BYPASS=true

# === LOGGING ===
LOG_LEVEL=INFO
LOG_FILE=/var/log/uap/app.log
ENABLE_PROMETHEUS=true

# === SECURITY ===
CORS_ORIGINS=https://admin.example.com,https://app.example.com
SECURE_COOKIES=true
HTTP_ONLY=true
```

### 3. Generate Secure Keys

```bash
# Generate JWT secret
openssl rand -base64 32

# Generate DB password
openssl rand -base64 32

# Store in .env and secure with restrictive permissions
chmod 600 .env
```

---

## Docker Deployment

### 1. Docker Compose File (Production)

Create `docker-compose.prod.yml`:

```yaml
version: "3.9"

services:
  # ─────────────────────────────────────────────────────────────
  # POSTGRESQL — Genesis Record Database
  # ─────────────────────────────────────────────────────────────
  postgres:
    image: postgres:15-alpine
    container_name: uap-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${PG_USER}
      POSTGRES_PASSWORD: ${PG_PASSWORD}
      POSTGRES_DB: ${PG_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./db/migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${PG_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - uap-network
    restart: always

  # ─────────────────────────────────────────────────────────────
  # OLLAMA — Local LLM Service
  # ─────────────────────────────────────────────────────────────
  ollama:
    image: ollama/ollama:latest
    container_name: uap-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    environment:
      OLLAMA_NUM_PARALLEL: 2
      OLLAMA_MAX_LOADED_MODELS: 1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - uap-network
    restart: always

  # ─────────────────────────────────────────────────────────────
  # API BACKEND — Flask + Auth + Integrations
  # ─────────────────────────────────────────────────────────────
  api:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: uap-api
    ports:
      - "8002:8002"
    environment:
      - FLASK_ENV=production
      - API_PORT=8002
      - PG_HOST=postgres
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      postgres:
        condition: service_healthy
      ollama:
        condition: service_healthy
    volumes:
      - ./uap/backend:/app/backend
      - api-logs:/var/log/uap
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - uap-network
    restart: always

  # ─────────────────────────────────────────────────────────────
  # WEBSOCKET SERVER — Real-Time Telemetry
  # ─────────────────────────────────────────────────────────────
  websocket:
    build:
      context: .
      dockerfile: Dockerfile.websocket
    container_name: uap-websocket
    ports:
      - "8004:8004"
    environment:
      - WS_PORT=8004
      - PG_HOST=postgres
    depends_on:
      - postgres
    networks:
      - uap-network
    restart: always

  # ─────────────────────────────────────────────────────────────
  # FRONTEND — Static Files + SPA
  # ─────────────────────────────────────────────────────────────
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: uap-frontend
    ports:
      - "8003:8003"
    environment:
      - NODE_ENV=production
      - API_URL=http://api:8002
      - WS_URL=ws://websocket:8004
    depends_on:
      - api
    networks:
      - uap-network
    restart: always

  # ─────────────────────────────────────────────────────────────
  # NGINX — Reverse Proxy + Load Balancer
  # ─────────────────────────────────────────────────────────────
  nginx:
    image: nginx:latest-alpine
    container_name: uap-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
      - frontend
    networks:
      - uap-network
    restart: always

volumes:
  pgdata:
  ollama-data:
  api-logs:

networks:
  uap-network:
    driver: bridge
```

### 2. Deploy

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f api
```

---

## Database Setup

### 1. Apply Migrations

```bash
# Connect to container
docker exec -it uap-postgres psql -U uap_admin -d uap_genesis

# Or run from host
python scripts/migrate.py up --all
```

### 2. Create Initial Schema

```sql
-- Users table
CREATE TABLE users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) DEFAULT 'operator',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Permissions
CREATE TABLE permissions (
  id SERIAL PRIMARY KEY,
  org_id UUID NOT NULL,
  role VARCHAR(50) NOT NULL,
  resource VARCHAR(100) NOT NULL,
  action VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rate limits
CREATE TABLE rate_limits (
  user_id UUID PRIMARY KEY,
  task_count INT DEFAULT 0,
  window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_users_org ON users(org_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_genesis_org ON genesis_logs(org_id);
```

### 3. Seed Demo Data

```bash
python scripts/seed_demo_data.py
```

---

## SSL/TLS Configuration

### 1. Generate Self-Signed Certificates (Development)

```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -out ssl/cert.pem -keyout ssl/key.pem \
  -days 365 \
  -subj "/CN=localhost"
```

### 2. Configure Nginx for HTTPS

```nginx
server {
    listen 443 ssl;
    server_name admin.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://frontend:8003;
        proxy_set_header Host $host;
    }
}
```

---

## Running Tests

### 1. Unit Tests

```bash
cd uap
pytest tests/test_api.py -v
pytest tests/test_phase3_auth.py -v
```

### 2. Integration Tests

```bash
pytest tests/test_phase2_integration.py -v
pytest tests/test_phase4_e2e.py -v
```

### 3. Code Coverage

```bash
pytest --cov=uap.backend --cov-report=html tests/

# View coverage report
open htmlcov/index.html
```

### 4. Load Testing

```bash
# Using locust
pip install locust
locust -f tests/load_test.py --host=http://localhost:8002
```

---

## Health Checks

### 1. API Health

```bash
curl -s http://localhost:8002/health | jq .
```

**Expected Response**:

```json
{
  "status": "healthy",
  "timestamp": "2026-04-04T12:00:00Z",
  "services": {
    "database": "connected",
    "cache": "connected",
    "ollama": "connected"
  }
}
```

### 2. WebSocket Health

```bash
# Connect to WebSocket
wscat -c ws://localhost:8004/

# Subscribe to telemetry
{"action": "subscribe", "channel": "telemetry"}
```

### 3. Database Health

```bash
docker exec -it uap-postgres psql -U uap_admin -d uap_genesis -c \
  "SELECT COUNT(*) FROM genesis_logs;"
```

---

## Monitoring

### 1. Prometheus Metrics

```bash
# Access metrics endpoint
curl -s http://localhost:8002/metrics | head -20
```

### 2. Logs

```bash
# View application logs
docker logs -f uap-api

# Tail logs
tail -f /var/log/uap/app.log
```

### 3. Performance Monitoring

```bash
# CPU/Memory usage
docker stats uap-api

# Database connections
docker exec -it uap-postgres psql -U uap_admin -d uap_genesis -c \
  "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"
```

---

## Troubleshooting

### Connection Refused

```bash
# Check if port is in use
lsof -i :8002

# Kill process using port
kill -9 <PID>

# Or use different port in .env
API_PORT=8005
```

### Out of Memory

```bash
# Increase docker memory limit
# Edit docker-compose.yml:
# services:
#   api:
#     mem_limit: 2g
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
docker exec -it uap-postgres psql -U uap_admin -d uap_genesis

# Check logs
docker logs uap-postgres

# Reset database
docker-compose down -v
docker-compose up postgres
```

### WebSocket Connection Failed

```bash
# Check WebSocket logs
docker logs uap-websocket

# Verify endpoint is accessible
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  http://localhost:8004/
```

---

## Rollback Procedures

### 1. Previous Version

```bash
# List available versions
git tag | grep release

# Checkout previous release
git checkout release-v3.9.0

# Rebuild and restart
docker-compose build api
docker-compose up -d api
```

### 2. Database Rollback

```bash
# Revert last migration
python scripts/migrate.py down -1

# Or backup & restore
pg_dump -h localhost -U uap_admin uap_genesis > backup.sql
dropdb -h localhost -U uap_admin uap_genesis
createdb -h localhost -U uap_admin uap_genesis
psql -h localhost -U uap_admin uap_genesis < backup.sql
```

### 3. Emergency Reset

```bash
# Full reset (CAUTION: loses all data!)
docker-compose down -v
docker-compose up -d

# Re-seed demo data
python scripts/seed_demo_data.py
```

---

## Production Checklist

- [ ] JWT_SECRET is strong (32+ chars)
- [ ] Database password is secure
- [ ] SSL/TLS certificates installed
- [ ] Rate limits configured
- [ ] Monitoring/alerting enabled
- [ ] Logs backed up
- [ ] Backup plan documented
- [ ] Team trained on operations
- [ ] Disaster recovery tested

---

**Support**: For issues, contact: ops@example.com | Slack: #uap-production
