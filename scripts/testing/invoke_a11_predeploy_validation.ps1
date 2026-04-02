param(
    [int]$Port = 8011,
    [int]$StartupTimeoutSeconds = 10
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$starter = Join-Path $projectRoot "scripts\testing\start_arbitrage_api_test_port.ps1"
$runner = Join-Path $projectRoot "scripts\testing\run_a11_runtime_test.ps1"

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

Set-Location $projectRoot
$apiBase = "http://127.0.0.1:$Port"

if (-not (Test-QuantumEndpoint -BaseUrl $apiBase)) {
    throw "Quantum endpoint is not available on $apiBase. Start the dedicated API first: .\scripts\testing\start_arbitrage_api_test_port.ps1 -Port $Port"
}

& $runner -Port $Port
exit $LASTEXITCODE
