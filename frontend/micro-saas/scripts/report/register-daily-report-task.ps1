param(
    [string]$Endpoint = "http://127.0.0.1:3000/api/cron/daily-report",
    [string]$Token = "",
    [string]$TaskName = "MicroSaaS-DailyReport-0900"
)

$ErrorActionPreference = "Stop"

$psScript = if ($Token) {
    "`$headers = @{ Authorization = 'Bearer $Token' }; Invoke-WebRequest -UseBasicParsing -Method POST -Uri '$Endpoint' -Headers `$headers | Out-Null"
} else {
    "Invoke-WebRequest -UseBasicParsing -Method POST -Uri '$Endpoint' | Out-Null"
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -Command $psScript"
$trigger = New-ScheduledTaskTrigger -Daily -At 09:00

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Description "Daily Micro SaaS KPI report at 09:00" -Force | Out-Null

Write-Host "Scheduled task created/updated: $TaskName at 09:00"
