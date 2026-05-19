# Plan: Organizacja przestrzeni `C:\Users\adiha\.1_Projekty`

Data: 2026-05-15 10:48:57 +02:00
Status: `in-progress`
Tryb: dry-run, bez fizycznego przenoszenia plików

## Sygnatura DSV

`Input`: rozproszona przestrzeń projektowa `C:\Users\adiha\.1_Projekty`

`Output`: uporządkowany katalog główny, manifest przenosin, raport weryfikacji, brak utraty danych

## Definicja Ukończenia

- Katalog główny ma czytelne strefy: dokumentacja, narzędzia, wizualizacje, raporty, archiwum.
- Pliki krytyczne pozostają w miejscu: `.git`, `.agents`, `.github`, `.n8nac`, `.vscode`, `AGENTS.md`, `README.md`, `.gitattributes`, `desktop.ini`.
- Aktywne projekty nie są przenoszone bez osobnej akceptacji: `162 demencje w schemacie 369`, `Consultacja-Wielomodelowa-AI`, `n8n-produkcja`, `adrion-369-architecture`, `adrion-deploy`, `leadgen-comet-pipeline`, `embedding-ab-test-framework`, `kyc-provider-integration-guide`.
- Każde przeniesienie ma jawne źródło i cel.
- Po przenosinach przechodzi weryfikacja: brak konfliktów nazw, brak brakujących plików, aktualny `git status`.

## Fazy

| Faza | Status | Cel | Weryfikacja |
|---|---|---|---|
| 0 | `done` | Inwentaryzacja root | Lista katalogów i plików pobrana read-only |
| 1 | `done` | Identyfikacja ryzyka | Wykryto aktywne zmiany Git i zależności n8n |
| 2 | `done` | Utworzenie struktury katalogów | Katalogi istnieją, brak konfliktów |
| 3 | `planned` | Przeniesienie plików luźnych | Manifest źródło -> cel zgodny |
| 4 | `planned` | Opcjonalne przeniesienie katalogów projektów | Tylko po osobnej akceptacji |
| 5 | `planned` | Aktualizacja indeksów | Linki i ścieżki zgodne z nową strukturą |
| 6 | `planned` | Raport końcowy | `REPORTS/...` zawiera wynik |

## Docelowy Porządek

```text
C:\Users\adiha\.1_Projekty
|-- README.md
|-- AGENTS.md
|-- 00_DOKUMENTACJA/
|   |-- operacyjna/
|   `-- referencje/
|-- 20_NARZEDZIA/
|-- 30_WIZUALIZACJE/
|-- 40_RAPORTY/
|-- 90_ARCHIWUM/
|   `-- paczki/
|-- PLAN/
|-- PROGRESS/
`-- REPORTS/
```

## Polityka Bezpieczeństwa

- Nie usuwać plików.
- Nie nadpisywać plików docelowych.
- Nie używać `git reset`, `git clean`, `Remove-Item -Recurse` ani kasowania duplikatów.
- Nie przenosić folderów `.git`, `.n8nac`, `.agents`, `.github`, `.vscode`.
- Nie przenosić aktywnych projektów bez zatwierdzonego etapu 2.

## Rekomendowana Ścieżka

Wykonać etap 1: przenieść wyłącznie 56 luźnych plików root do stref `00/20/30/40/90`. To daje natychmiastowy porządek i minimalizuje ryzyko uszkodzenia importów, Docker Compose, n8n oraz aktywnych repozytoriów.
