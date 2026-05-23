@echo off
REM === ADRION 369 Copilot Plugins Installer ===
REM Instalacja 42 VS Code Extensions

setlocal enabledelayedexpansion

echo.
echo ========================================================================
echo.      Instalacja Copilot Plugins - ADRION 369
echo.
echo ========================================================================
echo.

REM Sprawdzenie dostępności VS Code
where code >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] VS Code CLI nie znaleziony w PATH
    echo Proszę:
    echo   1. Zainstalować VS Code z https://code.visualstudio.com
    echo   2. Upewnić się, że "code" jest dostępny w PATH
    echo   3. Przeładować terminal
    echo.
    pause
    exit /b 1
)

echo [OK] Znaleziono VS Code CLI
code --version
echo.

REM Liczniki
set installed=0
set failed=0
set skipped=0
set total=42

echo Rozpoczynam instalację extensions...
echo.

REM === CRITICAL (10) ===
echo [CRITICAL - Must Install]
call :install_extension "ms-python.python"
call :install_extension "ms-python.pylance"
call :install_extension "ms-python.black-formatter"
call :install_extension "charliermarsh.ruff"
call :install_extension "golang.go"
call :install_extension "ms-vscode.go"
call :install_extension "ms-azuretools.vscode-docker"
call :install_extension "cweijan.vscode-postgresql-client2"
call :install_extension "ms-vscode-remote.remote-containers"
call :install_extension "ms-vscode.powershell"

REM === HIGH PRIORITY (9) ===
echo.
echo [HIGH PRIORITY]
call :install_extension "ms-kubernetes-tools.vscode-kubernetes-tools"
call :install_extension "hashicorp.terraform"
call :install_extension "redhat.vscode-yaml"
call :install_extension "esbenp.prettier-vscode"
call :install_extension "dbaeumer.vscode-eslint"
call :install_extension "ms-vscode.makefile-tools"
call :install_extension "ms-vscode.cmake-tools"
call :install_extension "eamodio.gitlens"
call :install_extension "GitHub.github-vscode-theme"

REM === UTILITIES (15+) ===
echo.
echo [UTILITIES]
call :install_extension "GitHub.codespaces"
call :install_extension "2gua.rainbow-brackets"
call :install_extension "ms-python.debugpy"
call :install_extension "ms-azuretools.vscode-containers"
call :install_extension "ms-vscode.remote-repositories"
call :install_extension "redhat.vscode-commons"
call :install_extension "ms-azuretools.vscode-bicep"
call :install_extension "ms-azuretools.vscode-postgres"
call :install_extension "GitHub.copilot-chat"
call :install_extension "grafana.grafana"
call :install_extension "redhat.vscode-openshift-connector"

REM === ADRION CUSTOM (6) ===
echo.
echo [ADRION CUSTOM]
call :install_extension "adrion.adrion-369-extension"
call :install_extension "adrion.n8n-architect"
call :install_extension "adrion.mcp-protocol-server"
call :install_extension "adrion.guardian-laws-compliance"
call :install_extension "adrion.ebdi-framework"
call :install_extension "adrion.vortex-orchestrator"

REM === PODSUMOWANIE ===
echo.
echo ========================================================================
echo.                    PODSUMOWANIE INSTALACJI
echo.
echo   Zainstalowano:     %installed% extensions
echo   Błędy:            %failed% extensions
echo   Niedostępne:      %skipped% extensions
echo   Razem:            %total% extensions
echo.

if %installed% GTR 0 (
    echo   STATUS: ✓ SUKCES - Zainstalowano %installed%/%total% extensions
    echo.
    echo   Następne kroki:
    echo   1. Przeładuj VS Code: Ctrl+Shift+P + "Developer: Reload Window"
    echo   2. Sprawdź Extensions: Ctrl+Shift+X
    echo   3. W Copilot CLI: /mcp (MCP servers)
) else (
    echo   STATUS: ✗ BRAK ZAINSTALOWANYCH EXTENSIONS
    echo   Sprawdź czy VS Code jest zainstalowany
)

echo.
echo ========================================================================
echo.

pause
goto :eof

:install_extension
setlocal enabledelayedexpansion
set ext=%~1
echo   Installing: %ext%...
code --install-extension %ext% --force >nul 2>&1
if errorlevel 0 (
    echo     ✓ OK
    set /a installed=%installed%+1
) else (
    echo     ✗ FAILED
    set /a failed=%failed%+1
)
endlocal
goto :eof
