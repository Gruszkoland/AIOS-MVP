param(
    [int]$Port = 8011,
    [int]$StartupTimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot

function Test-QuantumEndpoint {
    param([string]$BaseUrl)

    try {
        $resp = Invoke-WebRequest -Uri "$BaseUrl/api/arbitrage/quantum/decide" -Method POST -ContentType "application/json" -Body '{"price_source":100,"price_target":120,"channel_id":"AUDIO_PREMIUM"}' -UseBasicParsing -TimeoutSec 3
        return @((200), (400), (429)) -contains [int]$resp.StatusCode
    }
    catch {
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $status = [int]$_.Exception.Response.StatusCode
            return @((200), (400), (429)) -contains $status
        }
        return $false
    }
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Host "GATE_STEP_START=$Name"
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "GATE_STEP_FAILED=$Name exit=$LASTEXITCODE"
    }
    Write-Host "GATE_STEP_OK=$Name"
}

Invoke-Step -Name "validate_session_reports" -Action {
    & ".\.venv\Scripts\python.exe" "scripts\reporting\validate_session_reports.py"
}

Invoke-Step -Name "check_llm_kpi_gate_warmup" -Action {
    & ".\.venv\Scripts\python.exe" "scripts\reporting\check_llm_kpi_gate.py" "--window" "200" "--min-events" "30" "--rollback-on-fail" "--warmup-ok" "--max-age-days" "7"
}

Invoke-Step -Name "validate_powershell_tasks" -Action {
    & ".\.venv\Scripts\python.exe" "scripts\reporting\validate_powershell_tasks.py"
}

$apiProc = $null
$apiBase = "http://127.0.0.1:$Port"

try {
    $stdoutPath = Join-Path $projectRoot "_precommit_a11_api_stdout.log"
    $stderrPath = Join-Path $projectRoot "_precommit_a11_api_stderr.log"

    $apiProc = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "scripts/testing/start_arbitrage_api_test_port.py", "$Port" -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath

    $deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
        if (Test-QuantumEndpoint -BaseUrl $apiBase) {
            $ready = $true
            break
        }
        Start-Sleep -Milliseconds 500
    }

    if (-not $ready) {
        throw "A11 API not ready on $apiBase within ${StartupTimeoutSeconds}s"
    }

    Invoke-Step -Name "a11_predeploy_validation" -Action {
        & "scripts\testing\invoke_a11_predeploy_validation.ps1" -Port $Port
    }
}
finally {
    if ($apiProc -and -not $apiProc.HasExited) {
        Stop-Process -Id $apiProc.Id -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "FINAL_DEPLOYMENT_GATE=PASS"
