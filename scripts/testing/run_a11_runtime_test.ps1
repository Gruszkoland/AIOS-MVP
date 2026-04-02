param(
	[int]$Port = 8011
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot

$env:ARBITRAGE_API_BASE = "http://127.0.0.1:$Port"

& ".\.venv\Scripts\python.exe" -m pytest tests/test_runtime_connectors.py -m runtime -k "ArbitrageApiRuntime" -v --tb=short
exit $LASTEXITCODE
