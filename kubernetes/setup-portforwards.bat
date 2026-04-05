@echo off
REM ADRION 369 - Kubernetes Port Forwarding Setup
REM Opens port-forwards for all monitoring and management services

echo.
echo ========================================================================
echo  ADRION 369 - Port Forwarding Configuration
echo ========================================================================
echo.

setlocal enabledelayedexpansion

REM Get kubectl path
for /f "tokens=*" %%A in ('where kubectl') do set KUBECTL=%%A

if "%KUBECTL%"=="" (
    echo ERROR: kubectl not found in PATH
    exit /b 1
)

echo [INFO] kubectl found at: %KUBECTL%
echo.

REM Create separate terminal windows for each port-forward
echo [1] Starting API Gateway port-forward (localhost:8001)...
start "API Gateway - :8001" cmd /k "%KUBECTL% port-forward -n adrion-369 svc/api 8001:8001"

timeout /t 2 /nobreak

echo [2] Starting Grafana port-forward (localhost:3000)...
start "Grafana Dashboard - :3000" cmd /k "%KUBECTL% port-forward -n adrion-369 svc/grafana 3000:3000"

timeout /t 2 /nobreak

echo [3] Starting Prometheus port-forward (localhost:9090)...
start "Prometheus Metrics - :9090" cmd /k "%KUBECTL% port-forward -n adrion-369 svc/prometheus 9090:9090"

timeout /t 2 /nobreak

echo [4] Starting Loki port-forward (localhost:3100)...
start "Loki Logs - :3100" cmd /k "%KUBECTL% port-forward -n adrion-369 svc/loki 3100:3100"

timeout /t 2 /nobreak

echo [5] Starting N8N port-forward (localhost:5678)...
start "N8N Workflows - :5678" cmd /k "%KUBECTL% port-forward -n adrion-369 svc/n8n 5678:5678"

timeout /t 2 /nobreak

echo [6] Starting Ollama port-forward (localhost:11434)...
start "Ollama LLM - :11434" cmd /k "%KUBECTL% port-forward -n adrion-369 svc/ollama 11434:11434"

echo.
echo ========================================================================
echo [OK] All port-forwards started
echo ========================================================================
echo.
echo Accessible services:
echo   API Gateway:    http://localhost:8001/health
echo   Grafana:        http://localhost:3000 (admin/admin)
echo   Prometheus:     http://localhost:9090
echo   Loki:           http://localhost:3100
echo   N8N:            http://localhost:5678
echo   Ollama:         http://localhost:11434/api/tags
echo.
echo Each service opened in a separate terminal window.
echo Close any terminal to stop that port-forward.
echo.
pause
