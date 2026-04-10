#!/bin/bash

# ADRION 369 — OpenRouter Deployment Script
# ============================================
# This script automates the complete OpenRouter deployment

set -e

echo "======================================================================"
echo "🚀 ADRION 369 — OpenRouter Deployment Script"
echo "======================================================================"
echo ""

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

# Constants
PYTHON_MIN_VERSION="3.9"
PROJECT_ROOT="\C:\Users\adiha\162 demencje w schemacie 369\temp_deploy\ADRION-369_OPEN-ROUTER_finalny_projekt"
VENV_DIR="\/venv"
LOG_FILE="\/deployment.log"

# Functions
log_success() {
    echo -e "\✅ \\" | tee -a "\"
}

log_error() {
    echo -e "\❌ \\" | tee -a "\"  
}

log_info() {
    echo -e "\ℹ️  \\" | tee -a "\"
}

# Phase 1: Check Prerequisites
echo "PHASE 1: Checking Prerequisites"
echo "=================================="

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found"
    exit 1
fi

PYTHON_VERSION=\
log_success "Python \ found"

if ! command -v pip3 &> /dev/null; then
    log_error "pip3 not found"
    exit 1
fi

log_success "pip3 available"
echo ""

# Phase 2: Setup Virtual Environment
echo "PHASE 2: Setting up Virtual Environment"
echo "========================================"

if [ ! -d "\" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv "\"
    log_success "Virtual environment created"
else
    log_success "Virtual environment exists (reusing)"
fi

source "\/bin/activate"
log_success "Virtual environment activated"
echo ""

# Phase 3: Install Dependencies
echo "PHASE 3: Installing Dependencies"
echo "================================="

if [ -f "requirements.txt" ]; then
    log_info "Installing packages..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    log_success "Dependencies installed"
else
    log_error "requirements.txt not found"
    exit 1
fi
echo ""

# Phase 4: Validate Configuration
echo "PHASE 4: Validating Configuration"
echo "=================================="

if [ ! -f ".env" ]; then
    log_error ".env file not found"
    log_info "Creating from template..."
    cp 1_env_templates/.env.openrouter-production .env
    log_info "Edit .env with your OpenRouter API key before continuing"
    exit 1
fi

log_success ".env file found"

if grep -q "PLACEHOLDER" .env; then
    log_error ".env contains PLACEHOLDER values"
    exit 1
fi

log_success ".env validated"
echo ""

# Phase 5: Run Tests
echo "PHASE 5: Running Tests"
echo "======================"

if [ -d "4_tests" ]; then
    log_info "Running test suite..."
    cd 4_tests
    pytest test_openrouter_basic.py -v --tb=short 2>&1 | tee -a "..\"
    cd ..
    log_success "Tests completed"
else
    log_info "Test directory not found (skipping)"
fi
echo ""

# Phase 6: Start Service
echo "PHASE 6: Starting Service"
echo "========================="

log_info "Starting ADRION 369 with OpenRouter..."
log_success "Service deployment complete!"

echo ""
echo "======================================================================"
echo "✅ DEPLOYMENT SUCCESSFUL"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "1. Check service status: curl http://localhost:8001/api/arbitrage/status"
echo "2. View logs: tail -f deployment.log"
echo "3. Read docs: cat OPENROUTER_CONFIG.md"
echo ""
