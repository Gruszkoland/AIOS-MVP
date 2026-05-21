param(
    [double]$IntervalMinutes = 30,
    [int]$MaxIterations = 0,
    [switch]$EmailOnFail,
    [switch]$EmailOnEveryRun,
    [string]$WorkspaceRoot = "$(Get-Location)"
)

$ErrorActionPreference = "Continue"
Set-Location $WorkspaceRoot

function Invoke-HealthCycle {
    param([int]$Iteration)

    Write-Host "[HEALTH] Iteration $Iteration started at $(Get-Date -Format s)"

    powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/reporting/validate_copilot_workspace.ps1"
    $validationExit = $LASTEXITCODE

    if (Test-Path ".venv\Scripts\python.exe") {
        & ".\.venv\Scripts\python.exe" "scripts/reporting/generate_copilot_stability_report.py"
        $stabilityExit = $LASTEXITCODE

        & ".\.venv\Scripts\python.exe" "scripts/reporting/generate_tooling_recommendations.py"
        $recommendExit = $LASTEXITCODE
    }
    else {
        python "scripts/reporting/generate_copilot_stability_report.py"
        $stabilityExit = $LASTEXITCODE

        python "scripts/reporting/generate_tooling_recommendations.py"
        $recommendExit = $LASTEXITCODE
    }

    $failed = @()
    if ($validationExit -ne 0) { $failed += "validation:$validationExit" }
    if ($stabilityExit -ne 0) { $failed += "stability:$stabilityExit" }
    if ($recommendExit -ne 0) { $failed += "recommendations:$recommendExit" }

    $status = if ($failed.Count -eq 0) { "OK" } else { "FAILED" }
    Write-Host "[HEALTH] Iteration $Iteration status: $status"

    $shouldEmail = $false
    if ($EmailOnEveryRun) { $shouldEmail = $true }
    if ($EmailOnFail -and $status -eq "FAILED") { $shouldEmail = $true }

    if ($shouldEmail) {
        $subject = "ADRION | VS Code Health | $status | Iteration $Iteration"
        powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/reporting/send_copilot_health_email.ps1" -WorkspaceRoot $WorkspaceRoot -Subject $subject -AttachAllReports
    }

    return @{ Status = $status; Errors = $failed }
}

$iteration = 0
while ($true) {
    $iteration++
    $result = Invoke-HealthCycle -Iteration $iteration

    if ($MaxIterations -gt 0 -and $iteration -ge $MaxIterations) {
        Write-Host "[HEALTH] MaxIterations reached. Exiting."
        break
    }

    Start-Sleep -Seconds ([int]([Math]::Max(6, $IntervalMinutes * 60)))
}
