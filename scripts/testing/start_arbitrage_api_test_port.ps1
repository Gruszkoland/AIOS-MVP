param(
    [int]$Port = 8011
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot

& ".\.venv\Scripts\python.exe" "scripts\testing\start_arbitrage_api_test_port.py" $Port
