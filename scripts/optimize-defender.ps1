# Add Windows Defender exclusions for project directories
# Run as Administrator

$exclusions = @(
    "C:\Users\adiha\162 demencje w schemacie 369",
    "C:\Users\adiha\162 demencje w schemacie 369\.venv",
    "C:\Users\adiha\162 demencje w schemacie 369\arbitrage",
    "C:\Users\adiha\162 demencje w schemacie 369\arbitrage-core",
    "C:\Users\adiha\162 demencje w schemacie 369\persona-agents",
    "C:\Users\adiha\162 demencje w schemacie 369\scripts",
    "C:\Users\adiha\162 demencje w schemacie 369\.git",
    "C:\Users\adiha\162 demencje w schemacie 369\tests",
    "C:\Users\adiha\.vscode",
    "C:\Users\adiha\AppData\Local\Docker"
)

Write-Host "Adding Windows Defender exclusions..." -ForegroundColor Cyan

foreach ($path in $exclusions) {
    if (Test-Path $path) {
        Add-MpPreference -ExclusionPath $path -ErrorAction SilentlyContinue
        Write-Host "✅ Excluded: $path" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Path not found: $path" -ForegroundColor Yellow
    }
}

Write-Host "`nDone! Windows Defender is now optimized for development." -ForegroundColor Green
Write-Host "Restart VS Code to apply changes." -ForegroundColor Yellow
