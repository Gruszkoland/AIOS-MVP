@echo off
REM ADRION 369 Dashboard - Quick Start Script

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║         ADRION 369 Dashboard - Windows Quick Start             ║
echo ║              🚀 Start dashboard on http://localhost:8000       ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Check Python
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python not found!
    echo.
    echo Install Python from: https://www.python.org/downloads/
    echo Then run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo ✅ Python found
python --version

echo.
echo 🚀 Starting Dashboard Server on http://localhost:8000
echo.
echo Press Ctrl+C to stop
echo.

python server.py
