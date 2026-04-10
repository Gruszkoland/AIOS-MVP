@echo off
REM Test manualnego zasilania strumieni wydarzeń (UGC i Resale) w Arbitrage Server.
REM Wykorzystuje endpoint POST /api/arbitrage/streams/run.
REM Jeśli nie ustawisz URLach źródeł w .env, system i tak zadziała w trybie "Seeded", 
REM ale ten test pokaże, jak API raportuje stan konektorów.

echo [1/3] Sprawdzanie aktualnego stanu konektorów...
curl -X GET http://localhost:5000/api/arbitrage/status
echo.

echo [2/3] Automatyczne uruchomienie procesów strumieniowych (próba fetchowania)...
curl -X POST http://localhost:5000/api/arbitrage/streams/run
echo.

echo [3/3] Gotowe. Jeśli w konsoli serwera widzisz "Source: External", dane spłynęły z URL.
echo Zobacz wyniki w Dashboardzie: http://localhost:5000/
pause
