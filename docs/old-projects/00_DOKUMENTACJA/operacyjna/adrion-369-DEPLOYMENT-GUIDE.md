# 🚀 Deployment Quick-Start Guide - ADRION-369

**Dokument:** Interactive Deployment Guide  
**Data:** 14.05.2026  
**Projekt:** ADRION-369 Ecosystem  
**Status:** Production Ready

---

## 📍 Table of Contents

1. [Environment Selection](#-environment-selection)
2. [Prerequisites](#-prerequisites)
3. [Local Development](#-local-development)
4. [Staging Deployment](#-staging-deployment)
5. [Production Deployment](#-production-deployment)
6. [Health Checks & Validation](#-health-checks--validation)
7. [Rollback Procedures](#-rollback-procedures)
8. [Monitoring & Logging](#-monitoring--logging)

---

## 🌍 Environment Selection

### Quick Decision Tree

```
START
  ├─ Development? (local machine / single node)
  │  └─→ Use: docker-compose.local.yml
  │      Features: Fast iteration, no HA, debug mode
  │
  ├─ Staging? (pre-production testing)
  │  └─→ Use: docker-compose.cloud.yml + Kubernetes
  │      Features: HA setup, realistic production config
  │
  └─ Production? (business-critical)
     └─→ Use: docker-compose.prod.yml + Kubernetes
         Features: Full redundancy, auto-scaling, SLAs
```

---

## ✅ Prerequisites

### System Requirements

#### Local Development
```yaml
Minimum:
  CPU:     2 cores
  RAM:     8 GB
  Storage: 20 GB
  Docker:  20.10+
  Docker Compose: 2.0+

Recommended:
  CPU:     4+ cores
  RAM:     16 GB
  Storage: 50 GB SSD
```

#### Staging/Production
```yaml
Kubernetes:
  Cluster:   1.20+
  Nodes:     3+ (HA)
  CPU:       2 cores/node minimum
  RAM:       4 GB/node minimum
  
Storage:
  PersistentVolume: 100 GB+
  Database:         50 GB+ (PostgreSQL)
```

### Required Tools

#### All Environments
```bash
# Package Managers
brew install docker          # macOS
apt-get install docker.io   # Linux

# Docker & Compose
docker --version            # ≥ 20.10.0
docker-compose --version    # ≥ 2.0.0

# Essential CLI
git --version               # ≥ 2.30.0
```

#### Kubernetes Deployments
```bash
# Kubernetes CLI
kubectl version --client

# Helm (optional but recommended)
helm version

# kops / eksctl (for cluster management)
# CloudFormation / Terraform templates
```

### Environment Variables

```bash
# Copy template to active config
cp .env.example .env

# Required variables (all environments)
export ADRION_ENV=development          # dev/staging/prod
export DATABASE_URL=postgresql://...   # DB connection
export REDIS_URL=redis://...          # Cache connection
export LOG_LEVEL=INFO                 # DEBUG/INFO/WARN/ERROR

# Optional but recommended
export SENTRY_DSN=https://...         # Error tracking
export DATADOG_API_KEY=...            # Monitoring
export SLACK_WEBHOOK=https://...      # Alerts
```

---

## 💻 Local Development

### Quick Start (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/Gruszkoland/adrion-369.git
cd adrion-369

# 2. Initialize environment
cp .env.example .env
# Edit .env with your settings

# 3. Start local stack
docker-compose -f docker-compose.local.yml up -d

# 4. Verify deployment
./scripts/health-check.sh local

# 5. Access services
# Genesis:  http://localhost:8001
# Guardian: http://localhost:8002
# Healer:   http://localhost:8003
# Oracle:   http://localhost:8004
# Vortex:   http://localhost:8005
# Router:   http://localhost:8000
```

### Detailed Local Setup

#### Step 1: Build Services

```bash
# Build all services locally
docker-compose -f docker-compose.local.yml build

# Build specific service
docker-compose -f docker-compose.local.yml build genesis-mcp

# Build with cache bypass
docker-compose -f docker-compose.local.yml build --no-cache
```

#### Step 2: Start Infrastructure

```bash
# Start all services
docker-compose -f docker-compose.local.yml up -d

# Follow logs in real-time
docker-compose -f docker-compose.local.yml logs -f

# Monitor specific service
docker-compose -f docker-compose.local.yml logs -f genesis-mcp
```

#### Step 3: Initialize Database

```bash
# Run migrations
docker-compose -f docker-compose.local.yml exec db \
  psql -U adrion_user -d adrion_dev -f /init.sql

# Seed data (optional)
docker-compose -f docker-compose.local.yml exec db \
  python /scripts/seed_db.py
```

#### Step 4: Verify Services

```bash
# Check running containers
docker-compose -f docker-compose.local.yml ps

# Test Router endpoint
curl http://localhost:8000/health

# Test Genesis MCP
curl http://localhost:8001/genesis/health

# Complete health check
make health-check-local
```

### Local Development Workflow

```bash
# Monitor all services
docker-compose -f docker-compose.local.yml logs -f \
  genesis-mcp guardian-mcp healer-mcp oracle-mcp vortex-mcp

# Run tests
pytest tests/

# Check code quality
pylint mcp_servers/
mypy mcp_servers/

# Format code
black mcp_servers/

# Update dependencies
pip install --upgrade -r requirements-mcp.txt
```

### Local Debugging

```bash
# Enable debug mode in .env
export LOG_LEVEL=DEBUG
export DEBUG=1

# Restart with debug
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d

# Attach to service console
docker-compose -f docker-compose.local.yml exec genesis-mcp bash

# Check resource usage
docker stats

# View network issues
docker network inspect adrion-369_default
```

---

## 🏗️ Staging Deployment

### Architecture

```
┌─────────────────────────────────────────┐
│      Kubernetes Cluster (Staging)       │
├─────────────────────────────────────────┤
│  Namespace: adrion-staging              │
│  Replicas: 2 per service                │
│  Load Balancer: Service type LoadBalancer
└─────────────────────────────────────────┘
```

### Pre-deployment Checklist

- [ ] Kubernetes cluster created (3+ nodes)
- [ ] StorageClass configured
- [ ] Ingress controller installed
- [ ] Monitoring stack deployed
- [ ] TLS certificates obtained
- [ ] Container registry configured

### Deployment Commands

```bash
# 1. Create namespace
kubectl create namespace adrion-staging

# 2. Create secrets
kubectl create secret generic adrion-secrets \
  --from-env-file=.env.staging \
  -n adrion-staging

# 3. Apply Kubernetes manifests
kubectl apply -f kubernetes/staging/ -n adrion-staging

# 4. Wait for rollout
kubectl rollout status deployment/genesis-mcp \
  -n adrion-staging --timeout=5m

# 5. Verify all pods running
kubectl get pods -n adrion-staging

# 6. Check service IPs
kubectl get svc -n adrion-staging
```

### Staging Configuration

```yaml
# kubernetes/staging/values.yaml
environment: staging
replicas:
  genesis: 2
  guardian: 2
  healer: 2
  oracle: 1
  vortex: 2
  router: 2

resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi

persistence:
  enabled: true
  size: 20Gi
  storageClass: standard

ingress:
  enabled: true
  host: staging-adrion.example.com
  tls: true
```

### Health Checks (Staging)

```bash
# Check service endpoints
kubectl get endpoints -n adrion-staging

# Port forward for testing
kubectl port-forward -n adrion-staging \
  service/router 8000:8000

# Test endpoints (in another terminal)
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/genesis

# Check logs
kubectl logs -f deployment/genesis-mcp -n adrion-staging

# Monitor resource usage
kubectl top nodes -n adrion-staging
kubectl top pods -n adrion-staging
```

### Staging Validation

```bash
# Run integration tests
pytest tests/integration/ \
  --env=staging \
  --endpoint=http://staging-adrion.example.com

# Performance testing
locust -f tests/load/locustfile.py \
  --host=http://staging-adrion.example.com \
  --users=100 \
  --spawn-rate=10

# Security scanning
trivy image adrion-369/genesis-mcp:latest
```

---

## 🏢 Production Deployment

### Pre-Deployment Checklist

- [ ] Production Kubernetes cluster (3+ nodes minimum)
- [ ] Persistent storage configured & tested
- [ ] Database backups configured
- [ ] Load balancer configured
- [ ] SSL/TLS certificates installed
- [ ] Monitoring & logging configured
- [ ] Incident response team notified
- [ ] Rollback plan documented
- [ ] Backup & recovery tested

### Deployment Steps

```bash
# 1. Create production namespace
kubectl create namespace adrion-prod

# 2. Setup RBAC
kubectl apply -f kubernetes/rbac/prod-rbac.yaml \
  -n adrion-prod

# 3. Create secrets from vault
export VAULT_ADDR=https://vault.example.com
vault kv get -format=json secret/adrion/prod | \
  jq -r '.data.data | to_entries[] | "\(.key)=\(.value)"' > prod.env
kubectl create secret generic adrion-secrets \
  --from-env-file=prod.env \
  -n adrion-prod

# 4. Deploy services
kubectl apply -f kubernetes/prod/ -n adrion-prod

# 5. Wait for rollout
for service in genesis guardian healer oracle vortex router; do
  kubectl rollout status deployment/$service-mcp \
    -n adrion-prod --timeout=10m
done

# 6. Run smoke tests
./scripts/smoke-tests.sh prod

# 7. Enable traffic
kubectl patch service router -n adrion-prod \
  -p '{"spec":{"selector":{"version":"v1"}}}'
```

### Production Configuration

```yaml
# kubernetes/prod/values.yaml
environment: production
replicas:
  genesis: 3
  guardian: 3
  healer: 2
  oracle: 2
  vortex: 5
  router: 3

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2
    memory: 2Gi

persistence:
  enabled: true
  size: 100Gi
  storageClass: premium-ssd

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPU: 70%
  targetMemory: 80%

ingress:
  enabled: true
  host: api.adrion.example.com
  tls: true
  certManager: true

monitoring:
  enabled: true
  prometheus: true
  grafana: true
  alerting: true
```

### Production Health Checks

```bash
# Comprehensive health check
./scripts/health-check.sh prod --verbose

# Check all services
kubectl get deployments -n adrion-prod

# Check pods status
kubectl get pods -n adrion-prod -o wide

# Check resource usage
kubectl top nodes
kubectl top pods -n adrion-prod

# Check events
kubectl get events -n adrion-prod --sort-by='.lastTimestamp'

# Monitor metrics
kubectl exec -it -n adrion-prod <pod-name> -- \
  curl http://localhost:8000/metrics | grep -i latency
```

---

## 🩺 Health Checks & Validation

### Quick Health Check Script

```bash
#!/bin/bash
# scripts/health-check.sh

ENV=${1:-local}

echo "=== ADRION-369 Health Check ($ENV) ==="
echo ""

# Check Router
echo "🔀 Router Health..."
curl -s http://localhost:8000/health | jq .

# Check Genesis
echo "🌅 Genesis Health..."
curl -s http://localhost:8001/genesis/health | jq .

# Check Guardian
echo "🛡️  Guardian Health..."
curl -s http://localhost:8002/guardian/health | jq .

# Check Healer
echo "💊 Healer Health..."
curl -s http://localhost:8003/healer/health | jq .

# Check Oracle
echo "🔮 Oracle Health..."
curl -s http://localhost:8004/oracle/health | jq .

# Check Vortex
echo "⚡ Vortex Health..."
curl -s http://localhost:8005/vortex/health | jq .

# Check dependencies
echo ""
echo "=== Dependencies ==="
echo "PostgreSQL: $(pg_isready -h localhost -U adrion_user)"
echo "Redis: $(redis-cli ping)"
echo "RabbitMQ: $(rabbitmqctl status | grep running)"

echo ""
echo "=== All systems go! ✅ ==="
```

### Validation Tests

```bash
# Endpoint test
curl -X POST http://localhost:8000/api/v1/genesis \
  -H "Content-Type: application/json" \
  -d '{"action": "init"}'

# Performance baseline
ab -n 1000 -c 10 http://localhost:8000/health

# Dependency verification
docker-compose -f docker-compose.local.yml exec db \
  psql -U adrion_user -d adrion_dev -c "SELECT version();"

# Service connectivity
docker network inspect adrion-369_default | jq '.[0].Containers'
```

---

## ⏮️ Rollback Procedures

### Automatic Rollback

```bash
# Kubernetes automatic rollback (if health checks fail)
kubectl rollout undo deployment/genesis-mcp -n adrion-prod

# Verify previous version is running
kubectl rollout history deployment/genesis-mcp -n adrion-prod
kubectl rollout status deployment/genesis-mcp -n adrion-prod
```

### Manual Rollback

```bash
# 1. Check deployment history
kubectl rollout history deployment/genesis-mcp -n adrion-prod

# 2. Rollback to previous version
kubectl rollout undo deployment/genesis-mcp -n adrion-prod

# 3. Or rollback to specific revision
kubectl rollout undo deployment/genesis-mcp -n adrion-prod --to-revision=5

# 4. Verify rollback
kubectl rollout status deployment/genesis-mcp -n adrion-prod

# 5. Check pods
kubectl get pods -n adrion-prod -l app=genesis-mcp
```

### Docker Compose Rollback

```bash
# 1. Stop current deployment
docker-compose -f docker-compose.prod.yml down

# 2. Switch to previous image tag
sed -i 's/image: adrion\/genesis:v2/image: adrion\/genesis:v1/g' \
  docker-compose.prod.yml

# 3. Restart with previous version
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify
docker-compose -f docker-compose.prod.yml ps
```

### Database Rollback

```bash
# 1. List available backups
aws s3 ls s3://adrion-backups/postgres/

# 2. Restore from backup
pg_restore -d adrion_prod \
  s3://adrion-backups/postgres/backup-20260514-100000.sql

# 3. Verify data integrity
psql -d adrion_prod -c "SELECT COUNT(*) FROM public.entities;"
```

---

## 📊 Monitoring & Logging

### Monitoring Stack

```yaml
# docker-compose local additions
services:
  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    
  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Access Monitoring

```bash
# Local
Prometheus:  http://localhost:9090
Grafana:     http://localhost:3000 (admin/admin)

# Kubernetes
kubectl port-forward -n adrion-prod \
  svc/prometheus 9090:9090 &
kubectl port-forward -n adrion-prod \
  svc/grafana 3000:3000 &

# Production
https://monitoring.adrion.example.com
```

### Key Metrics to Monitor

```
Router:
  - request_latency_p95
  - error_rate
  - active_connections

Genesis:
  - initialization_time
  - state_size
  - cache_hit_ratio

Guardian:
  - validation_latency
  - policy_violations
  - audit_log_size

Healer:
  - anomaly_detection_accuracy
  - recovery_time
  - proposal_generation_rate

Oracle:
  - prediction_latency
  - model_accuracy
  - feature_engineering_time

Vortex:
  - processing_throughput
  - queue_depth
  - stream_lag
```

### Logging Configuration

```bash
# View logs (local)
docker-compose -f docker-compose.local.yml logs -f

# View logs (Kubernetes)
kubectl logs -f deployment/genesis-mcp -n adrion-prod

# Stream logs to file
kubectl logs -f deployment/genesis-mcp -n adrion-prod \
  > genesis.log &

# Centralized logging (ELK stack)
curl -X GET "elasticsearch:9200/_search?q=service:genesis"
```

---

## 🎯 Post-Deployment Checklist

- [ ] All services reporting healthy status
- [ ] Database migrations completed successfully
- [ ] Initial data load verified
- [ ] SSL/TLS certificates valid
- [ ] Monitoring and alerting active
- [ ] Log aggregation confirmed
- [ ] Backup and recovery tested
- [ ] DNS records updated
- [ ] Team notifications sent
- [ ] Documentation updated

---

## 📞 Support & Escalation

**Deployment Issues?**
- Check logs: `docker-compose logs -f`
- Health check: `./scripts/health-check.sh`
- Review: [Troubleshooting Guide](adrion-369-TROUBLESHOOTING.md)

**On-call?**
- Page: #adrion-oncall (Slack)
- PagerDuty: [link]
- Runbooks: `/docs/runbooks/`

---

*Dokument zaktualizowany: 14.05.2026*
