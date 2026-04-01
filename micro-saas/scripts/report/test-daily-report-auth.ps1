param(
    [string]$Endpoint = "http://127.0.0.1:3000/api/cron/daily-report",
    [string]$Token = ""
)

$ErrorActionPreference = "Stop"

function Get-TokenFromEnvLocal {
    $envFile = Join-Path $PSScriptRoot "..\..\.env.local"
    if (-not (Test-Path $envFile)) {
        return ""
    }

    $line = Get-Content $envFile | Where-Object { $_ -match '^DAILY_REPORT_TOKEN=' } | Select-Object -First 1
    if (-not $line) {
        return ""
    }

    $value = $line.Substring("DAILY_REPORT_TOKEN=".Length).Trim()
    if ($value -eq "" -or $value -eq "CHANGE_ME_LONG_RANDOM_TOKEN") {
        return ""
    }

    return $value
}

function Invoke-Endpoint {
    param(
        [string]$Url,
        [hashtable]$Headers = @{},
        [string]$Label
    )

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Method POST -Uri $Url -Headers $Headers
        [PSCustomObject]@{
            Test = $Label
            StatusCode = [int]$response.StatusCode
            Result = "ok"
        }
    }
    catch {
        $statusCode = 0
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }

        [PSCustomObject]@{
            Test = $Label
            StatusCode = $statusCode
            Result = "error"
        }
    }
}

if (-not $Token) {
    $Token = Get-TokenFromEnvLocal
}

Write-Host "Testing endpoint: $Endpoint"

$results = @()
$results += Invoke-Endpoint -Url $Endpoint -Label "No token"

if ($Token) {
    $safeLen = $Token.Length
    Write-Host "Token detected from parameter/env.local (length=$safeLen)."

    $results += Invoke-Endpoint -Url ("$Endpoint?token=$Token") -Label "Query token"
    $results += Invoke-Endpoint -Url $Endpoint -Headers @{ Authorization = "Bearer $Token" } -Label "Bearer token"
}
else {
    Write-Host "No valid token provided. Skipping token-authenticated tests."
}

$results | Format-Table -AutoSize

if ($Token) {
    $unauthorized = $results | Where-Object { $_.Test -eq "No token" -and $_.StatusCode -eq 401 }
    $authorized = $results | Where-Object { ($_.Test -eq "Query token" -or $_.Test -eq "Bearer token") -and $_.StatusCode -eq 200 }

    if ($unauthorized -and $authorized.Count -ge 1) {
        Write-Host "Auth behavior looks correct: unauthorized without token, authorized with token."
        exit 0
    }

    Write-Host "Auth behavior unexpected. Check endpoint logs and token configuration."
    exit 1
}

if (($results | Select-Object -First 1).StatusCode -eq 200) {
    Write-Host "Endpoint allows no-token access (DAILY_REPORT_TOKEN likely unset in runtime)."
    exit 0
}

Write-Host "Endpoint returned non-200 without token and no token available for authenticated test."
exit 1
