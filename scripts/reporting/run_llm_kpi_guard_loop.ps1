param(
    [double]$IntervalMinutes = 15,
    [int]$Window = 200,
    [int]$MinEvents = 30,
    [switch]$RollbackOnFail,
    [switch]$WarmupOk,
    [switch]$PromoteOnPass,
    [double]$PromotePercent = 5,
    [string]$PromoteBackend = "openrouter",
    [switch]$AlertOnReady,
    [string]$AlertPath = "monitoring/llm_rollout_alert.json",
    [int]$MaxIterations = 0
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
$checker = Join-Path $root "scripts\reporting\check_llm_kpi_gate.py"

if (!(Test-Path $python)) {
    Write-Host "[KPI-GUARD] Python env not found at $python"
    exit 1
}
if (!(Test-Path $checker)) {
    Write-Host "[KPI-GUARD] Checker not found at $checker"
    exit 1
}

if ($IntervalMinutes -lt 0.1) {
    $IntervalMinutes = 0.1
}

$iter = 0
while ($true) {
    $iter += 1
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[KPI-GUARD][$ts] Iteration $iter starting..."

    $checkerArgs = @($checker, "--window", "$Window", "--min-events", "$MinEvents")
    if ($RollbackOnFail) {
        $checkerArgs += "--rollback-on-fail"
    }
    if ($WarmupOk) {
        $checkerArgs += "--warmup-ok"
    }
    if ($PromoteOnPass) {
        $checkerArgs += "--promote-on-pass"
        $checkerArgs += "--promote-percent"
        $checkerArgs += "$PromotePercent"
        $checkerArgs += "--promote-backend"
        $checkerArgs += "$PromoteBackend"
    }
    if ($AlertOnReady) {
        $checkerArgs += "--alert-on-ready"
        $checkerArgs += "--alert-path"
        $checkerArgs += "$AlertPath"
    }

    & $python @checkerArgs
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "[KPI-GUARD] PASS"
    } elseif ($exitCode -eq 2) {
        Write-Host "[KPI-GUARD] PENDING"
    } else {
        Write-Host "[KPI-GUARD] FAIL (exit=$exitCode)"
    }

    if ($MaxIterations -gt 0 -and $iter -ge $MaxIterations) {
        Write-Host "[KPI-GUARD] Completed $iter iteration(s). Exiting."
        exit 0
    }

    $sleepSeconds = [int][Math]::Round($IntervalMinutes * 60)
    if ($sleepSeconds -lt 1) {
        $sleepSeconds = 1
    }
    Start-Sleep -Seconds $sleepSeconds
}
