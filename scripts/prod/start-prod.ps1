param(
    [int]$Port = 9100
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

$runtimeDir = Join-Path $root '.runtime'
if (-not (Test-Path $runtimeDir)) {
    New-Item -ItemType Directory -Path $runtimeDir | Out-Null
}

$pythonExe = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $pythonExe)) {
    $pythonExe = 'python'
}

$pidFile = Join-Path $runtimeDir 'waitress.pid'
$logFile = Join-Path $runtimeDir 'waitress.log'
$errFile = Join-Path $runtimeDir 'waitress.err.log'

# Stop previous managed process if present.
if (Test-Path $pidFile) {
    try {
        $oldPid = Get-Content $pidFile | Select-Object -First 1
        if ($oldPid) {
            Stop-Process -Id ([int]$oldPid) -Force -ErrorAction SilentlyContinue
        }
    } catch {}
    Remove-Item $pidFile -ErrorAction SilentlyContinue
}

$waitressArgs = @('-m', 'waitress', "--listen=0.0.0.0:$Port", 'wsgi:app')
$proc = Start-Process -FilePath $pythonExe -ArgumentList $waitressArgs -WorkingDirectory $root -RedirectStandardOutput $logFile -RedirectStandardError $errFile -NoNewWindow -PassThru
$proc.Id | Out-File -FilePath $pidFile -Encoding ascii -NoNewline

Start-Sleep -Seconds 2

try {
    $status = & $pythonExe -c "import urllib.request, json; d=json.loads(urllib.request.urlopen('http://127.0.0.1:$Port/api/arbitrage/status', timeout=5).read().decode()); print(d.get('status','unknown'))"
    Write-Host "STARTED pid=$($proc.Id) port=$Port status=$status"
} catch {
    Write-Host "STARTED pid=$($proc.Id) port=$Port but healthcheck failed. See .runtime/waitress.log"
}
