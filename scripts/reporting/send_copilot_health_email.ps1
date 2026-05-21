param(
    [string]$WorkspaceRoot = "$(Get-Location)",
    [string]$To = $env:REPORT_EMAIL_TO,
    [string]$Subject = "ADRION | Raport zdrowia przestrzeni VS Code",
    [switch]$AttachAllReports
)

$ErrorActionPreference = "Stop"
Set-Location $WorkspaceRoot

function Get-EnvOrThrow {
    param([string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name)
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "Brak zmiennej środowiskowej: $Name"
    }
    return $value
}

try {
    $smtpHost = Get-EnvOrThrow "SMTP_HOST"
    $smtpPort = [int](Get-EnvOrThrow "SMTP_PORT")
    $smtpUser = Get-EnvOrThrow "SMTP_USERNAME"
    $smtpPass = Get-EnvOrThrow "SMTP_PASSWORD"
    $from = Get-EnvOrThrow "REPORT_EMAIL_FROM"

    if ([string]::IsNullOrWhiteSpace($To)) {
        throw "Brak adresata raportu. Ustaw REPORT_EMAIL_TO albo podaj -To"
    }

    $useSslRaw = [Environment]::GetEnvironmentVariable("SMTP_USE_SSL")
    $useSsl = $true
    if (-not [string]::IsNullOrWhiteSpace($useSslRaw)) {
        $useSsl = $useSslRaw -in @("1", "true", "True", "TRUE")
    }

    $reportDir = Join-Path $WorkspaceRoot "reports"
    $stability = Join-Path $reportDir "copilot_stability_report.json"
    $kpiFinal = Get-ChildItem -Path $reportDir -Filter "copilot_reorg_kpi_final_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if (-not (Test-Path $stability)) {
        throw "Brak raportu: $stability"
    }

    $stabilityData = Get-Content $stability -Raw | ConvertFrom-Json

    $bodyLines = @(
        "Automatyczny raport zdrowia przestrzeni VS Code został wygenerowany.",
        "",
        "Workspace: $($stabilityData.workspace)",
        "Timestamp: $($stabilityData.timestamp)",
        "MCP enabled: $($stabilityData.checks.mcp_servers_enabled)",
        "Tasks count: $($stabilityData.checks.task_count)",
        "",
        "Załączniki zawierają pełne szczegóły."
    )

    $message = New-Object System.Net.Mail.MailMessage
    $message.From = $from
    $message.To.Add($To)
    $message.Subject = $Subject
    $message.Body = ($bodyLines -join [Environment]::NewLine)
    $message.IsBodyHtml = $false

    $message.Attachments.Add($stability) | Out-Null

    if ($kpiFinal) {
        $message.Attachments.Add($kpiFinal.FullName) | Out-Null
    }

    if ($AttachAllReports) {
        Get-ChildItem -Path $reportDir -Filter "copilot_*.json" -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.FullName -ne $stability -and (-not $kpiFinal -or $_.FullName -ne $kpiFinal.FullName)) {
                $message.Attachments.Add($_.FullName) | Out-Null
            }
        }
    }

    $client = New-Object System.Net.Mail.SmtpClient($smtpHost, $smtpPort)
    $client.EnableSsl = $useSsl
    $client.Credentials = New-Object System.Net.NetworkCredential($smtpUser, $smtpPass)
    $client.Send($message)

    Write-Host "EMAIL_SENT to $To via ${smtpHost}:$smtpPort" -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "EMAIL_SEND_FAILED :: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
