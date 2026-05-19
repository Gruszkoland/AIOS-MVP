#!/usr/bin/env pwsh
# ETAP 1 Deployment with full logging to file

$logFile = "ETAP_1_DEPLOYMENT.log"

"[$(Get-Date)] ETAP 1 DEPLOYMENT START" | Add-Content $logFile

cd "c:\Users\adiha\162 demencje w schemacie 369"

try {
    "[$(Get-Date)] Phase 1: Starting PostgreSQL..." | Add-Content $logFile
    docker-compose up -d postgres 2>&1 | Add-Content $logFile

    "[$(Get-Date)] Waiting 20 seconds for container startup..." | Add-Content $logFile
    Start-Sleep -Seconds 20

    "[$(Get-Date)] Checking container status..." | Add-Content $logFile
    docker ps --filter "name=adrion-postgres" 2>&1 | Add-Content $logFile

    "[$(Get-Date)] Phase 2: Applying schema..." | Add-Content $logFile
    $sql = Get-Content "scripts/db_migrations/001_schema_init.sql" -Raw
    $sql | docker exec -i adrion-postgres psql -U adrion -d genesis_record 2>&1 | Add-Content $logFile

    "[$(Get-Date)] Verifying tables..." | Add-Content $logFile
    docker exec adrion-postgres psql -U adrion -d genesis_record -c "\dt" 2>&1 | Add-Content $logFile

    "[$(Get-Date)] ✅ DEPLOYMENT COMPLETE" | Add-Content $logFile
}
catch {
    "[$(Get-Date)] ❌ ERROR: $_" | Add-Content $logFile
}

"[$(Get-Date)] Showing log file:"
Get-Content $logFile | Select-Object -Last 50
