# ADRION 369 — Local Kubernetes Testing Guide

**Goal:** Get Kubernetes running locally in 15 minutes
**Status:** ✅ Step-by-step instructions

---

## Step 1: Enable Kubernetes in Docker Desktop (2 min)

1. Open **Docker Desktop**
2. Click **Settings** (⚙️ icon)
3. Go to **Kubernetes** tab
4. Check **Enable Kubernetes**
5. Click **Apply & Restart**
6. Wait 2-3 minutes for cluster to start

**Verify:**
```bash
kubectl cluster-info
kubectl get nodes
```

Expected output:
```
Kubernetes master is running at https://127.0.0.1:6443
CoreDNS is running at https://127.0.0.1:6443/api/v1/namespaces/kube-system/services/coredns:dns/proxy

NAME             STATUS   ROLES    AGE   VERSION
docker-desktop   Ready    master   2m    v1.27.0
```

✅ **Done!**

---

## Step 2: Deploy ADRION 369 (8 min)

```bash
# Navigate to project
cd "C:\Users\adiha\162 demencje w schemacie 369"

# Deploy all manifests
kubectl apply -f kubernetes/00-namespace.yaml
kubectl apply -f kubernetes/01-secrets-configmaps.yaml
kubectl apply -f kubernetes/02-storage.yaml
kubectl apply -f kubernetes/03-postgres.yaml
kubectl apply -f kubernetes/04-backend.yaml
kubectl apply -f kubernetes/05-frontend.yaml
kubectl apply -f kubernetes/06-ingress.yaml
kubectl apply -f kubernetes/07-pgadmin-policies.yaml

# Or in one command
kubectl apply -f kubernetes/*.yaml
```

**Verify deployment:**
```bash
kubectl get pods -n adrion --watch
```

Wait for all pods to be RUNNING:
```
NAME                               READY   STATUS    RESTARTS   AGE
postgres-0                         1/1     Running   0          2m
uap-backend-abc123                 1/1     Running   0          1m30s
uap-backend-def456                 1/1     Running   0          1m30s
uap-backend-ghi789                 1/1     Running   0          1m30s
uap-frontend-jkl012                1/1     Running   0          1m
uap-frontend-mno345                1/1     Running   0          1m
pgadmin-pqr678                     1/1     Running   0          30s
```

✅ **Done!**

---

## Step 3: Test Deployment (5 min)

### Test 1: Backend API

```bash
# Port forward backend
kubectl port-forward -n adrion svc/uap-backend 8002:8002 &

# Test API
curl -H "X-API-Key: local-dev-key-123" http://localhost:8002/mapi/v1/status

# Expected response: JSON with status info
```

### Test 2: Frontend

```bash
# Port forward frontend
kubectl port-forward -n adrion svc/uap-frontend 8003:8003 &

# Test
curl http://localhost:8003

# Expected: HTML content (frontend loads)
```

### Test 3: Database

```bash
# Connect to PostgreSQL
kubectl exec -it postgres-0 -n adrion -- \
  psql -U adrion -d genesis_record -c "SELECT version();"

# Expected: PostgreSQL 15.x output
```

### Test 4: Check Services

```bash
kubectl get svc -n adrion

# Expected output:
# NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)
# postgres        ClusterIP   None            <none>        5432/TCP
# uap-backend     ClusterIP   10.96.x.y       <none>        8002/TCP
# uap-frontend    ClusterIP   10.96.a.b       <none>        8003/TCP
# pgadmin         ClusterIP   10.96.p.q       <none>        5050/TCP
```

### Test 5: Check HPA (Auto-scaling)

```bash
kubectl get hpa -n adrion

# Expected output:
# NAME                    REFERENCE                          TARGETS           MINPODS   MAXPODS   REPLICAS   AGE
# uap-backend-hpa         Deployment/uap-backend             2%/70%, 5%/80%    3         10        3          1m
# uap-frontend-hpa        Deployment/uap-frontend            1%/75%, 3%/85%    2         5         2          1m
```

✅ **All Tests Passed!**

---

## Useful Commands for Daily Testing

| Command | Purpose |
|---------|---------|
| `kubectl get pods -n adrion` | List all pods |
| `kubectl logs -f deployment/uap-backend -n adrion` | Stream backend logs |
| `kubectl describe pod pod-name -n adrion` | Debug specific pod |
| `kubectl exec -it pod-name -n adrion -- sh` | Shell into pod |
| `kubectl port-forward svc/uap-backend 8002:8002 -n adrion` | Port forward |
| `kubectl scale deployment uap-backend --replicas=5 -n adrion` | Manual scale |
| `kubectl get hpa -n adrion --watch` | Watch auto-scaling |
| `kubectl delete pod pod-name -n adrion` | Delete pod (auto-recreated) |
| `kubectl top nodes` | Node resource usage |
| `kubectl top pod -n adrion` | Pod resource usage |

---

## Troubleshooting

### Pods stuck in Pending

```bash
# Check what's blocking
kubectl describe pod pod-name -n adrion

# Common causes:
# - Image pull issues: Check `kubectl logs pod-name -n adrion`
# - Storage not ready: `kubectl get pvc -n adrion`
# - Resource constraints: `kubectl top nodes`
```

### Database connection failed

```bash
# Check PostgreSQL is running
kubectl get pod postgres-0 -n adrion

# Test connectivity
kubectl exec -it uap-backend-0 -n adrion -- \
  nc -zv postgres.adrion.svc.cluster.local 5432

# Check logs
kubectl logs uap-backend-0 -n adrion
```

### Kill port forward

```bash
# Find process
lsof -i :8002

# Kill it
kill -9 <PID>
```

---

## What's Running?

```
Docker Desktop Kubernetes Cluster
├─ Namespace: adrion (isolated)
├─ PostgreSQL (1 pod, 50Gi storage)
├─ Backend API (3 pods, auto-scales to 10)
├─ Frontend (2 pods, auto-scales to 5)
├─ pgAdmin (1 pod)
└─ Networking:
   ├─ Service discovery (internal)
   ├─ Auto-scaling (HPA watching CPU/Memory)
   └─ Persistent storage (Docker Desktop default)
```

---

## Next Steps

1. ✅ Keep K8s running for testing
2. ⏳ Install/upgrade VS Code extension with K8s commands
3. ⏳ Run load testing (simulate traffic)
4. ⏳ Setup monitoring (Prometheus + Grafana)
5. ⏳ Deploy to cloud (AWS EKS, Google GKE, Azure AKS)

---

**Status:** 🟢 LOCAL KUBERNETES RUNNING
**Estimated time to here:** 15 minutes
**Ready to test:** YES
