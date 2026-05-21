#!/bin/bash
# === ADRION 369 Copilot Plugins Installer (Bash/Cross-platform) ===

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           Instalacja Copilot Plugins — ADRION 369           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Liczniki
INSTALLED=0
FAILED=0
SKIPPED=0
TOTAL=42

# Funkcja do instalacji extension'u
install_extension() {
    local ext=$1
    local count=$2
    
    echo "[$count/$TOTAL] $ext"
    
    if command -v code &> /dev/null; then
        if code --install-extension "$ext" --force &> /dev/null; then
            echo "  ✓ OK"
            INSTALLED=$((INSTALLED + 1))
        else
            echo "  ✗ FAILED"
            FAILED=$((FAILED + 1))
        fi
    else
        echo "  ⚠ VS Code CLI not found"
        SKIPPED=$((SKIPPED + 1))
    fi
}

# Arrays of extensions
CRITICAL=(
    "ms-python.python"
    "ms-python.pylance"
    "ms-python.black-formatter"
    "charliermarsh.ruff"
    "golang.go"
    "ms-vscode.go"
    "ms-azuretools.vscode-docker"
    "cweijan.vscode-postgresql-client2"
    "ms-vscode-remote.remote-containers"
    "ms-vscode.powershell"
)

HIGH_PRIORITY=(
    "ms-kubernetes-tools.vscode-kubernetes-tools"
    "hashicorp.terraform"
    "redhat.vscode-yaml"
    "esbenp.prettier-vscode"
    "dbaeumer.vscode-eslint"
    "ms-vscode.makefile-tools"
    "ms-vscode.cmake-tools"
    "eamodio.gitlens"
    "GitHub.github-vscode-theme"
)

UTILITIES=(
    "GitHub.codespaces"
    "2gua.rainbow-brackets"
    "ms-python.debugpy"
    "ms-azuretools.vscode-containers"
    "ms-vscode.remote-repositories"
    "redhat.vscode-commons"
    "ms-azuretools.vscode-bicep"
    "ms-azuretools.vscode-postgres"
    "GitHub.copilot-chat"
    "grafana.grafana"
    "redhat.vscode-openshift-connector"
)

CUSTOM=(
    "adrion.adrion-369-extension"
    "adrion.n8n-architect"
    "adrion.mcp-protocol-server"
    "adrion.guardian-laws-compliance"
    "adrion.ebdi-framework"
    "adrion.vortex-orchestrator"
)

# Install CRITICAL
echo "[CRITICAL - Must Install]"
count=1
for ext in "${CRITICAL[@]}"; do
    install_extension "$ext" "$count"
    count=$((count + 1))
done

# Install HIGH PRIORITY
echo ""
echo "[HIGH PRIORITY]"
for ext in "${HIGH_PRIORITY[@]}"; do
    install_extension "$ext" "$count"
    count=$((count + 1))
done

# Install UTILITIES
echo ""
echo "[UTILITIES]"
for ext in "${UTILITIES[@]}"; do
    install_extension "$ext" "$count"
    count=$((count + 1))
done

# Install CUSTOM
echo ""
echo "[ADRION CUSTOM]"
for ext in "${CUSTOM[@]}"; do
    install_extension "$ext" "$count"
    count=$((count + 1))
done

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    PODSUMOWANIE INSTALACJI                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "✓ Zainstalowano:        $INSTALLED extensions"
echo "✗ Błędy:                $FAILED extensions"
echo "⚠ Niedostępne/Custom:   $SKIPPED extensions"
echo ""

if [ $INSTALLED -gt 0 ]; then
    echo "✅ SUKCES: Zainstalowano $INSTALLED/$TOTAL extensions!"
    echo ""
    echo "Następne kroki:"
    echo "  1. Przeładuj VS Code: Ctrl+Shift+P → 'Developer: Reload Window'"
    echo "  2. Sprawdź Extensions: Ctrl+Shift+X"
    echo "  3. Wpisz w Copilot: /mcp — aby aktywować MCP servers"
else
    echo "⚠ UWAGA: Brak zainstalowanych extensions!"
    echo "  Sprawdź czy VS Code jest zainstalowany i dostępny w PATH"
fi

echo ""
