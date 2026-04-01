@echo off
REM ADRION 369 Setup Script - Ollama & Aider Quick Start

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║         ADRION 369 - Quick Setup Script for Windows            ║
echo ║   Multi-Persona AI Coding System with Trinity + EBDI           ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Check if Ollama is installed
echo [1] Checking Ollama installation...
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ❌ Ollama не найден в PATH
    echo.
    echo 📥 Please install Ollama from: https://ollama.ai/
    echo.
    echo After installation, add to PATH:
    echo    C:\Users\%USERNAME%\AppData\Local\Programs\Ollama
    echo.
    echo Then reopen this script.
    pause
    exit /b 1
) else (
    echo ✅ Ollama found!
    ollama --version
)

echo.
echo [2] Checking installed models...
ollama list

echo.
echo [3] Would you like to download deepseek-coder-v2:16b? (Y/N)
set /p download_model="Enter choice: "

if /i "%download_model%"=="Y" (
    echo.
    echo 📥 Downloading deepseek-coder-v2:16b (warning: ~9GB)...
    echo.
    ollama pull deepseek-coder-v2:16b
    if %errorlevel% equ 0 (
        echo ✅ Model downloaded successfully!
    ) else (
        echo ❌ Download failed. Check internet connection.
        pause
        exit /b 1
    )
)

echo.
echo [4] Starting Ollama server...
echo.
echo 🚀 Ollama starting on localhost:11434
echo.
echo Press Ctrl+C to stop the server
echo.
ollama serve

