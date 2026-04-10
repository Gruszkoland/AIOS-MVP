#!/bin/bash

# ADRION 369 — OpenRouter Setup Verification
# ============================================

echo "✅ ADRION 369 — OpenRouter Setup Verification"
echo "=============================================="
echo ""

RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

PASS_COUNT=0
FAIL_COUNT=0

check_file() {
    if [ -f "\" ]; then
        echo -e "\✅\ \"
        ((PASS_COUNT++))
    else
        echo -e "\❌\ \"
        ((FAIL_COUNT++))
    fi
}

check_port() {
    if command -v netstat &> /dev/null; then
        if netstat -tuln 2>/dev/null | grep -q ":\"; then
            echo -e "\✅\ Port \ is listening"
            ((PASS_COUNT++))
        else
            echo -e "\⚠️\ Port \ not listening"
        fi
    fi
}

echo "Checking configuration files..."
check_file "../../.env"
check_file "../../3_config/openrouter/models.json"
check_file "../../6_docker/docker-compose.cloud.yml"

echo ""
echo "Checking service status..."
check_port "8001"
check_port "3000"

echo ""
echo "======================================"
echo -e "Results: \\ passed\, \\ failed\"
echo "======================================"
