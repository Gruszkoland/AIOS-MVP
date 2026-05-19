#!/bin/bash

# ADRION 369 — Oracle Cloud Automated Deployment Script
# Runs on Ubuntu 22.04 LTS VM in Oracle Cloud
# Usage: bash oracle-deploy.sh <environment>

set -e

ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# STEP 1: System Prerequisites
# ============================================================================

log_info "Step 1: Checking system prerequisites..."

if ! command -v docker &> /dev/null; then
    log_warn "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    sudo usermod -aG docker ubuntu
    log_info "Docker installed. Please log out and back in for group permissions."
    exit 0
fi

if ! command -v docker-compose &> /dev/null; then
    log_warn "Docker Compose not found. Installing..."
    sudo apt update -qq && sudo apt install -y -qq docker-compose-plugin
fi

docker --version
docker-compose --version

log_info "✓ System prerequisites satisfied"

# ============================================================================
# STEP 2: Clone/Update Repository
# ============================================================================

log_info "Step 2: Setting up repository..."

if [ ! -d "$PROJECT_ROOT/.git" ]; then
    log_warn "Not a git repository. Assuming ADRION-369 is already cloned."
else
    log_info "Updating repository..."
    cd "$PROJECT_ROOT"
    git fetch origin
    git checkout main
    git pull origin main
fi

log_info "✓ Repository ready"

# ============================================================================
# STEP 3: Environment Configuration
# ============================================================================

log_info "Step 3: Configuring environment..."

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    log_warn ".env file not found. Creating with defaults..."

    # Generate random passwords
    DB_PASSWORD=$(openssl rand -base64 32)
    SECRET_KEY=$(openssl rand -base64 32)
    API_KEY=$(openssl rand -hex 32)
    GRAFANA_PASSWORD=$(openssl rand -base64 16)

    cat > "$PROJECT_ROOT/.env" << EOF
# ADRION 369 — Oracle Cloud Production Configuration
ENVIRONMENT=$ENVIRONMENT
FLASK_ENV=$ENVIRONMENT
LLM_BACKEND=${LLM_BACKEND:-openrouter}

# Database Configuration (set DB_HOST when database VM is ready)
DB_HOST=${DB_HOST:-localhost}
DB_PORT=5432
DB_NAME=adrion_production
DB_USER=adrion_user
DB_PASSWORD=$DB_PASSWORD
DB_POOL_SIZE=10
DB_POOL_RECYCLE=3300

# Security
SECRET_KEY=$SECRET_KEY
UAP_API_KEY=$API_KEY

# Services Configuration
MAPI_HOST=0.0.0.0
MAPI_PORT=8002

# Monitoring
PROMETHEUS_RETENTION=720h
GRAFANA_ADMIN_PASSWORD=$GRAFANA_PASSWORD

# LLM (optional)
OPENROUTER_KEY=${OPENROUTER_KEY:-}

# CORS
CORS_ALLOWED_ORIGIN=http://localhost:8003
EOF

    log_warn "📝 .env file created with defaults. Update with actual values:"
    log_warn "  - DB_HOST: IP of database VM"
    log_warn "  - OPENROUTER_KEY: Your OpenRouter API key (optional)"
    log_warn "  - CORS_ALLOWED_ORIGIN: Your domain or VM public IP"
fi

log_info "✓ Environment configured"

# ============================================================================
# STEP 4: Build Docker Images
# ============================================================================

log_info "Step 4: Building Docker images..."

cd "$PROJECT_ROOT"

log_info "  Building Flask API..."
docker-compose build adrion-api

log_info "  Building UAP Orchestrator..."
docker-compose build adrion-uap

log_info "✓ Docker images built"

# ============================================================================
# STEP 5: Create Data Directories
# ============================================================================

log_info "Step 5: Creating data directories..."

mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/backups"
mkdir -p "$PROJECT_ROOT/monitoring/prometheus"
mkdir -p "$PROJECT_ROOT/monitoring/grafana/dashboards"
mkdir -p "$PROJECT_ROOT/monitoring/grafana/provisioning"
mkdir -p "$PROJECT_ROOT/monitoring/loki"
mkdir -p "$PROJECT_ROOT/monitoring/promtail"

chmod 755 "$PROJECT_ROOT/data"
chmod 755 "$PROJECT_ROOT/logs"
chmod 755 "$PROJECT_ROOT/backups"

log_info "✓ Data directories created"

# ============================================================================
# STEP 6: Start Services
# ============================================================================

log_info "Step 6: Starting services..."

cd "$PROJECT_ROOT"

# Validate .env DB_HOST is set
if grep -q "DB_HOST=localhost" .env; then
    log_error "⚠️  DB_HOST is still set to 'localhost'. Update .env with database VM IP before proceeding."
    log_error "   Edit .env and set: DB_HOST=<database-vm-private-ip>"
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Use oracle compose file if it exists, otherwise fall back to standard
if [ -f "docker-compose.oracle.yml" ]; then
    log_info "Using docker-compose.oracle.yml"
    docker-compose -f docker-compose.oracle.yml up -d
else
    log_warn "docker-compose.oracle.yml not found. Using docker-compose.yml"
    docker-compose up -d
fi

log_info "Waiting for services to be healthy (60 seconds)..."
sleep 60

# ============================================================================
# STEP 7: Verify Services
# ============================================================================

log_info "Step 7: Verifying services..."

HEALTHY=0
TOTAL=0

check_service() {
    local service=$1
    local port=$2
    local endpoint=$3

    TOTAL=$((TOTAL + 1))

    if curl -s -f "http://localhost:$port$endpoint" > /dev/null 2>&1; then
        log_info "  ✓ $service is healthy"
        HEALTHY=$((HEALTHY + 1))
    else
        log_warn "  ✗ $service is not responding yet (will retry)"
    fi
}

check_service "Flask API" 8003 "/api/arbitrage/status"
check_service "UAP Orchestrator" 8002 "/mapi/v1/health"
check_service "Prometheus" 9090 "/-/ready"
check_service "Grafana" 3000 "/api/health"

log_info "$HEALTHY/$TOTAL services are healthy"

if [ $HEALTHY -lt 2 ]; then
    log_warn "Some services are not healthy yet. Waiting 30 more seconds..."
    sleep 30
    docker-compose ps
fi

# ============================================================================
# STEP 8: Display Service URLs
# ============================================================================

log_info "Step 8: Service URLs"

PUBLIC_IP=$(hostname -I | awk '{print $1}')

cat << EOF

================================================================================
✅ ADRION 369 Deployment Complete
================================================================================

Public IP: $PUBLIC_IP

SERVICE URLS:
  Flask API (8003):          http://$PUBLIC_IP:8003/api/docs
  UAP Orchestrator (8002):   http://$PUBLIC_IP:8002/mapi/v1/health
  Prometheus (9090):         http://$PUBLIC_IP:9090 (ssh tunnel recommended)
  Grafana (3000):            http://$PUBLIC_IP:3000 (ssh tunnel recommended)

DEFAULT CREDENTIALS:
  Grafana Admin:  admin / $(grep GRAFANA_ADMIN_PASSWORD .env | cut -d= -f2)

SSH TUNNEL COMMANDS:
  Prometheus: ssh -i your-key.key -L 9090:localhost:9090 ubuntu@$PUBLIC_IP
  Grafana:    ssh -i your-key.key -L 3000:localhost:3000 ubuntu@$PUBLIC_IP

NEXT STEPS:
  1. Update .env with database VM IP (DB_HOST)
  2. Set up backup cron jobs (see ORACLE_CLOUD_DEPLOYMENT_GUIDE.md)
  3. Access Grafana dashboards via SSH tunnel
  4. Monitor logs: docker-compose logs -f

USEFUL COMMANDS:
  View logs:           docker-compose logs -f \<service\>
  Restart services:    docker-compose restart
  Stop all services:   docker-compose down
  Update ADRION code:  git pull && docker-compose build && docker-compose up -d

DOCUMENTATION:
  Full guide: docs/ORACLE_CLOUD_DEPLOYMENT_GUIDE.md
  Architecture: docs/ARCHITECTURE.md
  Troubleshooting: docs/CLOUD_DEPLOYMENT_RESEARCH.md

================================================================================
Cost: \$0/mo (Oracle Cloud Always-Free Tier)
Memory Usage: $(free -h | awk 'NR==2{print $3 "/" $2}')
Disk Usage: $(df -h / | awk 'NR==2{print $3 "/" $2}')
================================================================================

EOF

log_info "✓ Deployment complete"

# ============================================================================
# STEP 9: Optional - Create Backup Script
# ============================================================================

if command -v pg_isready &> /dev/null; then
    log_info "Step 9: Setting up backups (if PostgreSQL available)..."

    cat > "$PROJECT_ROOT/scripts/backup-oracle-db.sh" << 'BACKUP_SCRIPT'
#!/bin/bash
# Backup script for Oracle Cloud deployment
BACKUP_DIR="/home/ubuntu/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database if available
if docker ps | grep -q postgres; then
    docker exec adrion-postgres pg_dump -U adrion_user adrion_production | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
    echo "Backup created: $BACKUP_DIR/backup_$DATE.sql.gz"
else
    echo "PostgreSQL container not found"
fi

# Keep only last 30 backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
echo "Old backups cleaned up"
BACKUP_SCRIPT

    chmod +x "$PROJECT_ROOT/scripts/backup-oracle-db.sh"
    log_info "  Backup script created"
fi

exit 0
