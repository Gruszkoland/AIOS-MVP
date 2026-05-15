#Requires -Version 5.1
#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Instaluje automatyczny sync jako zadanie Windows Task Scheduler.
    Sync uruchamia się co 30 minut oraz przy logowaniu.

.NOTES
    Uruchomienie (jako Administrator):
    .\Install-SyncTask.ps1

    Usunięcie zadania:
    Unregister-ScheduledTask -TaskName "ADRION-Sync-Dokumentacja" -Confirm:$false
#>

$TaskName  = "ADRION-Sync-Dokumentacja"
$ScriptPath = "C:\Users\adiha\.1_Projekty\Sync-Dokumentacja.ps1"
$User       = $env:USERNAME

# Weryfikacja
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Skrypt sync nie istnieje: $ScriptPath"
    exit 1
}

# Usuń stare zadanie jeśli istnieje
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "♻  Stare zadanie usunięte." -ForegroundColor Yellow
}

# Akcja — uruchom PowerShell ze skryptem
$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ScriptPath`" -Silent"

# Wyzwalacze: co 30 minut + przy logowaniu
$TriggerRepeat = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 30) -Once -At (Get-Date)
$TriggerLogon  = New-ScheduledTaskTrigger -AtLogOn -User $User

# Ustawienia zadania
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -DontStopIfGoingOnBatteries `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# Rejestracja
Register-ScheduledTask `
    -TaskName   $TaskName `
    -Action     $Action `
    -Trigger    @($TriggerRepeat, $TriggerLogon) `
    -Settings   $Settings `
    -RunLevel   Limited `
    -Force | Out-Null

Write-Host "✅ Zadanie '$TaskName' zainstalowane pomyślnie!" -ForegroundColor Green
Write-Host "   → Sync co 30 minut + przy każdym logowaniu" -ForegroundColor Cyan
Write-Host ""
Write-Host "Sprawdź: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor DarkGray
Write-Host "Uruchom ręcznie: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor DarkGray
Write-Host "Usuń: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor DarkGray
