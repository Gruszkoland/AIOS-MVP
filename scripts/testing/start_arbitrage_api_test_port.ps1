param(
    [int]$Port = 8011
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$scriptPath = Join-Path $projectRoot "scripts\testing\start_arbitrage_api_test_port.py"

Push-Location $projectRoot
try {
    if (Test-Path $pythonExe) {
        & $pythonExe $scriptPath $Port
    }
    else {
        & python $scriptPath $Port
    }
}
finally {
    Pop-Location
}
