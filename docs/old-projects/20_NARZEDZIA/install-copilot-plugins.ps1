# ╔════════════════════════════════════════════════════════════════╗
# ║  ADRION 369 — Copilot Plugins Installer (v1.0)               ║
# ║  Instalacja niezbędnych pluginów dla wszystkich projektów     ║
# ╚════════════════════════════════════════════════════════════════╝

$ErrorActionPreference = "Stop"

# Kolory dla konsoli
$colorCritical = 'Red'
$colorHigh = 'Yellow'
$colorSuccess = 'Green'
$colorInfo = 'Cyan'

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor $colorInfo
Write-Host "║           Instalacja Copilot Plugins — ADRION 369           ║" -ForegroundColor $colorInfo
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor $colorInfo

# Mapa pluginów VS Code
$extensionIds = @{
    # === CRITICAL ===
    "Python" = "ms-python.python"
    "Pylance" = "ms-python.pylance"
    "Black Formatter" = "ms-python.black-formatter"
    "Ruff" = "charliermarsh.ruff"
    "Go" = "golang.go"
    "Go Extended" = "ms-vscode.go"
    "Docker" = "ms-azuretools.vscode-docker"
    "PostgreSQL Client" = "cweijan.vscode-postgresql-client2"
    "Remote Containers" = "ms-vscode-remote.remote-containers"
    "PowerShell" = "ms-vscode.powershell"
    
    # === HIGH ===
    "Kubernetes" = "ms-kubernetes-tools.vscode-kubernetes-tools"
    "Terraform" = "hashicorp.terraform"
    "YAML Support" = "redhat.vscode-yaml"
    "Prettier" = "esbenp.prettier-vscode"
    "ESLint" = "dbaeumer.vscode-eslint"
    "Makefile Tools" = "ms-vscode.makefile-tools"
    "CMake Tools" = "ms-vscode.cmake-tools"
    "GitLens" = "eamodio.gitlens"
    "GitHub Theme" = "GitHub.github-vscode-theme"
    "Codespaces" = "GitHub.codespaces"
    
    # === ADRION Custom ===
    "ADRION 369 Extension" = "adrion.adrion-369-extension"
    "n8n Architect" = "adrion.n8n-architect"
    "MCP Protocol Server" = "adrion.mcp-protocol-server"
    "Guardian Laws Compliance" = "adrion.guardian-laws-compliance"
    "EBDI Framework" = "adrion.ebdi-framework"
    "Vortex Orchestrator" = "adrion.vortex-orchestrator"
    "Grafana Dashboard" = "grafana.grafana"
    "OpenShift Connector" = "redhat.vscode-openshift-connector"
}

$critical = @("Python", "Pylance", "Black Formatter", "Ruff", "Go", "Go Extended", "Docker", "PostgreSQL Client", "Remote Containers", "PowerShell")
$high = @("Kubernetes", "Terraform", "YAML Support", "Prettier", "ESLint", "Makefile Tools", "GitLens", "GitHub Theme")

# Funkcja do instalacji extension'u
function Install-Extension {
    param(
        [string]$extensionId,
        [string]$displayName,
        [string]$priority = "medium"
    )
    
    $color = switch ($priority) {
        "critical" { $colorCritical }
        "high" { $colorHigh }
        default { $colorInfo }
    }
    
    Write-Host "[INSTALL] $displayName ($extensionId)" -ForegroundColor $color
    
    # Spróbuj zainstalować extension
    try {
        & code --install-extension $extensionId --force 2>&1 | Out-Null
        Write-Host "  ✓ Zainstalowano pomyślnie" -ForegroundColor $colorSuccess
        return $true
    }
    catch {
        Write-Host "  ✗ Błąd instalacji: $_" -ForegroundColor $colorCritical
        return $false
    }
}

# Liczniki
$installed = 0
$failed = 0
$skipped = 0

# === CRITICAL EXTENSIONS ===
Write-Host "`n▶ Instalacja CRITICAL pluginów (OBOWIĄZKOWE):`n" -ForegroundColor $colorCritical

foreach ($name in $critical) {
    $extId = $extensionIds[$name]
    if (Install-Extension -extensionId $extId -displayName $name -priority "critical") {
        $installed++
    } else {
        $failed++
    }
    Start-Sleep -Milliseconds 500
}

# === HIGH PRIORITY EXTENSIONS ===
Write-Host "`n▶ Instalacja HIGH PRIORITY pluginów:`n" -ForegroundColor $colorHigh

foreach ($name in $high) {
    $extId = $extensionIds[$name]
    if (Install-Extension -extensionId $extId -displayName $name -priority "high") {
        $installed++
    } else {
        $failed++
    }
    Start-Sleep -Milliseconds 500
}

# === ADRION CUSTOM EXTENSIONS ===
Write-Host "`n▶ Instalacja ADRION Custom pluginów:`n" -ForegroundColor $colorInfo

$adrionExtensions = @("ADRION 369 Extension", "n8n Architect", "MCP Protocol Server", "Guardian Laws Compliance", "EBDI Framework", "Vortex Orchestrator", "Grafana Dashboard", "OpenShift Connector")

foreach ($name in $adrionExtensions) {
    $extId = $extensionIds[$name]
    if (Install-Extension -extensionId $extId -displayName $name -priority "high") {
        $installed++
    } else {
        $skipped++  # Custom extensions mogą nie być dostępne, to OK
        Write-Host "  ⓘ Custom extension niedostępny — zainstaluj ręcznie w Marketplace" -ForegroundColor $colorInfo
    }
    Start-Sleep -Milliseconds 500
}

# === PODSUMOWANIE ===
Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor $colorSuccess
Write-Host "║                    PODSUMOWANIE INSTALACJI                    ║" -ForegroundColor $colorSuccess
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor $colorSuccess

Write-Host "`n✓ Zainstalowano:      $installed pluginów" -ForegroundColor $colorSuccess
Write-Host "✗ Błędy:              $failed pluginów" -ForegroundColor $colorCritical
Write-Host "ⓘ Niedostępne/Custom: $skipped pluginów" -ForegroundColor $colorHigh

if ($failed -eq 0) {
    Write-Host "`n✓ SUKCES: Wszystkie dostępne pluginy zostały zainstalowane!" -ForegroundColor $colorSuccess
    Write-Host "`nKroki następne:" -ForegroundColor $colorInfo
    Write-Host "  1. Przeładuj VS Code (Ctrl+Shift+P → Developer: Reload Window)" -ForegroundColor $colorInfo
    Write-Host "  2. Sprawdź pluginy: Extensions (Ctrl+Shift+X)" -ForegroundColor $colorInfo
    Write-Host "  3. Skonfiguruj każdy plugin wg potrzeb" -ForegroundColor $colorInfo
} else {
    Write-Host "`n⚠ UWAGA: Niektóre pluginy nie zostały zainstalowane!" -ForegroundColor $colorCritical
    Write-Host "  Spróbuj zainstalować ręcznie poprzez Marketplace (Ctrl+Shift+X)" -ForegroundColor $colorCritical
}

Write-Host "`nLokalizacja konfiguracji:" -ForegroundColor $colorInfo
Write-Host "  • Extensions list: .vscode/extensions.json" -ForegroundColor $colorInfo
Write-Host "  • Settings:        .vscode/settings.json" -ForegroundColor $colorInfo

Write-Host "`n"
