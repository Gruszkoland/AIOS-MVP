# uap_launcher.ps1
# ADRION 369 - System Launcher Script
# Manages backend/frontend startup and cleanup

param(
    [switch]$AutoStart = $false,
    [int]$BackendPort = 8002,
    [int]$FrontendPort = 8003
)

$Script:LogFile = "uap_launcher.log"

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARN", "ERROR")]
        [string]$Level = "INFO"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp [$Level] $Message"

    Write-Host $logMessage
    Add-Content -Path $Script:LogFile -Value $logMessage
}

function Test-PortInUse {
    param([int]$Port)

    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if ($connection) {
            Write-Log "Port $Port is in use (PID: $($connection.OwningProcess))" "WARN"
            return $true
        }
        return $false
    }
    catch {
        Write-Log "Error checking port: $_" "WARN"
        return $false
    }
}

function Stop-ProcessOnPort {
    param([int]$Port)

    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if ($connection) {
            $pid = $connection.OwningProcess
            Write-Log "Killing process $pid on port $Port" "WARN"
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
        }
    }
    catch {
        Write-Log "Error stopping process: $_" "ERROR"
    }
}

function Test-HealthCheck {
    param(
        [int]$Port = 8002,
        [int]$TimeoutSeconds = 2
    )

    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Port/mapi/v1/health" `
                                      -TimeoutSec $TimeoutSeconds `
                                      -ErrorAction SilentlyContinue
        return ($response.StatusCode -eq 200)
    }
    catch {
        return $false
    }
}

function Start-Backend {
    Write-Log "Starting backend services..."

    # Check ports
    if (Test-PortInUse -Port $BackendPort) {
        Write-Log "Port $BackendPort in use, attempting to free..." "WARN"
        Stop-ProcessOnPort -Port $BackendPort
    }

    # Start launcher
    $launcherPath = "scripts/launch_uap_local_v3.py"
    if (-not (Test-Path $launcherPath)) {
        Write-Log "Launcher not found: $launcherPath" "ERROR"
        return $false
    }

    try {
        Write-Log "Running: python $launcherPath"
        $process = Start-Process -FilePath "python.exe" `
                                 -ArgumentList $launcherPath `
                                 -PassThru `
                                 -WindowStyle Minimized

        Write-Log "Launcher started (PID: $($process.Id))" "INFO"

        # Wait for backend to be ready (15 seconds)
        for ($i = 0; $i -lt 30; $i++) {
            if (Test-HealthCheck -Port $BackendPort) {
                Write-Log "✓ Backend is healthy" "INFO"
                return $true
            }
            Start-Sleep -Milliseconds 500
        }

        Write-Log "Backend startup timeout" "ERROR"
        return $false
    }
    catch {
        Write-Log "Error starting backend: $_" "ERROR"
        return $false
    }
}

function Start-TrayApp {
    Write-Log "Starting tray application..."

    $trayScript = "uap\desktop\systray\uap_systray.py"
    if (-not (Test-Path $trayScript)) {
        Write-Log "Tray script not found: $trayScript" "ERROR"
        return $false
    }

    try {
        $process = Start-Process -FilePath ".venv\Scripts\python.exe" `
                                 -ArgumentList $trayScript `
                                 -PassThru

        Write-Log "Tray app started (PID: $($process.Id))" "INFO"
        return $true
    }
    catch {
        Write-Log "Error starting tray: $_" "ERROR"
        return $false
    }
}

function Main {
    Write-Log "========================================" "INFO"
    Write-Log "ADRION 369 - UAP Launcher" "INFO"
    Write-Log "========================================" "INFO"
    Write-Log "AutoStart: $AutoStart" "INFO"
    Write-Log "Backend Port: $BackendPort" "INFO"
    Write-Log "Frontend Port: $FrontendPort" "INFO"

    # Check venv
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        Write-Log "Python venv not found!" "ERROR"
        return 1
    }

    # Start backend if requested
    if ($AutoStart) {
        if (-not (Start-Backend)) {
            Write-Log "Failed to start backend" "ERROR"
            return 1
        }
    }

    # Start tray app
    if (-not (Start-TrayApp)) {
        Write-Log "Failed to start tray app" "ERROR"
        return 1
    }

    Write-Log "✓ Launch sequence complete" "INFO"
    return 0
}

# Run
exit (Main)
