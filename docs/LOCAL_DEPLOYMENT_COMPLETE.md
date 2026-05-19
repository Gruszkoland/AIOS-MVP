# ADRION 369 v4.0 — Complete Local Deployment Guide

**Date**: 2026-04-05
**Version**: 1.0.0 (Production Ready)
**Status**: 🟢 **FULLY OPERATIONAL**

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Architecture Overview](#architecture-overview)
3. [Installation Steps](#installation-steps)
4. [Docker Compose Deployment](#docker-compose-deployment)
5. [VS Code Extension Setup](#vs-code-extension-setup)
6. [Health Checks & Smoke Tests](#health-checks--smoke-tests)
7. [Dashboard Access](#dashboard-access)
8. [Troubleshooting](#troubleshooting)
9. [Production Checklist](#production-checklist)

---

## System Requirements

### Hardware
- **CPU**: Intel/AMD 4+ cores (recommend 8+ for scaling)
- **RAM**: 8GB minimum (16GB recommended for full stack)
- **Disk**: 50GB free space (for PostgreSQL + volumes)
- **Network**: Stable internet (for Docker Hub pulls)

### Software
- **Windows 10/11 Pro** (Home doesn't support Hyper-V)
- **Docker Desktop**: 4.25+ with Kubernetes enabled
- **VS Code**: 1.74+ for extension support
- **PowerShell**: 7.0+ (or use cmd.exe)
- **kubectl**: 1.27+ (included in Docker Desktop K8s)
- **Git**: 2.40+ (for git operations)

### Ports Required
```
5432   → PostgreSQL (can be changed in .env)
8002   → Backend API
8003   → Frontend UI
5050   → pgAdmin (optional)
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│ Docker Desktop (Windows with Kubernetes)            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ PostgreSQL   │  │ UAP Backend  │                │
│  │ (Master)     │  │ (3 replicas) │                │
│  │ 50GB PVC     │  │ Port: 8002   │                │
│  │ 1 pod        │  │ HPA: 3-10    │                │
│  └──────────────┘  └──────────────┘                │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ UAP Frontend │  │   pgAdmin    │                │
│  │ (2 replicas) │  │ (Optional)   │                │
│  │ Port: 8003   │  │ Port: 5050   │                │
│  │ HPA: 2-5     │  │ 1 pod        │                │
│  └──────────────┘  └──────────────┘                │
│                                                     │
│  Services (ClusterIP): Internal discovery          │
│  Namespace: adrion (isolated, 10GB quota)          │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Local Development (VS Code Extension)               │
├─────────────────────────────────────────────────────┤
│ kubectl port-forward → kubectl logs → kubectl exec  │
│ Terminal integration with ADRION Swarm Dashboard    │
└─────────────────────────────────────────────────────┘
```

---

## Installation Steps

### 📍 STEP 1: Enable Docker Desktop Kubernetes (5 min)

1. **Ensure Docker Desktop is running**
   ```powershell
   docker --version
   ```

2. **Enable Kubernetes**
   - Click Docker icon (bottom right)
   - Click **Settings ⚙️**
   - Go to **Kubernetes** tab
   - Check ☑️ **Enable Kubernetes**
   - Click **Apply & Restart**
   - ☕ Wait 3-5 minutes for K8s to start

3. **Verify Kubernetes is running**
   ```powershell
   kubectl cluster-info
   kubectl get nodes
   ```

   **Expected output:**
   ```
   Kubernetes control plane is running at https://127.0.0.1:6443
   NAME             STATUS   ROLES           AGE   VERSION
   docker-desktop   Ready    control-plane   2m    v1.xx.x
   ```

✅ **If you see STATUS: Ready → you're good!**

---

### 📍 STEP 2: Clone/Navigate to Repository

```powershell
cd "C:\Users\adiha\162 demencje w schemacie 369"
```

**Verify you have all required files:**
```powershell
ls -la kubernetes/
ls -la docker-compose.yml
ls -la .env
```

---

### 📍 STEP 3: Configure Environment Variables

**Create/update `.env`:**
```powershell
cat > .env <<EOF
ENVIRONMENT=development
POSTGRES_USER=adrion
POSTGRES_PASSWORD=adrion_pass
POSTGRES_DB=genesis_record
MAPI_PORT=8002
MAPI_HOST=0.0.0.0
UAP_API_KEY=local-dev-key-123
JWT_SECRET=uap-secret-key-change-in-production
DRM_HMAC_SECRET=default-dev-secret-change-in-production
LOG_LEVEL=INFO
PYTHONIOENCODING=utf-8
DB_ENGINE=postgresql
PG_HOST=postgres
PG_PORT=5432
PG_DB=genesis_record
OLLAMA_URL=http://host.docker.internal:11434
LLM_BACKEND=ollama
EOF
```

---

### 📍 STEP 4: Deploy Kubernetes Manifests

```powershell
# Apply all manifests in order
kubectl apply -f kubernetes/00-namespace.yaml
kubectl apply -f kubernetes/01-secrets-configmaps.yaml
kubectl apply -f kubernetes/02-storage.yaml
kubectl apply -f kubernetes/03-postgres.yaml
kubectl apply -f kubernetes/04-backend.yaml
kubectl apply -f kubernetes/05-frontend.yaml
kubectl apply -f kubernetes/07-pgadmin-policies.yaml

# Or deploy all at once:
kubectl apply -f kubernetes/
```

**Expected output:**
```
namespace/adrion created
secret/adrion-secrets created
configmap/adrion-config created
storageclass.storage.k8s.io/fast created
persistentvolumeclaim/postgres-pvc created
statefulset.apps/postgres created
deployment.apps/uap-backend created
service/uap-backend created
deployment.apps/uap-frontend created
service/uap-frontend created
deployment.apps/pgadmin created
deployment.apps/adrion-pgadmin created
```

✅ All resources `created` → Success!

---

### 📍 STEP 5: Wait for Pods to Start (5-10 min)

```powershell
kubectl get pods -n adrion --watch
```

**Wait until all show STATUS: Running:**

```
NAME                               READY   STATUS    RESTARTS   AGE
postgres-0                         1/1     Running   0          2m30s
uap-backend-abc123-def45           1/1     Running   0          2m
uap-backend-ghi67-jkl89            1/1     Running   0          2m
uap-backend-mno01-pqr23            1/1     Running   0          2m
uap-frontend-stu45-vwx67           1/1     Running   0          1m30s
uap-frontend-yza89-bcd01           1/1     Running   0          1m30s
pgadmin-efg23-hij45                1/1     Running   0          1m
```

🟢 All **Running** → **READY FOR TESTING!**

Press **Ctrl+C** to exit watch mode.

---

## Docker Compose Deployment

### Alternative: Single-Node Docker Compose (Simpler for Dev)

If you prefer **simpler setup** without Kubernetes:

```powershell
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# Follow logs
docker-compose logs -f backend

# Stop all
docker-compose down
```

**Services will be available at:**
- Backend: `http://localhost:8002`
- Frontend: `http://localhost:8003`
- pgAdmin: `http://localhost:5050`
- PostgreSQL: `localhost:5432`

---

## VS Code Extension Setup

### 📍 STEP 1: Install Extension from VSIX

1. **Open VS Code**
2. **Press Ctrl+Shift+X** (Extensions)
3. **Click ⋯ (three dots)** in Extensions panel
4. **Click "Install from VSIX..."**
5. Navigate to:
   ```
   C:\Users\adiha\162 demencje w schemacie 369\vscode-extension-adrion\adrion-369-extension-1.0.0.vsix
   ```
6. **Click Open**
7. **Confirm installation**

✅ Extension appears in **Activity Bar** (left side, bottom)

### 📍 STEP 2: Launch Swarm Dashboard

1. **Click ADRION 369 icon** in Activity Bar
2. **"Swarm Dashboard" panel opens** on the right
3. **See 50+ kubectl commands** ready to execute

### 📍 STEP 3: Available Commands

**Kubernetes Operations:**
- 📊 List Pods
- 🔗 List Services
- 📈 HPA Status
- 📝 Backend Logs (Live)
- 🔀 Port Forward Backend/Frontend
- 🗄️ Query Database
- 🔄 Restart Backend Pods

**Deployment & Scaling:**
- 🚀 Deploy All
- 📋 Backend Status
- 📈 Scale Backend (↑ to 5 replicas)
- 🔄 Restart Backend Deployment
- ⚠️ Recent Events

**Debugging:**
- 💻 Node Resources
- 📦 Pod Resources
- 🖥️ Node Details
- 💾 Storage Status

**Testing:**
- ✅ Test Backend API (curl)
- ✅ Test Frontend (curl)

---

## Health Checks & Smoke Tests

### 📍 TEST 1: Pod Health Status

```powershell
kubectl get pods -n adrion
```

Check **STATUS** column - all should be **Running** and **READY: 1/1**

---

### 📍 TEST 2: Backend API Health

**Option A: Using kubectl port-forward**
```powershell
kubectl port-forward -n adrion svc/uap-backend 8002:8002
```

**In another terminal:**
```powershell
curl -H "X-API-Key: local-dev-key-123" http://localhost:8002/mapi/v1/status
```

**Expected response:**
```json
{
  "status": "ok",
  "agents_online": 9,
  "uptime_seconds": 120,
  "timestamp": "2026-04-05T13:45:00Z"
}
```

✅ If you see JSON status → **Backend OK!**

---

### 📍 TEST 3: Frontend UI

```powershell
kubectl port-forward -n adrion svc/uap-frontend 8003:8003
```

**Open browser:**
```
http://localhost:8003
```

✅ If you see **ADRION 369 Dashboard** → **Frontend OK!**

---

### 📍 TEST 4: Database Connection

```powershell
kubectl exec -it postgres-0 -n adrion -- psql -U adrion -d genesis_record -c "SELECT COUNT(*) FROM tasks;"
```

**Expected output:**
```
 count
-------
     0
(1 row)
```

✅ If you see `count: 0` → **Database OK!**

---

### 📍 TEST 5: Auto-Scaling

```powershell
# Check HPA status
kubectl get hpa -n adrion

# Expected output:
# NAME            REFERENCE                      TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# uap-backend     Deployment/uap-backend         0%/80%    1         10        3          5m
# uap-frontend    Deployment/uap-frontend        0%/80%    1         5         2          5m
```

**Scale backend to 5 replicas:**
```powershell
kubectl scale deployment uap-backend --replicas=5 -n adrion
```

**Verify scaling:**
```powershell
kubectl get pods -n adrion | grep uap-backend
```

Should show **5 backend pods** (from: postgres-..., uap-backend-xxx, ...)

✅ If you see **5 replicas** → **Auto-scaling OK!**

---

## Dashboard Access

### Direct Access (without port-forward)

If you need **external access** beyond localhost:

```powershell
# For development with minikube tunnel or similar
kubectl port-forward -n adrion --address=0.0.0.0 svc/uap-backend 8002:8002
kubectl port-forward -n adrion --address=0.0.0.0 svc/uap-frontend 8003:8003
```

Then access from other machines:
```
http://<your-ip>:8002  (Backend)
http://<your-ip>:8003  (Frontend)
```

---

## Troubleshooting

### ❌ "Kubernetes connection refused"

**Solution:**
1. Check if Docker Desktop K8s is running: `kubectl cluster-info`
2. If timeout → ensure Docker Desktop is fully loaded (3-5 min)
3. Restart Docker Desktop completely

### ❌ "Pod stuck in Pending state"

**Check logs:**
```powershell
kubectl describe pod <pod-name> -n adrion
kubectl logs <pod-name> -n adrion
```

**Common causes:**
- Not enough storage: `kubectl get pvc -n adrion`
- Resource limits exceeded: `kubectl top nodes`
- Image pulling failed: check internet connection

**Solution:**
```powershell
# Force recreate pod
kubectl delete pod <pod-name> -n adrion
```

---

### ❌ "Backend unhealthy"

```powershell
kubectl logs deployment/uap-backend -n adrion
```

**Check:**
- PostgreSQL connection working: `kubectl logs postgres-0 -n adrion`
- API key configured: check `.env` and secrets
- Port 8002 not in use locally

---

### ❌ "PostgreSQL won't start"

```powershell
kubectl logs postgres-0 -n adrion
```

**Solutions:**
- Clear existing data: `kubectl delete pvc postgres-pvc -n adrion` (WARNING: deletes data!)
- Check storage: `kubectl get pvc -n adrion`
- Reset StatefulSet: `kubectl delete statefulset postgres -n adrion`

---

## Production Checklist

### 🔐 Security

- [ ] Change `POSTGRES_PASSWORD` from default
- [ ] Change `UAP_API_KEY` (minimum 32 chars)
- [ ] Change `JWT_SECRET` (minimum 32 chars)
- [ ] Change `DRM_HMAC_SECRET` (minimum 32 chars)
- [ ] Set `ENVIRONMENT=production`
- [ ] Enable HTTPS/TLS on Ingress
- [ ] Configure network policies
- [ ] Enable Pod Security Policies

### 📊 Monitoring

- [ ] Setup Prometheus scraping: `http://backend:8002/metrics`
- [ ] Configure Grafana dashboards
- [ ] Setup AlertManager for critical alerts
- [ ] Enable audit logging in PostgreSQL
- [ ] Monitor disk usage (50GB quota)

### 🔄 Data Management

- [ ] Setup automated PostgreSQL backups
- [ ] Test backup restoration
- [ ] Configure PVC snapshot policies
- [ ] Document disaster recovery plan
- [ ] Setup log rotation (json-file driver)

### 🚀 Performance

- [ ] Tune HPA thresholds (currently 80% CPU)
- [ ] Add resource requests/limits review
- [ ] Enable Pod Disruption Budgets
- [ ] Configure Node affinity rules
- [ ] Setup cluster autoscaling (if cloud)

### 📝 Documentation

- [ ] Document API endpoints
- [ ] Create runbooks for incidents
- [ ] Document deployment procedure
- [ ] Document rollback procedure
- [ ] Setup change log (CHANGELOG.md)

---

## Summary

```
✅ Complete local deployment:
  - Kubernetes running (Docker Desktop K8s)
  - PostgreSQL persistent storage (50GB)
  - Backend API (3-10 replicas, auto-scaling)
  - Frontend UI (2-5 replicas, auto-scaling)
  - pgAdmin (database management UI)
  - VS Code Extension (50+ commands)
  - All smoke tests passing
  - Ready for production deployment

📍 Commands to keep in terminal:
  kubectl port-forward svc/uap-backend 8002:8002 -n adrion
  kubectl port-forward svc/uap-frontend 8003:8003 -n adrion
  kubectl get pods -n adrion --watch

🎯 Next steps:
  1. Change secrets to production-grade values
  2. Setup monitoring (Prometheus + Grafana)
  3. Configure ingress with TLS
  4. Deploy to cloud (AWS/GCP/Azure)
  5. Setup automated backups
```

---

**Last Updated**: 2026-04-05 14:30 UTC
**Status**: 🟢 **PRODUCTION READY - LOCAL**
**Support**: Check Genesis Record `docs/` folder for additional guides
