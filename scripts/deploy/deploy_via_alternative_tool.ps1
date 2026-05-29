param(
    [ValidateSet("powershell")]
    [string]$Tool = "powershell",
    [int]$Port = 8011,
    [switch]$SkipLocalDeploy,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot

function Invoke-DeploymentStep {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Host "[DEPLOYMENT] START: $Name" -ForegroundColor Cyan

    if ($DryRun) {
        Write-Host "[DEPLOYMENT] DRY-RUN: $Name skipped" -ForegroundColor Yellow
        return
    }

    & $Action

    if ($LASTEXITCODE -ne 0) {
        throw "[DEPLOYMENT] FAILED: $Name (exit=$LASTEXITCODE)"
    }

    Write-Host "[DEPLOYMENT] OK: $Name" -ForegroundColor Green
}

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "ADRION Deployment Adapter (Alternative Tool)" -ForegroundColor Cyan
Write-Host "Tool: $Tool" -ForegroundColor Cyan
Write-Host "Root: $projectRoot" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

Invoke-DeploymentStep -Name "A11 predeploy validation" -Action {
    & "scripts\testing\invoke_a11_predeploy_validation.ps1" -Port $Port
}

Invoke-DeploymentStep -Name "Final deployment gate" -Action {
    & "scripts\security\run-final-deployment-gate.ps1" -Port $Port
}

if (-not $SkipLocalDeploy) {
    Invoke-DeploymentStep -Name "Local deployment" -Action {
        & "scripts\deploy-local.ps1"
    }
}

Invoke-DeploymentStep -Name "Deployment health check" -Action {
    if (Test-Path ".\.venv\Scripts\python.exe") {
        & ".\.venv\Scripts\python.exe" "scripts\deployment_health_check.py"
    }
    else {
        & "python" "scripts\deployment_health_check.py"
    }
}

Invoke-DeploymentStep -Name "KIMI health probe" -Action {
    if (Test-Path ".\.venv\Scripts\python.exe") {
        & ".\.venv\Scripts\python.exe" "scripts\testing\kimi_health_probe.py"
    }
    else {
        & "python" "scripts\testing\kimi_health_probe.py"
    }
}

Write-Host "[DEPLOYMENT] COMPLETED" -ForegroundColor Green