# Kubernetes ↔ UAP Integration — DEPLOYMENT QUICK START

**Date:** 2026-04-06
**Status:** 🚀 **READY FOR DEPLOYMENT**

---

## 📋 DEPLOYMENT OPTIONS

### Option 1: Local Development (Docker Compose)

**Prerequisites:**

- Docker & Docker Compose installed
- Python 3.9+ with .venv activated

**Steps:**

```bash
# 1. Navigate to project root
cd c:\Users\adiha\162 demencje w schemacie 369

# 2. Build and start all services
docker-compose -f docker-compose.k8s-integration.yml up -d

# 3. Wait for services to be healthy (30-60 seconds)
docker-compose -f docker-compose.k8s-integration.yml ps

# 4. Verify backend health
curl -X GET http://localhost:8002/mapi/v1/health

# 5. Access services
- Backend API:    http://localhost:8002/mapi/v1/kubernetes/
- Frontend:       http://localhost:8003/k8s-dashboard.html
- Grafana:        http://localhost:3000 (admin/admin)
- Prometheus:     http://localhost:9090
```

**Monitor Logs:**

```bash
# All services
docker-compose -f docker-compose.k8s-integration.yml logs -f

# Specific service
docker-compose -f docker-compose.k8s-integration.yml logs -f uap-backend
```

**Shutdown:**

```bash
docker-compose -f docker-compose.k8s-integration.yml down
```

---

### Option 2: Kubernetes Deployment

**Prerequisites:**

- kubectl configured
- Access to K8s cluster (docker-desktop, AKS, EKS, etc.)
- Python 3.9+ with .venv activated

**Steps:**

```bash
# 1. Ensure namespace exists or create it
kubectl create namespace adrion-369

# 2. Run deployment pipeline
python scripts/deploy_k8s_uap_integration.py --namespace adrion-369 --context docker-desktop

# 3. Verify deployment
kubectl get pods -n adrion-369
kubectl get services -n adrion-369
kubectl get configmaps -n adrion-369

# 4. Port-forward to access services
kubectl port-forward -n adrion-369 svc/uap-backend 8002:8002 &
kubectl port-forward -n adrion-369 svc/uap-frontend 8003:8003 &

# 5. Access services (same URLs as Option 1)
```

**View Logs:**

```bash
# Backend logs
kubectl logs -n adrion-369 -f deployment/uap-backend

# Follow all pods
kubectl logs -n adrion-369 -f --all-containers=true
```

---

### Option 3: Manual Local Launch

**Prerequisites:**

- Python 3.9+
- Virtual environment activated: `.venv\Scripts\Activate.ps1`
- kubectl installed (for K8s integration)

**Steps:**

```bash
# 1. Activate virtual environment
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database
python scripts/init_local_db.py

# 4. Start backend API
python uap/backend/api.py

# 5. In new terminal, start frontend
cd uap/frontend
python -m http.server 8003

# 6. Access services
- Backend API:    http://localhost:8002/mapi/v1/kubernetes/
- Frontend:       http://localhost:8003/k8s-dashboard.html
```

---

## 🧪 TESTING

### Run Unit Tests (Mocked)

```bash
python tests/test_k8s_mocked_comprehensive.py
```

### Run Integration Tests

```bash
python tests/test_k8s_integration_e2e.py
```

### Test API Endpoints

```bash
python scripts/test_k8s_api.py --api-key test-key --host localhost --port 8002
```

---

## 🔍 VERIFICATION CHECKLIST

After deployment, verify:

- [ ] Backend API responds to health check

  ```bash
  curl -X GET http://localhost:8002/mapi/v1/health
  ```

- [ ] Kubernetes cluster-info endpoint works

  ```bash
  curl -X GET http://localhost:8002/mapi/v1/kubernetes/cluster-info \
    -H "X-API-Key: test-key"
  ```

- [ ] Pods endpoint returns pod list

  ```bash
  curl -X GET http://localhost:8002/mapi/v1/kubernetes/pods \
    -H "X-API-Key: test-key"
  ```

- [ ] SSE stream endpoint is accessible

  ```bash
  curl -X GET http://localhost:8002/mapi/v1/kubernetes/stream \
    -H "X-API-Key: test-key"
  ```

- [ ] Frontend dashboard loads

  ```
  Open: http://localhost:8003/k8s-dashboard.html
  ```

- [ ] Real-time streaming works (click "Start Stream" button)

---

## 📊 DASHBOARD ACCESS

### Kubernetes Dashboard UI

- **URL:** http://localhost:8003/k8s-dashboard.html
- **Features:**
  - Cluster health overview
  - Pod status grid (running/pending/failed)
  - Services discovery
  - Deployments tracking
  - Events timeline
  - Real-time stream controls

### Monitoring Stack

**Grafana Dashboards:**

- URL: http://localhost:3000
- Default: admin / admin
- Pre-configured datasources: Prometheus, Loki

**Prometheus Metrics:**

- URL: http://localhost:9090
- PromQL available for custom queries

**Loki Logs:**

- Integrated in Grafana
- View logs from Kubernetes components

---

## 🐛 TROUBLESHOOTING

### Backend API won't start

```bash
# Check port 8002 is available
netstat -ano | findstr :8002

# Or specify different port
$env:MAPI_PORT = 8003
python uap/backend/api.py
```

### Frontend can't reach API

- Check CORS headers in backend
- Verify API URL in k8s_dashboard.js
- Check X-API-Key header is set

### Real-time streaming not working

- Verify WebSocket watcher is enabled: `K8S_WATCHER_ENABLED=true`
- Check kubectl is accessible
- View backend logs for watcher errors

### kubectl timeout

- Increase timeout: `kubectl config set-context --current --kube-api-burst=40`
- Check K8s cluster connectivity
- Check firewall rules

---

## 📈 SCALING

### Horizontal Scaling (Multiple Backend Instances)

```bash
# With K8s
kubectl scale deployment uap-backend -n adrion-369 --replicas=3

# With Docker Compose
docker-compose -f docker-compose.k8s-integration.yml up -d --scale uap-backend=3
```

### Load Balancing

- Deploy nginx ingress
- Configure service mesh (Istio)
- Setup HAProxy reverse proxy

---

## 🔐 SECURITY

### API Authentication

All endpoints require `X-API-Key` header:

```bash
curl -H "X-API-Key: your-secure-key" http://localhost:8002/mapi/v1/kubernetes/pods
```

### TLS/HTTPS

For production:

```bash
# Enable HTTPS in Flask
export FLASK_SSL_CERT=cert.pem
export FLASK_SSL_KEY=key.pem

# Or use reverse proxy (nginx)
```

### Network Policy

Apply K8s network policies:

```bash
kubectl apply -f kubernetes/network-policy.yaml
```

---

## 📊 MONITORING

### Health Checks

- Backend: `GET /mapi/v1/health` (returns 200 if healthy)
- Frontend: Static files accessible
- Database: Connection verified on startup

### Metrics Endpoints

- Prometheus: `http://localhost:9090/metrics`
- Custom K8s metrics: Available via K8s API

### Alerting

Configure alerts in Prometheus:

```yaml
groups:
  - name: k8s-integration
    rules:
      - alert: BackendDown
        expr: up{job="uap-backend"} == 0
        for: 1m
```

---

## 🚀 PRODUCTION DEPLOYMENT

### Pre-Production Checklist

- [ ] Configuration reviewed
- [ ] API keys rotated
- [ ] SSL/TLS certificates installed
- [ ] Backup strategy configured
- [ ] Monitoring alerts configured
- [ ] Load testing completed
- [ ] Security audit passed

### Deployment Steps

1. **Prepare cluster:** `kubectl create namespace adrion-369`
2. **Configure secrets:** `kubectl create secret generic uap-secrets -n adrion-369`
3. **Deploy:** `python scripts/deploy_k8s_uap_integration.py --namespace adrion-369`
4. **Verify:** Check all pods and services are running
5. **Monitor:** Watch logs and metrics

### Rollback

```bash
# If deployment fails
kubectl rollout undo deployment/uap-backend -n adrion-369

# Check history
kubectl rollout history deployment/uap-backend -n adrion-369
```

---

## 📞 SUPPORT

### Logs & Diagnostics

```bash
# Backend logs
kubectl logs -f deployment/uap-backend -n adrion-369

# Events
kubectl get events -n adrion-369

# Describe pod for details
kubectl describe pod <pod-name> -n adrion-369

# Check resource usage
kubectl top pods -n adrion-369
```

### Common Issues & Solutions

| Issue                      | Solution                               |
| -------------------------- | -------------------------------------- |
| 503 Kubernetes unavailable | kubectl must be accessible, check PATH |
| Connection refused on 8002 | Port in use or firewall blocking       |
| API Key rejected           | Verify header: `X-API-Key: <key>`      |
| Real-time not updating     | K8s watcher may be failing, check logs |
| Frontend CORS error        | Add CORS headers to Flask backend      |

---

## 📈 PERFORMANCE TUNING

### Connection Pooling

```python
# In uap/backend/config.py
DB_POOL_SIZE = 20
DB_POOL_RECYCLE = 3600
```

### Cache Configuration

```bash
export CACHE_BACKEND=redis
export REDIS_URL=redis://localhost:6379/0
```

### Memory Limits

```bash
# In K8s deployment
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "250m"
```

---

## 🎯 NEXT STEPS

1. **Choose deployment option** (1, 2, or 3)
2. **Run pre-flight checks** (prerequisites)
3. **Execute deployment** (follow steps)
4. **Run verification checklist** (confirm working)
5. **Monitor logs** (watch for errors)
6. **Test real-time streaming** (click Start Stream)
7. **Configure for production** (security, scaling, monitoring)

---

## 📝 DEPLOYMENT LOG

Record deployment information:

```
Date: 2026-04-06
Option: [1/2/3]
Namespace: adrion-369
Status: [IN_PROGRESS/SUCCESSFUL/FAILED]
Start Time: [timestamp]
End Time: [timestamp]
Notes:
```

---

**Questions? Check the comprehensive deployment report:**

```
Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/DEPLOYMENT/deployment_report_*.json
```

**Status: ✅ READY FOR DEPLOYMENT** 🚀
