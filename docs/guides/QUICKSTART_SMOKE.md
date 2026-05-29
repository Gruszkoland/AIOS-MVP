# Quickstart Smoke

## Cel
Szybka weryfikacja, że kluczowe ścieżki ADRION działają lokalnie po zmianach.

## Kroki
1. Aktywuj środowisko Python i zainstaluj zależności.
2. Uruchom walidator kontekstu repo.
3. Uruchom A11 predeploy check.
4. Uruchom final deployment gate.
5. Uruchom health check.

## Komendy
```powershell
.venv\Scripts\python.exe scripts/reporting/validate_repo_context_status.py
.venv\Scripts\python.exe scripts/reporting/sync_version_state.py
.venv\Scripts\python.exe scripts/reporting/update_project_confidence.py
.venv\Scripts\python.exe scripts/testing/invoke_a11_predeploy_validation.py
.venv\Scripts\python.exe scripts/security/run-final-deployment-gate.py
.venv\Scripts\python.exe scripts/deployment_health_check.py
```

## Kryterium pass
- Wszystkie komendy kończą się kodem `0`.
- Brak ERROR w logach.
- Health check raportuje status healthy.
