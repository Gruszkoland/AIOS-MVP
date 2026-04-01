param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

$gitCmd = $null

$gitFromPath = Get-Command git -ErrorAction SilentlyContinue
if ($gitFromPath) {
	$gitCmd = $gitFromPath.Source
}

if (-not $gitCmd) {
	$candidates = @(
		"$Env:ProgramFiles\Git\cmd\git.exe",
		"$Env:ProgramFiles\Git\bin\git.exe",
		"$Env:LocalAppData\Programs\Git\cmd\git.exe"
	)
	$gitCmd = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $gitCmd) {
	throw "Git executable not found. Install Git or add it to PATH, then rerun this script."
}

& $gitCmd config core.hooksPath .githooks
if ($LASTEXITCODE -ne 0) {
	throw "Failed to set core.hooksPath using '$gitCmd'"
}

$hooksPath = & $gitCmd config --get core.hooksPath
if ($LASTEXITCODE -ne 0 -or $hooksPath -ne '.githooks') {
	throw "hooksPath verification failed. Current value: '$hooksPath'"
}

Write-Host "Git hooks path set to .githooks"
Write-Host "Using git executable: $gitCmd"
Write-Host "Pre-commit hook is now active for this repository."
