# Oracle Cloud Deployment Guide — ADRION 369

**Cost:** $0/mo ∞ (Always-Free Tier)  
**Resources:** 2x Micro VMs (2 OCPU, 2-4GB RAM total) + 200GB storage  
**Setup Time:** 45-60 minutes

---

## Prerequisites

1. **Oracle Cloud Account** (free, requires credit card for verification only)
   - Sign up: https://www.oracle.com/cloud/free/
   - No charges if staying within free tier limits

2. **Local Tools**
   - Docker Desktop (for local testing before deployment)
   - SSH client (PuTTY on Windows or OpenSSH)
   - Git (to clone repository)

3. **Project Files** (already prepared)
   - `docker-compose.oracle.yml` — Multi-container stack for Oracle VMs
   - `scripts/oracle-setup.sh` — Automated deployment script
   - `docs/ORACLE_CLOUD_ARCHITECTURE.md` — Architecture diagram

---

## Step 1: Create Oracle Cloud Account

1. Navigate to https://www.oracle.com/cloud/free/
2. Click **Sign Up**
3. Enter email, create account
4. Verify identity (credit card required for verification, but NO charges for free tier)
5. Wait for account activation (5-10 minutes)

---

## Step 2: Create Virtual Machines in Oracle Cloud Console

### VM Configuration #1: Application Server

```
Name: adrion-app
Image: Canonical Ubuntu 22.04 LTS
Shape: VM.Standard.E2.1.Micro (always-free eligible)
  - 1 OCPU
  - 1 GB RAM
  - 50GB boot volume
Region: US Phoenix (PHX) or UK London (LHR) — always-free regions
VCN: Create new or use default
Subnet: Public
Security Group: 
  - Allow SSH (22) from your IP
  - Allow HTTP (80) from anywhere
  - Allow HTTPS (443) from anywhere
  - Allow 8003 (Flask) from anywhere
  - Allow 9090 (Prometheus) from your IP only
```

### VM Configuration #2: Database Server

```
Name: adrion-db
Image: Canonical Ubuntu 22.04 LTS
Shape: VM.Standard.E2.1.Micro (always-free eligible)
  - 1 OCPU
  - 1 GB RAM
  - 100GB boot volume
Region: Same as VM #1 (PHX or LHR)
VCN: Same as VM #1
Subnet: Private (optional, or public with restricted security group)
Security Group:
  - Allow SSH (22) from app VM only
  - Allow PostgreSQL (5432) from app VM only
  - Allow Redis (6379) from app VM only
```

---

## Step 3: Configure Network Security

### Create Ingress Rules (Oracle Cloud Console → VCN → Security Groups)

**For adrion-app Security Group:**

```
Ingress Rule 1: SSH
  Source: YOUR_IP/32
  Protocol: TCP
  Port: 22

Ingress Rule 2: HTTP
  Source: 0.0.0.0/0
  Protocol: TCP
  Port: 80

Ingress Rule 3: HTTPS
  Source: 0.0.0.0/0
  Protocol: TCP
  Port: 443

Ingress Rule 4: Flask API (8003)
  Source: 0.0.0.0/0
  Protocol: TCP
  Port: 8003

Ingress Rule 5: Prometheus (9090)
  Source: YOUR_IP/32
  Protocol: TCP
  Port: 9090

Ingress Rule 6: Grafana (3000)
  Source: YOUR_IP/32
  Protocol: TCP
  Port: 3000
```

**For adrion-db Security Group:**

```
Ingress Rule 1: SSH (from app VM)
  Source: ADRION_APP_PRIVATE_IP/32
  Protocol: TCP
  Port: 22

Ingress Rule 2: PostgreSQL (from app VM)
  Source: ADRION_APP_PRIVATE_IP/32
  Protocol: TCP
  Port: 5432

Ingress Rule 3: Redis (from app VM)
  Source: ADRION_APP_PRIVATE_IP/32
  Protocol: TCP
  Port: 6379
```

---

## Step 4: SSH into application VM and Install Docker

```bash
# SSH into adrion-app VM
ssh -i your-key.key ubuntu@<application-vm-public-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# Verify Docker installation
docker --version
docker-compose --version

# Exit and reconnect SSH for docker group to take effect
exit
ssh -i your-key.key ubuntu@<application-vm-public-ip>
```

---

## Step 5: Clone ADRION 369 Repository

```bash
# Clone repository
git clone https://github.com/your-org/ADRION-369.git
cd ADRION-369

# Or if using local copy, scp it:
# scp -r -i your-key.key ./ADRION-369 ubuntu@<app-ip>:/home/ubuntu/
```

---

## Step 6: Configure for Oracle Cloud Deployment

### 6A: Update Environment Variables

Create `.env` file in project root:

```bash
cat > .env << 'EOF'
# Oracle Cloud Deployment Configuration
ENVIRONMENT=production
LLM_BACKEND=openrouter
OPENROUTER_KEY=your-openrouter-key-here

# Database (on separate VM)
DB_HOST=<adrion-db-private-ip>
DB_PORT=5432
DB_NAME=adrion_production
DB_USER=adrion_user
DB_PASSWORD=generate-strong-password-here
DB_POOL_SIZE=10
DB_POOL_RECYCLE=3300

# Flask App
FLASK_ENV=production
SECRET_KEY=generate-random-secret-key-here
CORS_ALLOWED_ORIGIN=http://<app-vm-public-ip>:8003

# UAP Orchestrator
MAPI_HOST=0.0.0.0
MAPI_PORT=8002
UAP_API_KEY=generate-random-api-key-here

# Monitoring
PROMETHEUS_RETENTION=720h
GRAFANA_ADMIN_PASSWORD=generate-random-password-here

EOF
```

### 6B: Update docker-compose File

Create `docker-compose.oracle.yml`:

```yaml
version: '3.8'

services:
  # Flask API (localhost:8003)
  adrion-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: adrion-api
    env_file:
      - .env
    ports:
      - "8003:8003"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/api/arbitrage/status"]
      interval: 30s
      timeout: 5s
      retries: 5

  # UAP Orchestrator (localhost:8002)
  adrion-uap:
    build:
      context: uap
      dockerfile: Dockerfile
    container_name: adrion-uap
    env_file:
      - .env
    ports:
      - "8002:8002"
    depends_on:
      adrion-api:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/mapi/v1/health"]
      interval: 30s
      timeout: 5s
      retries: 5

  # Prometheus (localhost:9090)
  prometheus:
    image: prom/prometheus:latest
    container_name: adrion-prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=720h'
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-q", "-O", "-", "http://localhost:9090/-/ready"]
      interval: 30s
      timeout: 5s
      retries: 5

  # Grafana (localhost:3000)
  grafana:
    image: grafana/grafana:latest
    container_name: adrion-grafana
    env_file:
      - .env
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 5s
      retries: 5

volumes:
  prometheus-data:
  grafana-data:
```

---

## Step 7: Deploy Database VM

### SSH into Database VM

```bash
ssh -i your-key.key ubuntu@<database-vm-private-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
```

### Deploy PostgreSQL + Redis

Create `docker-compose.db.yml` on database VM:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: adrion-postgres
    environment:
      POSTGRES_DB: adrion_production
      POSTGRES_USER: adrion_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U adrion_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: adrion-redis
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
  redis-data:
```

```bash
# Copy compose file
cat > docker-compose.db.yml << 'EOF'
[content above]
EOF

# Set database password
export DB_PASSWORD="your-strong-password-here"

# Start services
docker-compose -f docker-compose.db.yml up -d

# Verify PostgreSQL is running
docker-compose -f docker-compose.db.yml logs postgres

# Verify Redis is running
docker-compose -f docker-compose.db.yml logs redis
```

---

## Step 8: Deploy Application VM

Back on application VM:

```bash
# Copy environment file (if not already there)
# scp -i your-key.key .env ubuntu@<app-ip>:/home/ubuntu/ADRION-369/

# Start application stack
docker-compose -f docker-compose.oracle.yml up -d

# Check all services
docker-compose -f docker-compose.oracle.yml ps

# View logs
docker-compose -f docker-compose.oracle.yml logs -f adrion-api

# Wait for services to be healthy (~2 minutes)
docker-compose -f docker-compose.oracle.yml ps
# All should show "healthy" status
```

---

## Step 9: Verify Deployment

### Health Checks

```bash
# From local machine
# Test Flask API
curl http://<app-vm-public-ip>:8003/api/arbitrage/status

# Test UAP Orchestrator
curl http://<app-vm-public-ip>:8002/mapi/v1/health

# Test Prometheus (from your IP only — open SSH tunnel)
ssh -i your-key.key -L 9090:localhost:9090 ubuntu@<app-vm-public-ip>
# Then open: http://localhost:9090

# Test Grafana
ssh -i your-key.key -L 3000:localhost:3000 ubuntu@<app-vm-public-ip>
# Then open: http://localhost:3000 (admin/password)
```

---

## Step 10: Set Up Automated Backups

```bash
# On database VM, create backup script
cat > /home/ubuntu/backup-postgres.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
docker exec adrion-postgres pg_dump -U adrion_user adrion_production | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
# Keep only last 30 backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
EOF

chmod +x /home/ubuntu/backup-postgres.sh

# Add to crontab for daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/backup-postgres.sh") | crontab -
```

---

## Monthly Cost Projection

| Component | Cost |
|-----------|------|
| VM #1 (App) | $0 (free tier) |
| VM #2 (DB) | $0 (free tier) |
| Storage (200GB) | $0 (free tier) |
| Bandwidth | $0 (free tier) |
| **Total** | **$0/mo** |

**Limits Before Charges:**
- CPU: 2 OCPU (2 cores)
- RAM: 2-4 GB
- Storage: 200 GB
- Network: 10 Mbps

---

## Maintenance & Monitoring

### Daily Tasks
- Monitor disk usage: `df -h`
- Check service health: `docker-compose ps`
- Review logs: `docker-compose logs --tail=100`

### Weekly Tasks
- Backup verification: `ls -lh /home/ubuntu/backups/`
- Performance review in Grafana
- Check for Docker updates: `docker version`

### Monthly Tasks
- Update base images: `docker pull postgres:15-alpine`
- Review Guardian Laws compliance
- Test disaster recovery (restore from backup)

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Restart service
docker-compose restart <service-name>

# Full reset (WARNING: data loss)
docker-compose down -v
docker-compose up -d
```

### Out of Memory

```bash
# Check memory usage
free -h
docker stats

# Solution: Use only 1 analyzer instead of 4
# Edit scripts/run-agent-session.py
```

### Database Connection Failed

```bash
# Test connectivity from app VM to DB VM
telnet <db-vm-private-ip> 5432

# Verify PostgreSQL is running on DB VM
docker exec adrion-postgres pg_isready -U adrion_user

# Check security group rules in Oracle Cloud Console
```

### Public IP Not Reachable

```bash
# Verify instance is running
# Check security group rules
# Verify firewall on VM:
sudo ufw status
sudo ufw allow 8003/tcp
```

---

## Next Steps

1. ✅ Create Oracle Cloud account
2. ✅ Create 2 VMs in free tier
3. ✅ Deploy PostgreSQL on DB VM
4. ✅ Deploy ADRION 369 on App VM
5. ✅ Verify health endpoints
6. ✅ Access Grafana dashboards
7. ✅ Monitor for 30 days to ensure no billing surprises

**Total Setup Time:** 45-60 minutes  
**Total Monthly Cost:** $0 (forever)

---

**Questions?** See `docs/CLOUD_DEPLOYMENT_RESEARCH.md` for detailed troubleshooting
