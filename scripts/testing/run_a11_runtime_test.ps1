param(
	[int]$Port = 8011
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

Push-Location $projectRoot
try {
	$env:ARBITRAGE_API_BASE = "http://127.0.0.1:$Port"

	if (Test-Path $pythonExe) {
		& $pythonExe -m pytest tests/test_runtime_connectors.py -m runtime -k "ArbitrageApiRuntime" -v --tb=short
	}
	else {
		& python -m pytest tests/test_runtime_connectors.py -m runtime -k "ArbitrageApiRuntime" -v --tb=short
	}

	exit $LASTEXITCODE
}
finally {
	Pop-Location
}
