# Deployment Alternative Tool Adapter

## Cel

Ten adapter pozwala uruchomic zaplanowane wdrazanie poza GitHub Actions,
lokalnie przez PowerShell, przy zachowaniu tych samych bramek jakosci.

## Entry point

Uruchamiany skrypt:

- `scripts/deploy/deploy_via_alternative_tool.ps1`

## Co wykonuje adapter

1. A11 predeploy validation (`scripts/testing/invoke_a11_predeploy_validation.ps1`)
2. Final deployment gate (`scripts/security/run-final-deployment-gate.ps1`)
3. Local deployment (`scripts/deploy-local.ps1`) - opcjonalnie
4. Health check (`scripts/deployment_health_check.py`)

## Uzycie

Pelny przebieg:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy/deploy_via_alternative_tool.ps1
```

Tylko walidacja i gate, bez lokalnego deployu:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy/deploy_via_alternative_tool.ps1 -SkipLocalDeploy
```

Tryb dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy/deploy_via_alternative_tool.ps1 -DryRun
```

Niestandardowy port testowego API:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy/deploy_via_alternative_tool.ps1 -Port 8012
```

## Mapowanie na planowane wdrazanie

- `A11 predeploy` -> kontrola gotowosci runtime i endpointow
- `Final gate` -> kontrola quality/security przed deployem
- `Local deployment` -> uruchomienie stacku lokalnego
- `Health check` -> potwierdzenie stanu po wdrozeniu

## Uwagi

- Adapter nie modyfikuje istniejacych workflow CI/CD.
- Adapter spina istniejace skrypty w jeden punkt uruchomienia.
- Zalecane uruchamianie z katalogu glownego repo.

## Governance reorganizacji repo

Przy porzadkowaniu struktury repo stosuj gotowe szablony z:

- `docs/guides/REPO_REORGANIZATION_TEMPLATES.md`

Kazda propozycja usuwania plikow musi byc opisana sekcja `ZALECANE KASOWANIE`
z lista plikow i jawna akceptacja uzytkownika przed wykonaniem.
