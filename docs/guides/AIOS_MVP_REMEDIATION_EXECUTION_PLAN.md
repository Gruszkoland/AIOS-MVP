# AIOS-MVP Remediation Execution Plan (54 -> 85+)

## Cel

Plan wykonania zadan z audytu 54/100 tak, aby uporzadkowac architekture, bezpieczenstwo, governance i CI bez zatrzymywania rozwoju.

## Zakres

- Wejscie: lista zadan z pliku Bierząca praca naprawcza NIESKOŃCZONA.txt.
- Wyjscie: spójny backlog wdrozeniowy z kolejnością, gate'ami i mierzalnym DoD.

## Zasada wykonania

- Priorytet: KRYTYCZNE -> WYSOKIE -> SREDNIE -> NISKIE.
- Brak destrukcyjnych krokow bez jawnej akceptacji (dotyczy usuwania plikow i czyszczenia historii git).
- Kazdy etap konczy sie bramka PASS/FAIL i aktualizacja REPO_CONTEXT_STATUS.txt.

## Faza A - Governance i SSOT (Dzien 1)

1. Ujednolicenie kontekstu repo

- Utrzymaj i waliduj REPO_CONTEXT_STATUS.txt jako SSOT.
- Dodaj CI gate: fail PR gdy brakuje sekcji wymaganych.

1. Ujednolicenie wersjonowania

- Dodaj plik VERSION.
- Synchronizuj VERSION -> MANIFEST.md -> PROJECT_STATE.json.

1. Ujednolicenie dokumentacji tozsamosci

- W README doprecyzuj model: mono-repo multi-stack albo split target.
- Dodaj ADR decyzji architektonicznej (mono-repo vs split).

Definition of Done

- VERSION istnieje i jest referencjonowany.
- README + MANIFEST + PROJECT_STATE bez sprzecznosci wersji.
- CI waliduje REPO_CONTEXT_STATUS.

## Faza B - Bezpieczenstwo repo i hygiene (Dzien 1-2)

1. .gitignore hardening

- Dodaj: **pycache**/, _.db, .lmstudio_, .moonshot\*, .wslconfig.

1. Sekrety i artefakty

- Potwierdz aktywna baze .secrets.baseline.
- Upewnij sie, ze detect-secrets jest wymagany w pre-commit i CI.

1. Historia git (krok destrukcyjny - tylko po akceptacji)

- Plan dla usuniecia arbitrage.db i artefaktow z historii (git-filter-repo/BFG).
- Przed wykonaniem: lista obiektow + potwierdzenie usera + backup.

Definition of Done

- Brak nowych artefaktow lokalnych w git status.
- Security scan i pre-commit przechodza.

## Faza C - Architektura i struktura (Dzien 2-4)

1. MCP deduplikacja

- Wybierz standard jednej nazwy katalogu: mcp-servers albo mcp_servers.
- Zrob mapowanie plikow i migracje importow.

1. Build topology

- Zweryfikuj cmd/vortex-server po stronie Go i decyzje: osobny module lub jawne odseparowanie od Rust workspace.

1. Compose i Docker spojnosc

- Zdefiniuj canonical entrypoint compose dla glownego scenariusza.
- Ogranicz proliferacje Dockerfile przez profile i multi-stage pattern.

Definition of Done

- Jedna konwencja MCP.
- Dokument architektury i build flow bez sprzecznosci.
- Canonical compose uruchamia scenariusz referencyjny.

Status wykonania (2026-05-29)

- [x] MCP deduplikacja: wybrana konwencja `mcp_servers` i poprawione aktywne wolumeny compose.
- [x] Build topology: `go list ./cmd/vortex-server/...` potwierdza separacje przez modul `adrion-vortex`.
- [x] Canonical compose (scenariusz referencyjny dev): `docker-compose.local.yml`.
- [ ] Ograniczenie proliferacji Dockerfile przez profile i full multi-stage standard (pozostaje).

## Faza D - Runtime metrics i wiarygodnosc danych (Dzien 3-5)

1. PROJECT_STATE confidence

- Zastap confidence=100 dynamiczna metryka (success_rate, freshness, task_count).
- Dodaj reguly inicjalizacji i fallback dla stale danych.

1. Testowalnosc metryki

- Testy jednostkowe dla kalkulacji confidence.
- Test regresji: idle agent nie moze miec confidence=100.

Definition of Done

- confidence jest wyliczane dynamicznie.
- Testy metryk przechodza.

Status wykonania (2026-05-29)

- [x] Wdrozone dynamiczne confidence (`arbitrage/project_state_confidence.py`).
- [x] Dodano updater (`scripts/reporting/update_project_state_confidence.py`).
- [x] Dodano testy regresji (`tests/test_project_state_confidence.py`) - PASS.

## Faza E - CI/CD i quality gates (Dzien 4-6)

1. Python quality lane

- Wymus: ruff, black, mypy --strict, bandit, safety.

1. Rust unsafe verification

- Dodaj cargo miri do pipeline dla obszarow z unsafe.

1. Dokumentacja i szybki start

- Dodaj QUICKSTART.md z komendami smoke dla Rust i Python.
- Dodaj badge coverage Python.

Definition of Done

- CI przechodzi dla obu stackow.
- QUICKSTART dziala w clean env.

Status wykonania (2026-05-29)

- [x] Dodano quality lane workflow: `black`, `ruff`, `mypy --strict`, `bandit`, `safety`, `miri`.
- [x] Dodano coverage/quality badge do README.
- [~] Pelne domkniecie CI po rerun na branchu PR.

## Faza F - Governance final (Dzien 6-7)

1. CODEOWNERS

- Mapowanie wlascicieli dla crates/modulow Python.

1. Branch protection (procedural)

- Wymagany min. 1 review + zielone CI przed merge.

1. Raport zamkniecia

- Final score re-evaluation i delta vs 54/100.

Definition of Done

- CODEOWNERS aktywny.
- Polityki merge opisane i wdrozone.

Status wykonania (2026-05-29)

- [x] CODEOWNERS zaktualizowany do bieżących ścieżek po migracji.
- [x] Dodano dokument final governance closure i zestaw wymaganych checków.
- [~] Wdrozenie branch protection pozostaje do wykonania po stronie ustawien GitHub.

## Kolejnosc wdrozenia (critical path)

1. Faza A (SSOT + wersjonowanie)
2. Faza B (.gitignore + security hygiene)
3. Faza C (MCP + architektura + compose)
4. Faza D (confidence metrics)
5. Faza E (CI/miri/quickstart)
6. Faza F (governance final)

## Ryzyka i mitigacje

- Ryzyko: zmiany destrukcyjne historii git.
- Mitigacja: backup, dry-run, jawna akceptacja usera.

- Ryzyko: regresja przez deduplikacje MCP.
- Mitigacja: etapowe PR i testy importow.

- Ryzyko: dalszy dryf dokumentacji.
- Mitigacja: SSOT + walidator w CI.

## Checklist startowa (następne 24h)

- [x] Dodac VERSION + synchronizator VERSION.
- [x] Dodac CI validator REPO_CONTEXT_STATUS.
- [x] Harden .gitignore.
- [x] Przygotowac plan bezpiecznego usuniecia artefaktow z historii.
- [x] Wybrac kanoniczna nazwe katalogu MCP i zaplanowac migracje.

### Delta wdrozenia (2026-05-29)

- Dodano `REPO_CONTEXT_STATUS.txt` jako aktywny SSOT z wymaganymi sekcjami.
- Dodano walidator: `scripts/reporting/validate_repo_context_status.py`.
- Dodano CI gate: `.github/workflows/repo-context-gate.yml`.
- Ujednolicono wersjonowanie: `VERSION -> MANIFEST (Project Version) -> PROJECT_STATE.project_version`.
- Ujednolicono MCP na konwencji `mcp_servers` i poprawiono mapowania volume w `docker-compose.mcp-tier.yml`.
- Dodano runbook non-destructive dla purge historii: `docs/guides/repo-organization/GIT_HISTORY_ARTIFACT_PURGE_PLAN.md`.

## Plan wykonawczy T-48h do deadline PARP (startup funding readiness)

### Założenie operacyjne

- MVP traktujemy jako prototyp TRL 3-4 do oceny inwestycyjnej, nie jako produkcję.
- Celem jest pakiet 100/100 w rubryce: technika + biznes + compliance + outreach.

### Rubryka 100/100 (10 x 10 punktów)

1. Product narrative i problem-solution fit
2. Wiarygodność techniczna demonstratora
3. Deployment + rollback repeatability
4. CI quality gates
5. Security + AI Act readiness
6. Repo governance i SSOT
7. IP ownership i ochrona know-how
8. Ekonomia i wycena aportu
9. Outreach Z01-Z05 execution
10. Data room kompletność

### Harmonogram godzinowy (T-48h)

#### Blok 1 (T-48h do T-36h): domknięcie techniczne

- [ ] T-48h: Freeze scope MVP (bez nowych feature)
- [ ] T-47h: Zielona ścieżka smoke test dla demonstratora
- [ ] T-46h: Ustabilizować jeden canonical workflow CI do pokazu
- [ ] T-45h: Zapis dowodów PASS (log, commit, timestamp)
- [ ] T-44h: Weryfikacja rollback strategy w praktyce
- [ ] T-43h: Zamknięcie listy known risks z mitigacją
- [ ] T-42h: Review security findings (critical/high)
- [ ] T-41h: Review dependency risk (Python/Go/Rust)
- [ ] T-40h: Potwierdzenie minimalnej ścieżki uruchomienia MVP
- [ ] T-39h: Snapshot statusu repo pod audyt
- [ ] T-38h: Final smoke rerun po poprawkach
- [ ] T-37h: Lock dokumentacji technicznej do wersji demo
- [ ] T-36h: Gate G1: Technical Credibility PASS/FAIL

#### Blok 2 (T-36h do T-24h): pakiet inwestorski

- [ ] T-35h: One-pager Investment Memo v1
- [ ] T-34h: Value proposition i moat (ADRION 162D + AI Act)
- [ ] T-33h: Segmentacja klientów i use-case pitch
- [ ] T-32h: COCOMO II assumptions i wycena $894k update
- [ ] T-31h: IP ownership statement (100% founders)
- [ ] T-30h: Ryzyka prawne i compliance notes
- [ ] T-29h: Series A readiness T+100 roadmap
- [ ] T-28h: Data room index (co, gdzie, po co)
- [ ] T-27h: Evidence pack: logi, metryki, wyniki testów
- [ ] T-26h: FAQ inwestorskie (10 najtrudniejszych pytań)
- [ ] T-25h: Pitch narrative 3 min i 10 min
- [ ] T-24h: Gate G2: Investor Package PASS/FAIL

#### Blok 3 (T-24h do T-12h): outreach Z01-Z05

- [ ] T-23h: Lista targetów Z01 (VC) - min 20
- [ ] T-22h: Lista targetów Z02 (inkubacja/akceleracja) - min 20
- [ ] T-21h: Lista targetów Z03 (grant/public) - min 20
- [ ] T-20h: Lista targetów Z04 (partnerzy strategiczni) - min 20
- [ ] T-19h: Lista targetów Z05 (aniołowie/syndykaty) - min 20
- [ ] T-18h: Szablon wiadomości A/B (mail/LinkedIn)
- [ ] T-17h: Batch #1 wysyłek (top 40 kontaktów)
- [ ] T-16h: Follow-up template + CRM tracker
- [ ] T-15h: Batch #2 wysyłek (kolejne 60 kontaktów)
- [ ] T-14h: Triaging odpowiedzi i kwalifikacja leadów
- [ ] T-13h: Ustalanie terminów spotkań intro
- [ ] T-12h: Gate G3: Outreach KPI PASS/FAIL

#### Blok 4 (T-12h do T-0h): finalizacja

- [ ] T-11h: Ostateczny consistency check SSOT
- [ ] T-10h: Aktualizacja statusu wersji i changelogów
- [ ] T-9h: Final evidence pack zip + checksum
- [ ] T-8h: Rehearsal demo + pitch
- [ ] T-7h: Security/compliance sign-off
- [ ] T-6h: Backup i rollback checkpoint
- [ ] T-5h: Final outreach push + follow-up
- [ ] T-4h: Gate review board (Go/No-Go)
- [ ] T-3h: Poprawki krytyczne tylko typu blocker
- [ ] T-2h: Freeze final artifacts
- [ ] T-1h: Wysyłka finalnych pakietów
- [ ] T-0h: Zamknięcie sesji i raport końcowy

### KPI wykonawcze (minimum)

- Technical: 1 canonical green lane + 1 powtarzalny smoke pass
- Governance: 0 sprzeczności między VERSION/README/MANIFEST/PROJECT_STATE
- Investor: 1 komplet memo + valuation + IP statement + roadmap
- Outreach: 100 kontaktów (5x20), min 10 odpowiedzi, min 3 spotkania

### Kryterium Go/No-Go

- GO: wszystkie bramki G1, G2, G3 = PASS
- NO-GO: dowolna bramka FAIL -> wysyłka ograniczona do soft outreach i szybka pętla naprawcza
