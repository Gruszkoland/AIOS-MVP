$ErrorActionPreference = 'Continue'
$logPath = 'C:\Users\adiha\162 demencje w schemacie 369\progress\wsl-docker-admin-repair.log'

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "$ts - $Message" | Tee-Object -FilePath $logPath -Append
}

"" | Out-File -FilePath $logPath -Encoding utf8
Write-Log 'Start naprawy WSL i Docker (Admin).'

Write-Log 'Krok 1: Zamkniecie Docker Desktop (jesli uruchomiony).'
Get-Process -Name 'Docker Desktop' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Log 'Krok 2: wsl --shutdown'
wsl --shutdown 2>&1 | Tee-Object -FilePath $logPath -Append

Write-Log 'Krok 3: Stop uslugi Docker.'
net stop com.docker.service 2>&1 | Tee-Object -FilePath $logPath -Append

Write-Log 'Krok 4: Start uslugi LxssManager.'
net start LxssManager 2>&1 | Tee-Object -FilePath $logPath -Append

Write-Log 'Krok 5: Aktualizacja WSL.'
wsl --update 2>&1 | Tee-Object -FilePath $logPath -Append

Write-Log 'Krok 6: Status WSL.'
wsl --status 2>&1 | Tee-Object -FilePath $logPath -Append

Write-Log 'Krok 7: Lista distro WSL.'
wsl -l -v --all 2>&1 | Tee-Object -FilePath $logPath -Append

Write-Log 'Krok 8: Start uslugi Docker.'
net start com.docker.service 2>&1 | Tee-Object -FilePath $logPath -Append

Write-Log 'Krok 9: Koncowy status uslug.'
Get-Service LxssManager, vmcompute, hns, com.docker.service | Select-Object Name, Status, StartType | Format-Table -AutoSize | Out-String | Tee-Object -FilePath $logPath -Append

Write-Log 'Koniec naprawy (Admin).'
