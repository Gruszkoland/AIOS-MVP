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

2. Ujednolicenie wersjonowania
- Dodaj plik VERSION.
- Synchronizuj VERSION -> MANIFEST.md -> PROJECT_STATE.json.

3. Ujednolicenie dokumentacji tozsamosci
- W README doprecyzuj model: mono-repo multi-stack albo split target.
- Dodaj ADR decyzji architektonicznej (mono-repo vs split).

Definition of Done
- VERSION istnieje i jest referencjonowany.
- README + MANIFEST + PROJECT_STATE bez sprzecznosci wersji.
- CI waliduje REPO_CONTEXT_STATUS.

## Faza B - Bezpieczenstwo repo i hygiene (Dzien 1-2)

1. .gitignore hardening
- Dodaj: __pycache__/, *.db, .lmstudio*, .moonshot*, .wslconfig.

2. Sekrety i artefakty
- Potwierdz aktywna baze .secrets.baseline.
- Upewnij sie, ze detect-secrets jest wymagany w pre-commit i CI.

3. Historia git (krok destrukcyjny - tylko po akceptacji)
- Plan dla usuniecia arbitrage.db i artefaktow z historii (git-filter-repo/BFG).
- Przed wykonaniem: lista obiektow + potwierdzenie usera + backup.

Definition of Done
- Brak nowych artefaktow lokalnych w git status.
- Security scan i pre-commit przechodza.

## Faza C - Architektura i struktura (Dzien 2-4)

1. MCP deduplikacja
- Wybierz standard jednej nazwy katalogu: mcp-servers albo mcp_servers.
- Zrob mapowanie plikow i migracje importow.

2. Build topology
- Zweryfikuj cmd/vortex-server po stronie Go i decyzje: osobny module lub jawne odseparowanie od Rust workspace.

3. Compose i Docker spojnosc
- Zdefiniuj canonical entrypoint compose dla glownego scenariusza.
- Ogranicz proliferacje Dockerfile przez profile i multi-stage pattern.

Definition of Done
- Jedna konwencja MCP.
- Dokument architektury i build flow bez sprzecznosci.
- Canonical compose uruchamia scenariusz referencyjny.

## Faza D - Runtime metrics i wiarygodnosc danych (Dzien 3-5)

1. PROJECT_STATE confidence
- Zastap confidence=100 dynamiczna metryka (success_rate, freshness, task_count).
- Dodaj reguly inicjalizacji i fallback dla stale danych.

2. Testowalnosc metryki
- Testy jednostkowe dla kalkulacji confidence.
- Test regresji: idle agent nie moze miec confidence=100.

Definition of Done
- confidence jest wyliczane dynamicznie.
- Testy metryk przechodza.

## Faza E - CI/CD i quality gates (Dzien 4-6)

1. Python quality lane
- Wymus: ruff, black, mypy --strict, bandit, safety.

2. Rust unsafe verification
- Dodaj cargo miri do pipeline dla obszarow z unsafe.

3. Dokumentacja i szybki start
- Dodaj QUICKSTART.md z komendami smoke dla Rust i Python.
- Dodaj badge coverage Python.

Definition of Done
- CI przechodzi dla obu stackow.
- QUICKSTART dziala w clean env.

## Faza F - Governance final (Dzien 6-7)

1. CODEOWNERS
- Mapowanie wlascicieli dla crates/modulow Python.

2. Branch protection (procedural)
- Wymagany min. 1 review + zielone CI przed merge.

3. Raport zamkniecia
- Final score re-evaluation i delta vs 54/100.

Definition of Done
- CODEOWNERS aktywny.
- Polityki merge opisane i wdrozone.

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

- [ ] Dodac VERSION + synchronizator VERSION.
- [ ] Dodac CI validator REPO_CONTEXT_STATUS.
- [ ] Harden .gitignore.
- [ ] Przygotowac plan bezpiecznego usuniecia artefaktow z historii.
- [ ] Wybrac kanoniczna nazwe katalogu MCP i zaplanowac migracje.
