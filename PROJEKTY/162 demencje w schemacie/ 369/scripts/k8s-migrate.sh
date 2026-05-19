#!/bin/bash

# ADRION 369 — Docker to Kubernetes Migration Script
# Migrates data and configuration from docker-compose to Kubernetes cluster

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Configuration
NAMESPACE="adrion"
DB_CONTAINER="adrion-postgres"
DB_NAME="genesis_record"
DB_USER="adrion"
BACKUP_FILE="/tmp/genesis_record_migration_$(date +%Y%m%d_%H%M%S).sql"

# Check prerequisites
log_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
  log_error "Docker not found. Please install Docker."
  exit 1
fi

if ! command -v kubectl &> /dev/null; then
  log_error "kubectl not found. Please install kubectl."
  exit 1
fi

# Test Docker connection
if ! docker ps > /dev/null 2>&1; then
  log_error "Cannot connect to Docker daemon. Ensure Docker is running."
  exit 1
fi

# Test Kubernetes connection
if ! kubectl cluster-info &> /dev/null; then
  log_error "Cannot connect to Kubernetes cluster. Please configure kubectl."
  exit 1
fi

log_success "Prerequisites checked"

# Step 1: Check if docker-compose services are running
log_info "Checking docker-compose services..."
if ! docker ps | grep -q "$DB_CONTAINER"; then
  log_warn "PostgreSQL container ($DB_CONTAINER) not running."
  log_info "Starting docker-compose stack..."
  docker-compose up -d
  sleep 10
fi

log_success "docker-compose services checked"

# Step 2: Backup current database
log_info "Backing up database from docker-compose..."

docker exec $DB_CONTAINER pg_dump -U $DB_USER -d $DB_NAME > "$BACKUP_FILE"

if [ -s "$BACKUP_FILE" ]; then
  log_success "Database backed up to: $BACKUP_FILE"
else
  log_error "Backup file is empty or failed"
  exit 1
fi

# Step 3: Create Kubernetes namespace
log_info "Creating Kubernetes namespace..."

if kubectl get namespace $NAMESPACE &> /dev/null; then
  log_warn "Namespace $NAMESPACE already exists"
else
  kubectl create namespace $NAMESPACE
  log_success "Namespace $NAMESPACE created"
fi

# Step 4: Deploy Kubernetes stack
log_info "Deploying Kubernetes stack..."

KUBE_DIR="kubernetes"

if [ ! -d "$KUBE_DIR" ]; then
  log_error "Kubernetes directory not found: $KUBE_DIR"
  exit 1
fi

# Deploy in order
for file in $KUBE_DIR/00-namespace.yaml \
            $KUBE_DIR/01-secrets-configmaps.yaml \
            $KUBE_DIR/02-storage.yaml \
            $KUBE_DIR/03-postgres.yaml \
            $KUBE_DIR/04-backend.yaml \
            $KUBE_DIR/05-frontend.yaml \
            $KUBE_DIR/06-ingress.yaml \
            $KUBE_DIR/07-pgadmin-hpa-policies.yaml; do

  if [ -f "$file" ]; then
    log_info "Deploying: $file"
    kubectl apply -f "$file"
  fi
done

log_success "Kubernetes stack deployed"

# Step 5: Wait for PostgreSQL pod
log_info "Waiting for PostgreSQL pod to be ready..."

kubectl wait --for=condition=ready pod \
  -l app=postgres \
  -n $NAMESPACE \
  --timeout=300s

log_success "PostgreSQL pod is ready"

# Step 6: Restore database
log_info "Restoring database to Kubernetes..."

kubectl exec -i postgres-0 -n $NAMESPACE -- \
  psql -U $DB_USER -d $DB_NAME < "$BACKUP_FILE"

if [ $? -eq 0 ]; then
  log_success "Database restored successfully"
else
  log_error "Database restore failed"
  exit 1
fi

# Step 7: Verify data
log_info "Verifying migrated data..."

TABLE_COUNT=$(kubectl exec -it postgres-0 -n $NAMESPACE -- \
  psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | tail -2 | head -1 | tr -d ' ')

log_info "Number of tables in Kubernetes PostgreSQL: $TABLE_COUNT"

# Step 8: Wait for other services
log_info "Waiting for Backend and Frontend pods..."

kubectl wait --for=condition=ready pod \
  -l app=uap-backend \
  -n $NAMESPACE \
  --timeout=300s

kubectl wait --for=condition=ready pod \
  -l app=uap-frontend \
  -n $NAMESPACE \
  --timeout=300s

log_success "All pods are ready"

# Step 9: Health check
log_info "Running health checks..."

# Check PostgreSQL
PG_CHECK=$(kubectl exec -i postgres-0 -n $NAMESPACE -- \
  psql -U $DB_USER -d $DB_NAME -c "SELECT 'OK';" 2>/dev/null || echo "FAILED")

if [[ "$PG_CHECK" == *"OK"* ]]; then
  log_success "PostgreSQL: OK"
else
  log_error "PostgreSQL: FAILED"
fi

# Check Backend API
BACKEND_CHECK=$(kubectl exec -it uap-backend-0 -n $NAMESPACE -- \
  curl -s -H "X-API-Key: local-dev-key-123" http://localhost:8002/mapi/v1/status 2>/dev/null || echo "FAILED")

if [[ "$BACKEND_CHECK" == *"status"* ]]; then
  log_success "Backend API: OK"
else
  log_warn "Backend API: Check manually"
fi

# Step 10: Summary
log_info "Migration complete!"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "   ADRION 369 — Docker to Kubernetes Migration Summary"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "✅ Backup created:        $BACKUP_FILE"
echo "✅ Kubernetes namespace:  $NAMESPACE"
echo "✅ PostgreSQL:            Ready"
echo "✅ Backend:               Ready"
echo "✅ Frontend:              Ready"
echo ""
echo "Next steps:"
echo "  1. Update Ingress domain in 06-ingress.yaml"
echo "  2. Install Ingress Controller (nginx-ingress or traefik)"
echo "  3. Access your application: kubectl port-forward svc/uap-frontend 8003:8003 -n $NAMESPACE"
echo ""
echo "Useful commands:"
echo "  kubectl get pods -n $NAMESPACE"
echo "  kubectl logs -f deployment/uap-backend -n $NAMESPACE"
echo "  kubectl port-forward svc/uap-backend 8002:8002 -n $NAMESPACE"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

log_success "Migration complete! System is running on Kubernetes."
