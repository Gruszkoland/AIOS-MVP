# Docker to Kubernetes Migration Guide

## 5-Phase Migration (1-2 hours)

### Phase 1: Backup (10 min)

```bash
# Backup Docker database
docker exec adrion-postgres pg_dump -U adrion genesis_record > backup_$(date +%Y%m%d).sql

# Verify backup
wc -l backup_*.sql
```

### Phase 2: Kubernetes Setup (30 min)

```bash
# Apply manifests in order
kubectl apply -f kubernetes/00-namespace.yaml
kubectl apply -f kubernetes/01-secrets-configmaps.yaml
kubectl apply -f kubernetes/02-storage.yaml

# Wait for storage
kubectl get pvc -n adrion --watch

# Deploy PostgreSQL
kubectl apply -f kubernetes/03-postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n adrion --timeout=300s
```

### Phase 3: Restore Database (10 min)

```bash
# Restore backup
kubectl exec -i postgres-0 -n adrion -- \
  psql -U adrion -d genesis_record < backup_*.sql

# Verify
kubectl exec -it postgres-0 -n adrion -- \
  psql -U adrion -d genesis_record -c "\dt"
```

### Phase 4: Deploy Services (20 min)

```bash
# Backend
kubectl apply -f kubernetes/04-backend.yaml
kubectl wait --for=condition=ready pod -l app=uap-backend -n adrion --timeout=300s

# Frontend
kubectl apply -f kubernetes/05-frontend.yaml
kubectl wait --for=condition=ready pod -l app=uap-frontend -n adrion --timeout=300s

# Ingress
kubectl apply -f kubernetes/06-ingress.yaml
kubectl apply -f kubernetes/07-pgadmin-policies.yaml
```

### Phase 5: Verification (10 min)

```bash
# Check all pods
kubectl get pods -n adrion

# Test backend
kubectl port-forward -n adrion svc/uap-backend 8002:8002 &
curl -H "X-API-Key: local-dev-key-123" http://localhost:8002/mapi/v1/status

# Test frontend
kubectl port-forward -n adrion svc/uap-frontend 8003:8003 &
curl http://localhost:8003
```

## Post-Migration

1. Update Ingress domain
2. Install Ingress Controller
3. Setup monitoring (Prometheus/Grafana)
4. Configure backups
5. Test failover scenarios

## Rollback Plan

If issues occur during migration:

```bash
# Keep Docker services running during pilot
docker-compose ps

# Fall back to Docker if needed
docker-compose up -d

# Delete K8s resources
kubectl delete namespace adrion
```

---

**Total Time: 1-2 hours**
**Risk Level: Low (Docker remains running as fallback)**
