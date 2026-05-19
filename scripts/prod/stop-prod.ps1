param(
    [int]$Port = 9100
)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pidFile = Join-Path $root '.runtime\waitress.pid'

$stopped = $false
if (Test-Path $pidFile) {
    try {
        $managedPid = Get-Content $pidFile | Select-Object -First 1
        if ($managedPid) {
            Stop-Process -Id ([int]$managedPid) -Force -ErrorAction SilentlyContinue
            Write-Host "STOPPED managed pid=$managedPid"
            $stopped = $true
        }
    } catch {}
    Remove-Item $pidFile -ErrorAction SilentlyContinue
}

# Fallback: kill listeners on requested port.
$lines = netstat -ano | findstr /R ":$Port"
if ($lines) {
    $pids = @()
    foreach ($line in $lines) {
        $cols = ($line -split '\s+') | Where-Object { $_ -ne '' }
        if ($cols.Count -ge 5) {
            $candidate = $cols[$cols.Count - 1]
            if ($candidate -match '^[0-9]+$') { $pids += [int]$candidate }
        }
    }
    $pids = $pids | Select-Object -Unique
    foreach ($listenerPid in $pids) {
        Stop-Process -Id $listenerPid -Force -ErrorAction SilentlyContinue
        Write-Host "STOPPED port=$Port pid=$listenerPid"
        $stopped = $true
    }
}

if (-not $stopped) {
    Write-Host "Nothing to stop on port $Port"
}
