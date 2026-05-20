# Rejestruje Windows Scheduled Task: sync dokumentacji co godzine
$taskName = "SyncDokumentacjaADRION"
$scriptPath = "C:\Users\adiha\sync-dokumentacja.ps1"

# Usun stare zadanie jesli istnieje
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -WindowStyle Hidden -File `"$scriptPath`""

# Wyzwalacz: co godzine, startuje od teraz
$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 1) -Once -At (Get-Date)

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -RunOnlyIfNetworkAvailable:$false `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Bidirectional sync: Desktop\Dokumentacja <-> .1_Projekty\WSZYSTKIE DOKUMENTY ADRIANA" `
    -Force

Write-Host ""
Write-Host "Task zarejestrowany: $taskName"
Write-Host "Uruchamia sie co godzine automatycznie."
Write-Host ""
Write-Host "Aby uruchomic recznie:"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'"
Write-Host "Aby sprawdzic status:"
Write-Host "  Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo"
