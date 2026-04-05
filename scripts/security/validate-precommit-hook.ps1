param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")),
    [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

function Resolve-ShPath {
    $candidates = @(
        "$Env:ProgramFiles\Git\bin\sh.exe",
        "$Env:ProgramFiles\Git\usr\bin\sh.exe",
        "$Env:LocalAppData\Programs\Git\bin\sh.exe",
        "$Env:LocalAppData\Programs\Git\usr\bin\sh.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Nie znaleziono sh.exe (Git Bash). Zainstaluj Git for Windows lub popraw sciezke."
}

function Invoke-HookProbe {
    param(
        [string]$Label,
        [string]$FileName,
        [string]$Content,
        [int]$ExpectedExit,
        [string]$ShPath,
        [string]$HookPath
    )

    $tempIndex = [System.IO.Path]::GetTempFileName()
    $oldIndex = $env:GIT_INDEX_FILE
    $oldSkipFinalGate = $env:ADRION_SKIP_FINAL_GATE

    try {
        Set-Content -Path $FileName -Value $Content -Encoding UTF8

        $env:GIT_INDEX_FILE = $tempIndex
        $env:ADRION_SKIP_FINAL_GATE = "1"
        git read-tree HEAD | Out-Null
        git add -- $FileName | Out-Null

        & $ShPath $HookPath
        $actualExit = $LASTEXITCODE

        if ($VerboseOutput) {
            Write-Host "[$Label] expected=$ExpectedExit actual=$actualExit"
        }

        if ($actualExit -ne $ExpectedExit) {
            throw "Probe '$Label' failed. Expected exit $ExpectedExit, got $actualExit."
        }
    }
    finally {
        if ($null -ne $oldIndex) {
            $env:GIT_INDEX_FILE = $oldIndex
        }
        else {
            Remove-Item Env:GIT_INDEX_FILE -ErrorAction SilentlyContinue
        }

        if ($null -ne $oldSkipFinalGate) {
            $env:ADRION_SKIP_FINAL_GATE = $oldSkipFinalGate
        }
        else {
            Remove-Item Env:ADRION_SKIP_FINAL_GATE -ErrorAction SilentlyContinue
        }

        Remove-Item -Path $tempIndex -Force -ErrorAction SilentlyContinue
        Remove-Item -Path $FileName -Force -ErrorAction SilentlyContinue
    }
}

$shPath = Resolve-ShPath
$hookPath = Join-Path $RepoRoot ".githooks\pre-commit"

if (-not (Test-Path $hookPath)) {
    throw "Nie znaleziono hooka: $hookPath"
}

Invoke-HookProbe -Label "placeholder" -FileName ".hook_probe_placeholder.txt" -Content "STRIPE_SECRET_KEY=STRIPE_SECRET_KEY_PLACEHOLDER" -ExpectedExit 0 -ShPath $shPath -HookPath $hookPath
Invoke-HookProbe -Label "secret" -FileName ".hook_probe_secret.txt" -Content "STRIPE_SECRET_KEY=sk_live_ABCDEFGHIJKLMNOPQRSTUV123456" -ExpectedExit 1 -ShPath $shPath -HookPath $hookPath

Write-Host "HOOK_VALIDATION=PASS"
