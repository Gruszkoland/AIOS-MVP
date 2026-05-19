# Monitor system performance real-time
# Usage: .\scripts/monitor_system.ps1

param(
    [int]$IntervalSeconds = 5,
    [int]$DurationMinutes = 0  # 0 = infinite
)

$startTime = Get-Date
$endTime = if ($DurationMinutes -gt 0) { $startTime.AddMinutes($DurationMinutes) } else { $null }

$processes = @('Code', 'docker.backend', 'vmmem', 'explorer', 'MsMpEng', 'python', 'powershell')

function Get-MemoryPercent {
    $totalMem = (Get-WmiObject Win32_OperatingSystem).TotalVisibleMemorySize
    $freeMem = (Get-WmiObject Win32_OperatingSystem).FreePhysicalMemory
    [math]::Round((($totalMem - $freeMem) / $totalMem) * 100, 1)
}

function Format-ByteSize {
    param([int64]$Bytes)
    if ($Bytes -ge 1GB) {
        return "{0:N1} GB" -f ($Bytes / 1GB)
    } elseif ($Bytes -ge 1MB) {
        return "{0:N1} MB" -f ($Bytes / 1MB)
    } else {
        return "{0:N1} KB" -f ($Bytes / 1KB)
    }
}

while ($true) {
    if ($endTime -and (Get-Date) -gt $endTime) { break }

    Clear-Host
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "🖥️  ADRION SYSTEM MONITOR — $timestamp" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan

    # System metrics
    $sysMemPercent = Get-MemoryPercent
    $sysMemColor = if ($sysMemPercent -gt 80) { "Red" } elseif ($sysMemPercent -gt 60) { "Yellow" } else { "Green" }
    Write-Host ""
    Write-Host "📊 SYSTEM MEMORY: $sysMemPercent% used " -ForegroundColor $sysMemColor

    # Process metrics
    Write-Host ""
    Write-Host "🔍 TOP PROCESSES:" -ForegroundColor White
    Get-Process | Where-Object { $_.Name -in $processes } | Sort-Object -Property WorkingSet64 -Descending | ForEach-Object {
        $procName = $_.ProcessName.PadRight(20)
        $pid = "PID: $($_.Id)".PadRight(12)
        $cpu = [math]::Round($_.CPU, 1)
        $cpuStr = "CPU: $cpu%".PadRight(12)
        $mem = Format-ByteSize($_.WorkingSet64)

        $cpuColor = if ($cpu -gt 50) { "Red" } elseif ($cpu -gt 25) { "Yellow" } else { "Green" }
        Write-Host "  $procName | $pid | $cpuStr | MEM: $mem" -ForegroundColor $cpuColor
    }

    Write-Host ""
    Write-Host "⏱️  Refreshing in $IntervalSeconds seconds... (Ctrl+C to stop)" -ForegroundColor Gray
    Start-Sleep -Seconds $IntervalSeconds
}

Write-Host "✅ Monitoring stopped." -ForegroundColor Green
