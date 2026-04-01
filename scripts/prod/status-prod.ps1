param(
    [int]$Port = 9100
)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonExe = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $pythonExe)) {
    $pythonExe = 'python'
}

Write-Host "=== Port status ($Port) ==="
netstat -ano | findstr /R ":$Port"

Write-Host "`n=== API healthcheck ==="
try {
    & $pythonExe -c "import urllib.request, json; d=json.loads(urllib.request.urlopen('http://127.0.0.1:$Port/api/arbitrage/status', timeout=5).read().decode()); print(json.dumps(d, ensure_ascii=True))"
} catch {
    Write-Host "Healthcheck failed: $($_.Exception.Message)"
}
