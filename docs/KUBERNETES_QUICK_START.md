# ADRION 369 — Kubernetes Quick Start

## 5-Minute Setup

### 1. Verify kubectl is working
```bash
kubectl cluster-info
kubectl get nodes
```

### 2. Deploy all manifests
```bash
cd kubernetes
kubectl apply -f 00-namespace.yaml
kubectl apply -f 01-secrets-configmaps.yaml
kubectl apply -f 02-storage.yaml
kubectl apply -f 03-postgres.yaml
kubectl apply -f 04-backend.yaml
kubectl apply -f 05-frontend.yaml
kubectl apply -f 06-ingress.yaml
kubectl apply -f 07-pgadmin-policies.yaml
```

### 3. Wait for pods to be ready
```bash
kubectl get pods -n adrion --watch
```

### 4. Test services
```bash
# Port forward backend
kubectl port-forward -n adrion svc/uap-backend 8002:8002 &

# Test API
curl -H "X-API-Key: local-dev-key-123" http://localhost:8002/mapi/v1/status
```

## Verify Installation

✅ All pods running:
```bash
kubectl get pods -n adrion
```

✅ All services healthy:
```bash
kubectl get svc -n adrion
```

✅ Database ready:
```bash
kubectl exec -it postgres-0 -n adrion -- psql -U adrion -d genesis_record -c "SELECT COUNT(*) FROM tasks;"
```

## Common Commands

| Command | Purpose |
|---------|---------|
| `kubectl get pods -n adrion` | List all pods |
| `kubectl logs -f deployment/uap-backend -n adrion` | Stream backend logs |
| `kubectl port-forward svc/uap-backend 8002:8002 -n adrion` | Port forward |
| `kubectl describe pod pod-name -n adrion` | Debug pod |
| `kubectl scale deployment uap-backend --replicas=5 -n adrion` | Manual scale |

## Next Steps

1. Update 06-ingress.yaml with your domain
2. Install Ingress Controller: `helm install nginx-ingress ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace`
3. Setup monitoring: `helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace`

## Troubleshooting

If pod not running:
```bash
kubectl describe pod pod-name -n adrion
kubectl logs pod-name -n adrion
```

If database connection failed:
```bash
kubectl exec -it uap-backend-0 -n adrion -- nc -zv postgres.adrion.svc.cluster.local 5432
```

---

For detailed guide: See docs/KUBERNETES_DEPLOYMENT.md
