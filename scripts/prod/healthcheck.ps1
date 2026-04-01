param(
    [int]$Port = 9100
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonExe = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $pythonExe)) {
    $pythonExe = 'python'
}

& $pythonExe -c "import urllib.request, json, sys; d=json.loads(urllib.request.urlopen('http://127.0.0.1:$Port/api/arbitrage/status', timeout=5).read().decode()); ok = (d.get('status') == 'online'); print(json.dumps(d, ensure_ascii=True)); sys.exit(0 if ok else 2)"
