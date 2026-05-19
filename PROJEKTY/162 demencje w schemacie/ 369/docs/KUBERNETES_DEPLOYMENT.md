# ADRION 369 — Kubernetes Deployment Guide

**Status:** Production-Ready
**Version:** 1.0.0
**Date:** 2026-04-04

---

## 🎯 Quick Start (5 min)

```bash
# 1. Create namespace and secrets
kubectl apply -f kubernetes/00-namespace.yaml
kubectl apply -f kubernetes/01-secrets-configmaps.yaml

# 2. Setup storage
kubectl apply -f kubernetes/02-storage.yaml

# 3. Deploy PostgreSQL
kubectl apply -f kubernetes/03-postgres.yaml

# 4. Deploy Backend & Frontend
kubectl apply -f kubernetes/04-backend.yaml
kubectl apply -f kubernetes/05-frontend.yaml

# 5. Setup Ingress
kubectl apply -f kubernetes/06-ingress.yaml

# 6. HPA + pgAdmin
kubectl apply -f kubernetes/07-pgadmin-hpa-policies.yaml

# 7. Verify
kubectl get pods -n adrion
kubectl get svc -n adrion
```

---

## Prerequisites

- Kubernetes cluster (1.20+): minikube, Docker Desktop, EKS, GKE, AKS
- `kubectl` CLI configured and authenticated
- Ingress Controller: `nginx-ingress` or `traefik`
- Storage provisioner: local-path, EBS, GCP Persistent Disk, etc.
- Optional: `cert-manager` for automatic SSL certificates

### Install on Your Platform

**Minikube (local development):**
```bash
minikube start --cpus 4 --memory 8192 --disk-size 40gb
minikube addons enable ingress
minikube addons enable metrics-server
```

**Docker Desktop:**
- Go to Preferences → Kubernetes → Enable Kubernetes
- Ingress already included

**EKS (AWS):**
```bash
eksctl create cluster --name adrion --region us-east-1 --nodegroup-name ng --nodes 3 --instance-types t3.medium
```

**GKE (Google Cloud):**
```bash
gcloud container clusters create adrion --num-nodes 3 --machine-type e2-medium
```

**AKS (Azure):**
```bash
az aks create --resource-group adrion --name adrion-cluster --node-count 3 --vm-set-type VirtualMachineScaleSets
```

---

## File Structure

```
kubernetes/
├── 00-namespace.yaml              # Namespace: adrion
├── 01-secrets-configmaps.yaml     # Secrets + ConfigMaps
├── 02-storage.yaml                # PV + PVC + StorageClass
├── 03-postgres.yaml               # PostgreSQL StatefulSet
├── 04-backend.yaml                # UAP Backend Deployment
├── 05-frontend.yaml               # UAP Frontend Deployment
├── 06-ingress.yaml                # Ingress + TLS
└── 07-pgadmin-hpa-policies.yaml   # pgAdmin, HPA, Network policies
```

---

## Section 1: Namespace & Secrets

### Create namespace

```bash
kubectl apply -f kubernetes/00-namespace.yaml

# Verify
kubectl get ns adrion
```

### Create secrets

```bash
kubectl apply -f kubernetes/01-secrets-configmaps.yaml

# Edit secret to add real values
kubectl edit secret adrion-secrets -n adrion

# Key fields to set (32+ random characters):
# - POSTGRES_PASSWORD
# - PG_PASSWORD
# - UAP_API_KEY
# - JWT_SECRET
# - DRM_HMAC_SECRET
# - PGADMIN_DEFAULT_PASSWORD
```

### Generate random secrets

```bash
# Option 1: Using openssl
openssl rand -base64 32

# Option 2: Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 3: Using /dev/urandom
head -c 32 /dev/urandom | base64
```

### Verify secrets created

```bash
kubectl get secrets -n adrion
kubectl describe secret adrion-secrets -n adrion
```

---

## Section 2: Storage Setup

### Check available storage classes

```bash
kubectl get storageclass
```

### Create PV + PVC

```bash
kubectl apply -f kubernetes/02-storage.yaml

# Verify
kubectl get pv
kubectl get pvc -n adrion
```

### For different cloud providers

**AWS EBS:**
```yaml
# Update 02-storage.yaml:
storageClassName: ebs
provisioner: ebs.csi.aws.com
```

**Google Cloud Persistent Disk:**
```yaml
storageClassName: standard-rwo
provisioner: pd.csi.storage.gke.io
```

**Azure Disk:**
```yaml
storageClassName: managed-premium
provisioner: disk.csi.azure.com
```

---

## Section 3: Deploy PostgreSQL

```bash
kubectl apply -f kubernetes/03-postgres.yaml

# Wait for StatefulSet
kubectl wait --for=condition=ready pod -l app=postgres -n adrion --timeout=300s

# Verify
kubectl get statefulset -n adrion
kubectl get pods -n adrion -l app=postgres
```

### Initialize database

```bash
# Connect to PostgreSQL
kubectl exec -it postgres-0 -n adrion -- psql -U adrion -d genesis_record

# Run migrations (inside pod or from local machine)
kubectl exec -i postgres-0 -n adrion -- \
  psql -U adrion -d genesis_record < db/migrations/001_initial_schema.sql

kubectl exec -i postgres-0 -n adrion -- \
  psql -U adrion -d genesis_record < db/migrations/002_add_indexes.sql

# Verify tables created
kubectl exec -it postgres-0 -n adrion -- \
  psql -U adrion -d genesis_record -c "\dt"
```

### Backup database

```bash
# Full backup
kubectl exec -it postgres-0 -n adrion -- \
  pg_dump -U adrion genesis_record > genesis_record_backup.sql

# Compressed backup
kubectl exec -it postgres-0 -n adrion -- \
  pg_dump -U adrion -Fc genesis_record > genesis_record_backup.dump

# To cloud storage (AWS S3 example)
kubectl exec -it postgres-0 -n adrion -- \
  pg_dump -U adrion genesis_record | \
  aws s3 cp - s3://adrion-backups/genesis_record_$(date +%Y-%m-%d).sql.gz
```

---

## Section 4: Deploy Backend

### Build and push Docker image

```bash
# Build
docker build -t your-registry/uap-backend:latest ./uap

# Push to registry (Docker Hub, ECR, GCR, ACR)
docker push your-registry/uap-backend:latest

# Update image in 04-backend.yaml
# Change: image: uap-backend:latest
# To: image: your-registry/uap-backend:latest
```

### Deploy

```bash
kubectl apply -f kubernetes/04-backend.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s \
  deployment -l app=uap-backend -n adrion

# Verify
kubectl get deployment -n adrion
kubectl get pods -n adrion -l app=uap-backend
```

### Check logs

```bash
# View logs from one pod
kubectl logs -n adrion deployment/uap-backend --tail=100

# Stream logs (follow)
kubectl logs -f -n adrion deployment/uap-backend

# Logs from specific pod
kubectl logs -n adrion uap-backend-xyz123 -c uap-backend
```

### Port forward for testing

```bash
kubectl port-forward -n adrion svc/uap-backend 8002:8002

# Test
curl -H "X-API-Key: local-dev-key-123" http://localhost:8002/mapi/v1/status
```

---

## Section 5: Deploy Frontend

```bash
kubectl apply -f kubernetes/05-frontend.yaml

# Verify
kubectl get deployment -n adrion -l app=uap-frontend
kubectl get pods -n adrion -l app=uap-frontend

# Port forward
kubectl port-forward -n adrion svc/uap-frontend 8003:8003

# Test
curl http://localhost:8003
```

---

## Section 6: Setup Ingress

### Prerequisites: Install Ingress Controller

**NGINX Ingress Controller:**
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

### Optional: Install cert-manager (for automatic SSL)

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true
```

### Deploy Ingress

```bash
# First, update domain in 06-ingress.yaml
# Change: adrion.example.com → your-domain.com

kubectl apply -f kubernetes/06-ingress.yaml

# Wait for certificate (if using cert-manager)
kubectl wait --for=condition=ready certificate -n adrion --timeout=300s

# Verify Ingress
kubectl get ingress -n adrion
kubectl describe ingress adrion-ingress -n adrion

# Get external IP
kubectl get service -n ingress-nginx
```

### Access your application

```bash
# Option 1: Using domain (if you have DNS configured)
https://adrion.example.com

# Option 2: Using LoadBalancer IP
# Get IP from: kubectl get service -n ingress-nginx
# Then add to /etc/hosts: 1.2.3.4 adrion.example.com

# Option 3: For minikube
minikube service -n adrion uap-frontend
```

---

## Section 7: Auto-scaling & Policies

### Deploy HPA, pgAdmin, Network Policies

```bash
kubectl apply -f kubernetes/07-pgadmin-hpa-policies.yaml

# Verify HPA
kubectl get hpa -n adrion
kubectl describe hpa uap-backend-hpa -n adrion

# Verify PDB
kubectl get pdb -n adrion

# Verify Network Policies
kubectl get networkpolicy -n adrion
```

### Monitor autoscaling

```bash
# Watch HPA in real-time
kubectl get hpa uap-backend-hpa -n adrion --watch

# Simulate load (for testing HPA)
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- \
  sh -c "while sleep 0.01; do wget -q -O- http://uap-backend.adrion.svc.cluster.local:8002/mapi/v1/status; done"
```

---

## Monitoring & Observability

### Install Prometheus Stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

### Access Prometheus & Grafana

```bash
# Prometheus
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open: http://localhost:9090

# Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:3000
# Open: http://localhost:3000
# Default login: admin / prom-operator
```

### Install Loki for logs

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set loki.enabled=true \
  --set promtail.enabled=true
```

---

## Common Operations

### View all resources

```bash
kubectl get all -n adrion
```

### Describe resources

```bash
kubectl describe deployment uap-backend -n adrion
kubectl describe pod uap-backend-xyz123 -n adrion
kubectl describe service postgres -n adrion
```

### Edit resources

```bash
kubectl edit deployment uap-backend -n adrion
kubectl edit secret adrion-secrets -n adrion
kubectl edit configmap adrion-config -n adrion
```

### Rollback deployment

```bash
# View rollout history
kubectl rollout history deployment/uap-backend -n adrion

# Rollback to previous version
kubectl rollout undo deployment/uap-backend -n adrion

# Rollback to specific revision
kubectl rollout undo deployment/uap-backend -n adrion --to-revision=2
```

### Scale deployment

```bash
# Manual scaling
kubectl scale deployment uap-backend --replicas=5 -n adrion

# Check HPA status (HPA will revert manual scaling)
kubectl get hpa uap-backend-hpa -n adrion
```

### Delete resources

```bash
# Delete entire deployment
kubectl delete deployment uap-backend -n adrion

# Delete all resources in namespace
kubectl delete all -n adrion

# Delete entire namespace (WARNING: destructive)
kubectl delete namespace adrion
```

---

## Troubleshooting

### Pod not starting

```bash
# Check pod status
kubectl describe pod uap-backend-xyz123 -n adrion

# View logs
kubectl logs uap-backend-xyz123 -n adrion

# Check events
kubectl get events -n adrion --sort-by='.lastTimestamp' | tail -20
```

### Database connection failed

```bash
# Test PostgreSQL connectivity
kubectl run -it --rm debug --image=alpine --restart=Never -- \
  sh -c "apk add --no-cache postgresql-client && \
  psql -h postgres.adrion.svc.cluster.local -U adrion -d genesis_record -c 'SELECT version();'"
```

### Ingress not working

```bash
# Check Ingress status
kubectl describe ingress adrion-ingress -n adrion

# Verify Ingress Controller
kubectl get pods -n ingress-nginx

# Check Ingress Controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

### Out of memory

```bash
# Check pod memory usage
kubectl top pod -n adrion

# Check node memory
kubectl top node

# Increase resource limits in deployment YAML
```

---

## Production Checklist

- [ ] Use external secret store (Vault, AWS Secrets Manager, Azure Key Vault)
- [ ] Enable RBAC (role-based access control)
- [ ] Setup Pod Security Standards (PSS)
- [ ] Configure network policies
- [ ] Setup monitoring (Prometheus + Grafana)
- [ ] Setup logging (ELK, Loki, Datadog)
- [ ] Setup alerting
- [ ] Configure backup and disaster recovery
- [ ] Setup multi-region failover (if needed)
- [ ] Security scanning (Trivy, Anchore)
- [ ] Setup CI/CD pipeline
- [ ] Document runbooks for incident response

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `kubectl apply -f file.yaml` | Deploy resource |
| `kubectl get pods -n adrion` | List pods |
| `kubectl logs pod-name -n adrion` | View logs |
| `kubectl exec -it pod-name -n adrion -- sh` | Shell into pod |
| `kubectl port-forward svc/name 8080:80 -n adrion` | Port forward |
| `kubectl scale deployment name --replicas=3 -n adrion` | Scale |
| `kubectl rollout undo deployment/name -n adrion` | Rollback |
| `kubectl delete -f file.yaml` | Delete resource |

---

**Status:** 🟢 PRODUCTION-READY
**Last Updated:** 2026-04-04
