# ADRION 369 Kubernetes Deployment Script for Windows PowerShell
# Complete orchestration deployment for all 12 services

$NAMESPACE = "adrion-369"
$ErrorActionPreference = "Stop"

function Log-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Log-Success { Write-Host "[OK]  $args" -ForegroundColor Green }
function Log-Error { Write-Host "[ERR] $args" -ForegroundColor Red }
function Log-Warn { Write-Host "[!]   $args" -ForegroundColor Yellow }

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ADRION 369 v4.0 — Kubernetes Full Stack Deploy" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan

# Check kubectl is available
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Log-Error "kubectl not found. Please install kubectl"
    exit 1
}

Log-Info "Kubernetes version:"
kubectl version --short

Log-Info "Applying manifests in order:"

try {
    # PHASE 0: Namespace & RBAC
    Log-Info "→ Phase 0: Namespace & RBAC"
    kubectl apply -f kubernetes/00-namespace/adrion-namespace.yaml | Out-Null
    Log-Success "Namespace 'adrion-369' created"

    # PHASE 1: Storage
    Log-Info "→ Phase 1: Storage Classes & PersistentVolumes"
    kubectl apply -f kubernetes/01-storage/storage-volumes.yaml 2>$null | Out-Null
    Log-Success "Storage configured"

    # PHASE 2: Config & Secrets
    Log-Info "→ Phase 2: ConfigMaps & Secrets"
    kubectl apply -f kubernetes/02-config/configmap-secrets.yaml | Out-Null
    Log-Success "Configurations loaded"

    # PHASE 3: PostgreSQL (dependency root)
    Log-Info "→ Phase 3: PostgreSQL StatefulSet"
    kubectl apply -f kubernetes/03-postgres/postgres-statefulset.yaml | Out-Null
    Log-Info "Waiting for PostgreSQL to be ready (timeout 5m)..."
    kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s 2>$null | Out-Null
    Log-Success "PostgreSQL ready"

    # PHASE 4: Tier 1
    Log-Info "→ Phase 4: Tier 1 Services (Redis, Ollama, N8N)"
    kubectl apply -f kubernetes/04-tier1/tier1-deployments.yaml | Out-Null
    Log-Success "Tier 1 deployed"

    # PHASE 5: Core services
    Log-Info "→ Phase 5: Core Services (N8N, Vortex, Healer, API)"
    kubectl apply -f kubernetes/05-core/core-deployments.yaml | Out-Null
    Log-Success "Core services deployed"

    # PHASE 6: Monitoring
    Log-Info "→ Phase 6: Monitoring Stack (Prometheus, Grafana, Loki)"
    kubectl apply -f kubernetes/06-monitoring/monitoring-deployments.yaml | Out-Null
    Log-Success "Monitoring deployed"

    # PHASE 7: Networking & Ingress
    Log-Info "→ Phase 7: Networking & Ingress"
    kubectl apply -f kubernetes/07-networking/ingress-networking.yaml | Out-Null
    Log-Success "Networking configured"

    # PHASE 8: Backup Jobs
    Log-Info "→ Phase 8: Backup CronJobs"
    kubectl apply -f kubernetes/08-jobs/backup-jobs.yaml | Out-Null
    Log-Success "Backup jobs configured"

    # Status check
    Log-Info "Checking deployment status..."
    Write-Host ""
    Write-Host "Namespace: $NAMESPACE" -ForegroundColor Yellow
    Write-Host "Pods status:" -ForegroundColor Yellow
    kubectl get pods -n $NAMESPACE -o wide

    Write-Host ""
    Write-Host "Services:" -ForegroundColor Yellow
    kubectl get svc -n $NAMESPACE

    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Log-Success "Deployment completed!"
    Write-Host ""

    Log-Info "Useful commands:"
    Write-Host "  kubectl get pods -n $NAMESPACE -w                    # Watch pods"
    Write-Host "  kubectl logs -n $NAMESPACE <pod-name>               # View logs"
    Write-Host "  kubectl port-forward -n $NAMESPACE svc/api 8001     # Forward API"
    Write-Host "  kubectl describe deployment -n $NAMESPACE api       # Details"
    Write-Host "  kubectl delete namespace $NAMESPACE                 # Remove all"
    Write-Host ""

    Log-Info "Port-forward commands:"
    Write-Host "  kubectl port-forward -n $NAMESPACE svc/api 8001:8001         # API"
    Write-Host "  kubectl port-forward -n $NAMESPACE svc/grafana 3000:3000     # Grafana"
    Write-Host "  kubectl port-forward -n $NAMESPACE svc/prometheus 9090:9090  # Prometheus"
    Write-Host "  kubectl port-forward -n $NAMESPACE svc/n8n 5678:5678         # N8N"
    Write-Host ""

    Log-Warn "Note: Access services via localhost:port after port-forward"

} catch {
    Log-Error "Deployment failed: $_"
    exit 1
}

exit 0
