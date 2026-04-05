#!/bin/bash
# ADRION 369 Kubernetes Deployment Script
# Complete orchestration deployment for all 12 services

set -e

NAMESPACE="adrion-369"
KUBE_CONFIG="${KUBECONFIG:-$HOME/.kube/config}"

echo "═══════════════════════════════════════════════════════"
echo "  ADRION 369 v4.0 — Kubernetes Full Stack Deploy"
echo "═══════════════════════════════════════════════════════"

# Color output functions
log_info() {
    echo -e "\033[0;36m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[✓]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

log_warn() {
    echo -e "\033[0;33m[!]\033[0m $1"
}

# Check kubectl is available
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl not found. Please install kubectl:"
    echo "  https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

log_info "Kubernetes version:"
kubectl version --short

log_info "Applying manifests in order:"

# PHASE 0: Namespace & RBAC
log_info "→ Phase 0: Namespace & RBAC"
kubectl apply -f kubernetes/00-namespace/adrion-namespace.yaml
log_success "Namespace 'adrion-369' created"

# PHASE 1: Storage
log_info "→ Phase 1: Storage Classes & PersistentVolumes"
kubectl apply -f kubernetes/01-storage/storage-volumes.yaml
log_success "Storage configured"

# PHASE 2: Config & Secrets
log_info "→ Phase 2: ConfigMaps & Secrets"
kubectl apply -f kubernetes/02-config/configmap-secrets.yaml
log_success "Configurations loaded"

# PHASE 3: PostgreSQL (dependency root)
log_info "→ Phase 3: PostgreSQL StatefulSet"
kubectl apply -f kubernetes/03-postgres/postgres-statefulset.yaml
log_info "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s 2>/dev/null || true

# PHASE 4: Tier 1 (Logging & AI)
log_info "→ Phase 4: Tier 1 Services (Loki, Promtail, Ollama)"
kubectl apply -f kubernetes/04-tier1/tier1-deployments.yaml
log_success "Tier 1 deployed"

# PHASE 5: Core services
log_info "→ Phase 5: Core Services (N8N, Vortex, Healer, API)"
kubectl apply -f kubernetes/05-core/core-deployments.yaml
log_success "Core services deployed"

# PHASE 6: Monitoring
log_info "→ Phase 6: Monitoring Stack (Prometheus, Grafana)"
kubectl apply -f kubernetes/06-monitoring/monitoring-deployments.yaml
log_success "Monitoring deployed"

# PHASE 7: Networking & Ingress
log_info "→ Phase 7: Networking & Ingress"
kubectl apply -f kubernetes/07-networking/ingress-networking.yaml
log_success "Networking configured"

# PHASE 8: Backup Jobs
log_info "→ Phase 8: Backup CronJobs"
kubectl apply -f kubernetes/08-jobs/backup-jobs.yaml
log_success "Backup jobs configured"

# Status check
log_info "Checking deployment status..."
echo ""
echo "Namespace: $NAMESPACE"
echo "Pods status:"
kubectl get pods -n $NAMESPACE -o wide

echo ""
echo "Services:"
kubectl get svc -n $NAMESPACE

echo ""
echo "═══════════════════════════════════════════════════════"
log_success "Deployment completed!"
echo ""
log_info "Useful commands:"
echo "  kubectl get pods -n $NAMESPACE -w          # Watch pods"
echo "  kubectl logs -n $NAMESPACE <pod-name>      # View logs"
echo "  kubectl port-forward -n $NAMESPACE svc/api 8001:8001  # Forward API"
echo "  kubectl describe deployment -n $NAMESPACE api         # Details"
echo "  kubectl delete namespace $NAMESPACE        # Remove all"
echo ""
log_info "Access via kubectl port-forward:"
echo "  API:        kubectl port-forward -n $NAMESPACE svc/api 8001:8001"
echo "  Grafana:    kubectl port-forward -n $NAMESPACE svc/grafana 3000:3000"
echo "  Prometheus: kubectl port-forward -n $NAMESPACE svc/prometheus 9090:9090"
echo "  N8N:        kubectl port-forward -n $NAMESPACE svc/n8n 5678:5678"
echo ""
log_warn "Note: Replace 'localhost' with your Kubernetes cluster IP or domain"
