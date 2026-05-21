param(
    [switch]$Strict,
    [string]$WorkspaceRoot = "$(Get-Location)"
)

$ErrorActionPreference = "Stop"
Set-Location $WorkspaceRoot

$failed = 0
$warnings = 0

function Assert-JsonFile {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        Write-Host "[FAIL] Missing file: $Path" -ForegroundColor Red
        $script:failed++
        return
    }

    try {
        Get-Content $Path -Raw | ConvertFrom-Json | Out-Null
        Write-Host "[OK] JSON valid: $Path" -ForegroundColor Green
    }
    catch {
        Write-Host "[FAIL] JSON invalid: $Path :: $($_.Exception.Message)" -ForegroundColor Red
        $script:failed++
    }
}

function Test-MissingWithWarning {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        Write-Host "[WARN] Missing optional file: $Path" -ForegroundColor Yellow
        $script:warnings++
    }
    else {
        Write-Host "[OK] Exists: $Path" -ForegroundColor Green
    }
}

Write-Host "== Copilot Workspace Validation =="

# 1) Parse critical JSON configs
Assert-JsonFile ".vscode/settings.json"
Assert-JsonFile ".vscode/tasks.json"
Assert-JsonFile ".roo/mcp.json"
Assert-JsonFile ".roo.json"
Assert-JsonFile "roo.profiles.json"
Assert-JsonFile "roo.rules.json"

# 2) Ensure .env template present
Test-MissingWithWarning ".env.template"

# 3) Check duplicate agent filenames in active sources only
$activeAgentSources = @(
    ".github",
    "config\\persona-agents"
)
$agentFiles = foreach ($source in $activeAgentSources) {
    if (Test-Path $source) {
        Get-ChildItem -Path $source -Recurse -File -Filter *.agent.md -ErrorAction SilentlyContinue
    }
}
$dups = $agentFiles | Group-Object Name | Where-Object { $_.Count -gt 1 }
if ($dups.Count -gt 0) {
    Write-Host "[WARN] Duplicate agent names found in active sources:" -ForegroundColor Yellow
    foreach ($dup in $dups) {
        Write-Host ("  - {0} x{1}" -f $dup.Name, $dup.Count) -ForegroundColor Yellow
    }
    $warnings++
}
else {
    Write-Host "[OK] No duplicate agent names" -ForegroundColor Green
}

# 4) Validate hooks config outside workspace
$hookJson = Join-Path $env:USERPROFILE ".agents\hooks\hooks.json"
if (Test-Path $hookJson) {
    try {
        $hook = Get-Content $hookJson -Raw | ConvertFrom-Json
        Write-Host "[OK] hooks.json parse valid" -ForegroundColor Green

        $windowsCmd = $hook.hooks.PostToolUse[0].windows
        if ($windowsCmd -and $windowsCmd -match "AZURE_MCP_COLLECT_TELEMETRY='false'") {
            Write-Host "[OK] PostToolUse telemetry default-off" -ForegroundColor Green
        }
        else {
            Write-Host "[WARN] PostToolUse telemetry default-off not detected" -ForegroundColor Yellow
            $warnings++
        }
    }
    catch {
        Write-Host "[FAIL] hooks.json invalid :: $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}
else {
    Write-Host "[WARN] hooks.json not found in user profile" -ForegroundColor Yellow
    $warnings++
}

Write-Host ""
Write-Host "Summary: FAIL=$failed WARN=$warnings"

if ($failed -gt 0) {
    exit 1
}

if ($Strict -and $warnings -gt 0) {
    exit 2
}

exit 0
