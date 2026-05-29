# Organization Implementation TODO Tracker

Typ dokumentu: How-to + status tracker

## Cel

Ten plik pokazuje wszystkie etapy wdrozenia organizacji repozytoriow oraz aktualny status wykonania.

## Legenda statusow

- [x] done
- [~] in progress
- [ ] planned

## Faza 0 - Alignment i governance freeze

- [x] Potwierdzic role trzech repo (Formula -> Architecture -> System)
- [x] Uzgodnic scope in/out dla kazdego repo
- [x] Przygotowac i zatwierdzic artefakty governance

## Faza 1 - Mission statements i artefakty kontrolne

- [x] Wstawic mission statement do README repo systemowego
- [x] Wstawic mission statement do README repo architecture
- [x] Utworzyc README scaffold dla formula target
- [x] Przygotowac PR payloady
- [x] Przygotowac mapping review bucket
- [x] Przygotowac daily checklist migracji

## Faza 2 - Migracja folderow (staging, bez kasowania)

- [x] Batch #1: przeniesc male foldery review bucket do stagingu
- [x] Batch #2: przeniesc duze foldery review bucket do stagingu (to-system / to-architecture / to-archive)
- [x] Wykonac szybki smoke po Batch #2
- [x] Zamknac Gate Week 1

## Faza 3 - PR i stabilizacja po migracjach

- [~] Przygotowac i domknac PR dla Batch #2 moves
- [x] Zmapowac importy po przeniesieniach
- [x] Naprawic sciezki skryptow i CI
- [x] Uruchomic smoke rozszerzony (selected tests + path checks)

## Delta wykonawcza (2026-05-29)

- [x] Dodano SSOT: `REPO_CONTEXT_STATUS.txt`.
- [x] Dodano gate CI: `repo-context-gate`.
- [x] Wlaczono walidacje spojnosci wersji (`VERSION`, `MANIFEST`, `PROJECT_STATE`).
- [x] Rozszerzono hardening `.gitignore`.
- [x] Wybrano kanoniczna konwencje MCP: `mcp_servers`.
- [x] Poprawiono wolumeny MCP w compose tier.
- [x] Wdrozono dynamiczne confidence w `PROJECT_STATE` + testy regresji.
- [x] Potwierdzono build topology dla `cmd/vortex-server`.
- [x] Ustalono canonical compose dla scenariusza referencyjnego: `docker-compose.local.yml`.
- [x] Zaktualizowano aktywne referencje runtime po migracjach (`Cargo.toml`, `rust-ci.yml`, `docker-compose.yml`, `CODEOWNERS`, `README.md`).
- [x] Wygenerowano pelna mape referencji: `POST_MIGRATION_REFERENCE_MAP.md`.

## Faza E/F - Quality lane i governance closure

- [x] Dodano workflow quality lane (`black`, `ruff`, `mypy --strict`, `bandit`, `safety`, `miri`).
- [x] Zaktualizowano README o badge quality/Python CI.
- [x] Dodano plan final governance closure i wymagane merge checks.
- [~] Domkniecie PR migracyjnego po zielonym pipeline.

## Faza 4 - Canonical extraction (Week 2)

- [x] Przeniesc canonical docs do Formula (staging: `migration_batches/batch3/to-formula/canonical-core`)
- [ ] Przeniesc contracts i schemas do Formula
- [~] Zastapic duplikaty canonical references w Architecture (manifest i kandydaci wygenerowani)
- [~] Zastapic duplikaty canonical references w System (manifest i kandydaci wygenerowani)
- [ ] Uruchomic i domknac canonical sync gate

Dowody wykonania (2026-05-29):

- `scripts/reporting/extract_canonical_docs.py`
- `docs/guides/repo-organization/CANONICAL_EXTRACTION_MANIFEST.md`
- `docs/guides/repo-organization/CANONICAL_EXTRACTION_MANIFEST.json`

## Faza 5 - Architecture consolidation (Week 3)

- [ ] Oczyscic Architecture do roli referencyjnej
- [ ] Domknac matrix testow (unit/security/stress)
- [ ] Opublikowac compatibility notes dla System
- [ ] Zweryfikowac integracje System <-> Architecture output

## Faza 6 - System realignment i retencja (Week 4-5)

- [ ] Ulozyc docelowy layout apps/services/platform/ops/docs/governance
- [ ] Przeniesc runtime assets do docelowych stref
- [ ] Wykonac smoke po kazdym batch move
- [ ] Przygotowac archive manifest i checksum index
- [ ] Wprowadzic retention policy dla ciezkich archiwow

## Faza 7 - Cutover i zamkniecie programu (Week 6)

- [ ] Wykonac final canonical integrity check
- [ ] Wykonac final release candidate validation
- [ ] Wykonac final cutover checklist
- [ ] Uruchomic end-to-end regresje
- [ ] Uzyskac final sign-off i zamknac migracje

## Biezacy etap wdrozenia

Aktualnie: Faza 3 (PR i stabilizacja po migracjach) + Faza C (MCP deduplikacja) w toku

Najblizsze 3 kroki:

1. Domknac PR dla Batch #2 moves.
2. Dokonczyc mapowanie importow i sciezek po przeniesieniach.
3. Uruchomic smoke rozszerzony i potwierdzic green lane.
