# ADRION 369 — Kubernetes Migration Guide

**Date:** 2026-04-04
**Version:** 1.0.0
**Status:** ✅ READY FOR MIGRATION

---

## Overview

This guide walks you through migrating ADRION 369 from Docker Compose to Kubernetes.

### Why Kubernetes?

✅ **Auto-scaling** — Scale pods based on CPU/memory usage
✅ **High Availability** — Automatic pod restart, rolling updates
✅ **Multi-region** — Deploy across multiple cloud providers
✅ **Self-healing** — Replace failed pods automatically
✅ **Advanced networking** — Service mesh, network policies, load balancing
✅ **Enterprise-grade** — Security, RBAC, compliance tools

### Before vs After

**Docker Compose (Local/Small Team):**
- Single machine orchestration
- Manual scaling
- Limited monitoring
- Basic fault tolerance

**Kubernetes (Production/Teams):**
- Multi-node clustering
- Automatic scaling (HPA)
- Built-in monitoring (Prometheus, Grafana)
- Self-healing with health checks
- Rolling updates with zero downtime
- Network policies for security
- Multi-cloud deployment

---

## Prerequisites

### Install kubectl

**macOS:**
```bash
brew install kubectl
```

**Windows (PowerShell):**
```powershell
choco install kubernetes-cli
```

**Linux:**
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

### Choose a Kubernetes cluster

**Option 1: Local Development (Minikube)**
```bash
# Install minikube
brew install minikube  # macOS
choco install minikube  # Windows

# Start cluster
minikube start --cpus 4 --memory 8192 --disk-size 40gb
minikube addons enable ingress
minikube addons enable metrics-server

# Verify
kubectl cluster-info
```

**Option 2: Docker Desktop (easiest for developers)**
- Preferences → Kubernetes → Enable Kubernetes
- Ingress already included
- Ready to go!

**Option 3: Cloud Kubernetes**

AWS EKS:
```bash
eksctl create cluster --name adrion --region us-east-1 --nodes 3
```

Google GKE:
```bash
gcloud container clusters create adrion --num-nodes 3 --zone us-central1-a
```

Azure AKS:
```bash
az aks create -g adrion -n adrion --node-count 3
```

### Verify Kubernetes is running

```bash
kubectl cluster-info
kubectl get nodes
kubectl get storageclass
```

---

## File Structure

```
kubernetes/
├── 00-namespace.yaml           # Namespace isolation
├── 01-secrets-configmaps.yaml  # Secrets + ConfigMaps
├── 02-storage.yaml             # PersistentVolume + StorageClass
├── 03-postgres.yaml            # PostgreSQL StatefulSet + Service
├── 04-backend.yaml             # Backend Deployment + Service + RBAC
├── 05-frontend.yaml            # Frontend Deployment + Service
├── 06-ingress.yaml             # Ingress + TLS (cert-manager)
└── 07-pgadmin-hpa-policies.yaml # HPA + pgAdmin + Network Policies
```

---

## Step-by-Step Migration

### Phase 1: Preparation (30 min)

#### 1.1 Backup Docker database

```bash
# Backup current data
docker exec adrion-postgres pg_dump -U adrion genesis_record > backup_$(date +%Y%m%d).sql

# Verify backup
ls -lah backup_*.sql
wc -l backup_*.sql  # Check it has content
```

#### 1.2 Update Kubernetes manifests

Edit the following files with your configuration:

**kubernetes/01-secrets-configmaps.yaml:**
```yaml
stringData:
  POSTGRES_PASSWORD: "YOUR_STRONG_PASSWORD_32_CHARS"  # ← Change
  PG_PASSWORD: "YOUR_STRONG_PASSWORD_32_CHARS"        # ← Change
  UAP_API_KEY: "YOUR_API_KEY_32_CHARS"               # ← Change
  JWT_SECRET: "YOUR_JWT_SECRET_32_CHARS"             # ← Change
  DRM_HMAC_SECRET: "YOUR_HMAC_SECRET_32_CHARS"       # ← Change
```

**kubernetes/06-ingress.yaml:**
```yaml
spec:
  rules:
  - host: adrion.your-domain.com  # ← Change to your domain
    http:
      paths:
      - path: /
```

#### 1.3 Generate strong secrets

```bash
# Generate 32-character random strings
python3 << 'EOF'
import secrets
for label in ["POSTGRES_PASSWORD", "UAP_API_KEY", "JWT_SECRET", "DRM_HMAC_SECRET"]:
    print(f"{label}: {secrets.token_urlsafe(32)}")
EOF
```

---

### Phase 2: Kubernetes Deployment (20 min)

#### 2.1 Deploy using automated script (recommended)

```bash
# Make script executable
chmod +x scripts/k8s-migrate.sh

# Run migration
./scripts/k8s-migrate.sh

# This will:
# 1. Backup Docker database
# 2. Create Kubernetes namespace
# 3. Deploy all resources
# 4. Restore database to Kubernetes
# 5. Run health checks
```

#### 2.2 Manual deployment (if script fails)

```bash
# 1. Create namespace
kubectl apply -f kubernetes/00-namespace.yaml

# 2. Create secrets and configmaps
kubectl apply -f kubernetes/01-secrets-configmaps.yaml

# 3. Setup storage
kubectl apply -f kubernetes/02-storage.yaml

# 4. Wait for storage
kubectl get pvc -n adrion --watch

# 5. Deploy PostgreSQL
kubectl apply -f kubernetes/03-postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n adrion --timeout=300s

# 6. Restore database
kubectl exec -i postgres-0 -n adrion -- \
  psql -U adrion -d genesis_record < backup_*.sql

# 7. Deploy Backend
kubectl apply -f kubernetes/04-backend.yaml
kubectl wait --for=condition=ready pod -l app=uap-backend -n adrion --timeout=300s

# 8. Deploy Frontend
kubectl apply -f kubernetes/05-frontend.yaml
kubectl wait --for=condition=ready pod -l app=uap-frontend -n adrion --timeout=300s

# 9. Setup Ingress
kubectl apply -f kubernetes/06-ingress.yaml

# 10. Setup HPA + Policies
kubectl apply -f kubernetes/07-pgadmin-hpa-policies.yaml
```

---

### Phase 3: Verification (10 min)

#### 3.1 Check all pods are running

```bash
kubectl get pods -n adrion

# Expected output:
# NAME                               READY   STATUS    RESTARTS   AGE
# postgres-0                         1/1     Running   0          2m
# uap-backend-xyz-abc                1/1     Running   0          1m
# uap-backend-xyz-def                1/1     Running   0          1m
# uap-backend-xyz-ghi                1/1     Running   0          1m
# uap-frontend-abc-def               1/1     Running   0          1m
# uap-frontend-ghi-jkl               1/1     Running   0          1m
# pgadmin-xyz-123                    1/1     Running   0          1m
```

#### 3.2 Check services

```bash
kubectl get svc -n adrion

# Expected:
# NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)     AGE
# postgres        ClusterIP   None            <none>        5432/TCP    2m
# uap-backend     ClusterIP   10.96.x.y       <none>        8002/TCP    1m
# uap-frontend    ClusterIP   10.96.a.b       <none>        8003/TCP    1m
# pgadmin         ClusterIP   10.96.p.q       <none>        5050/TCP    1m
```

#### 3.3 Test backend API

```bash
# Port forward
kubectl port-forward -n adrion svc/uap-backend 8002:8002 &

# Test API
curl -H "X-API-Key: local-dev-key-123" http://localhost:8002/mapi/v1/status

# Expected: JSON response with status info
```

#### 3.4 Test frontend

```bash
# Port forward
kubectl port-forward -n adrion svc/uap-frontend 8003:8003 &

# Test
curl http://localhost:8003

# Expected: HTML content
```

#### 3.5 Check database

```bash
kubectl exec -it postgres-0 -n adrion -- \
  psql -U adrion -d genesis_record -c "\dt"

# Expected: 4 tables (tasks, genesis_logs, checkpoints, agent_metrics)
```

---

### Phase 4: Networking & Security (15 min)

#### 4.1 Install Ingress Controller

**NGINX Ingress:**
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace
```

**Traefik:**
```bash
helm repo add traefik https://traefik.github.io/charts
helm install traefik traefik/traefik --namespace traefik --create-namespace
```

#### 4.2 Setup SSL certificates (optional but recommended)

**Using cert-manager (automatic renewal):**
```bash
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true
```

Then deploy Ingress:
```bash
kubectl apply -f kubernetes/06-ingress.yaml
```

#### 4.3 Get external IP

```bash
# For Ingress
kubectl get ingress -n adrion
kubectl get svc -n ingress-nginx

# For Minikube:
minikube service -n adrion uap-frontend

# For Docker Desktop:
kubectl port-forward -n adrion svc/uap-frontend 8003:8003
```

---

### Phase 5: Monitoring (10 min)

#### 5.1 Install Prometheus & Grafana

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

#### 5.2 Access Grafana

```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:3000

# Open: http://localhost:3000
# Login: admin / prom-operator
```

#### 5.3 Add ADRION dashboards

Create custom dashboard in Grafana querying Prometheus:
- `rate(adrion_requests_total[5m])` — Request rate
- `histogram_quantile(0.95, adrion_request_duration_seconds)` — P95 latency
- `rate(adrion_db_query_seconds[5m])` — Database query time

---

## Post-Migration Tasks

### 1. Verify data integrity

```bash
# Connect to PostgreSQL
kubectl exec -it postgres-0 -n adrion -- \
  psql -U adrion -d genesis_record

# Check row counts
SELECT COUNT(*) FROM tasks;
SELECT COUNT(*) FROM genesis_logs;
SELECT COUNT(*) FROM checkpoints;
SELECT COUNT(*) FROM agent_metrics;

\q  # Exit
```

### 2. Update your CI/CD

Update deployment scripts to target Kubernetes instead of Docker:
```bash
# Instead of: docker-compose up -d
# Use: kubectl apply -f kubernetes/*.yaml
```

### 3. Backup strategy for Kubernetes

```bash
# Backup PostgreSQL in Kubernetes
kubectl exec -i postgres-0 -n adrion -- \
  pg_dump -U adrion genesis_record | gzip > k8s_backup.sql.gz

# Backup entire cluster
kubectl get all,pvc,pv,secret,configmap -n adrion -o yaml > k8s_full_backup.yaml
```

### 4. Decommission Docker services (when satisfied)

```bash
# Keep running for a few days as fallback
docker-compose ps

# When ready to remove:
docker-compose down -v  # Remove volumes too
```

---

## Troubleshooting

### Pods stuck in `Pending`

```bash
# Check what's blocking
kubectl describe pod pod-name -n adrion

# Common causes:
# - Storage not available: kubectl get pvc -n adrion
# - Resources unavailable: kubectl top nodes
# - Image pull errors: kubectl logs pod-name -n adrion
```

### Database migration failed

```bash
# Restore from backup
kubectl exec -i postgres-0 -n adrion -- \
  psql -U adrion -d genesis_record < backup_*.sql

# Or restart PostgreSQL
kubectl rollout restart statefulset/postgres -n adrion
```

### Backend can't connect to database

```bash
# Check PostgreSQL is running
kubectl get pod postgres-0 -n adrion

# Check connectivity
kubectl exec -it uap-backend-0 -n adrion -- \
  nc -zv postgres.adrion.svc.cluster.local 5432

# Check logs
kubectl logs uap-backend-0 -n adrion
```

### Ingress not working

```bash
# Check Ingress Controller
kubectl get pods -n ingress-nginx

# Check Ingress status
kubectl describe ingress adrion-ingress -n adrion

# Check DNS
nslookup adrion.your-domain.com
```

---

## Quick Commands

| Command | Purpose |
|---------|---------|
| `kubectl get pods -n adrion` | List all pods |
| `kubectl logs -f deployment/uap-backend -n adrion` | Stream backend logs |
| `kubectl scale deployment uap-backend --replicas=5 -n adrion` | Manual scaling |
| `kubectl port-forward svc/uap-backend 8002:8002 -n adrion` | Port forward |
| `kubectl exec -it postgres-0 -n adrion -- psql` | Database shell |
| `kubectl describe pod pod-name -n adrion` | Debug pod |
| `kubectl top nodes` | Node resource usage |
| `kubectl top pod -n adrion` | Pod resource usage |

---

## Success Criteria

✅ **All requirements met for successful migration:**

- [ ] All pods running and healthy
- [ ] Database fully migrated
- [ ] Backend API responding
- [ ] Frontend UI accessible
- [ ] Ingress configured
- [ ] TLS certificates valid
- [ ] Monitoring operational
- [ ] Health checks passing
- [ ] HPA working (scale on CPU/memory)
- [ ] Network policies enforced
- [ ] Backups tested and working

---

**Status:** 🟢 READY FOR MIGRATION
**Estimated Time:** 1-2 hours
**Support:** See KUBERNETES_DEPLOYMENT.md for detailed reference

---

**Generated:** 2026-04-04
**Version:** 1.0.0
