# Repo Reorganization Templates

## Cel

Stale szablony do cyklicznej reorganizacji repo, zgodne z polityka bezpiecznego usuwania.

## Template 1 - Plan Reorganizacji (bez kasowania)

```md
# Plan Reorganizacji Repo - <Nazwa>

## Zakres
- Przeniesienia: <lista katalogow i plikow>
- Bez kasowania: TAK
- Czas wykonania: <okno>

## Etapy
1. Inwentaryzacja plikow root
2. Klasyfikacja: core/docs/artifacts
3. Przeniesienia `git mv`
4. Aktualizacja sciezek w CI i skryptach
5. Smoke test

## Kryteria Done
- Brak broken importow
- Brak broken workflow
- Root uproszczony
```

## Template 2 - Blok Obowiazkowy Dla Usuwania

```md
# ZALECANE KASOWANIE

## Powod
- <dlaczego pliki sa zbedne>

## Lista plikow do usuniecia (z uzasadnieniem per pozycja)
| Sciezka | Typ | Powod sugestii | Wplyw po usunieciu | Odtworzenie/Backup |
|---|---|---|---|---|
| <path-1> | <file/dir> | <konkretna przyczyna> | <niski/sredni/wysoki> | <jak odtworzyc> |
| <path-2> | <file/dir> | <konkretna przyczyna> | <niski/sredni/wysoki> | <jak odtworzyc> |
| <path-3> | <file/dir> | <konkretna przyczyna> | <niski/sredni/wysoki> | <jak odtworzyc> |

## Wplyw
- Ryzyko: <niskie/srednie/wysokie>
- Rollback: <jak przywrocic>

## Akceptacja uzytkownika
- Status: OCZEKUJE
- Decyzja: <TAK/NIE>
- Data: <YYYY-MM-DD HH:mm>
```

## Template 3 - Instrukcja Wdrozeniowa Reorganizacji

```md
# Deployment Instruction - Repo Reorg <Nazwa>

## Komponenty
- Przenoszone: <lista>
- Aktualizowane workflow: <lista>
- Aktualizowane importy: <lista>

## Kolejnosc
1. Commit checkpoint
2. Przeniesienia
3. Korekty sciezek
4. Walidacja (lint/test/smoke)
5. Raport koncowy

## Zakazy
- Brak usuwania bez sekcji ZALECANE KASOWANIE
- Brak usuwania bez akceptacji uzytkownika
```

## Template 4 - Miesieczny Audyt Struktury Repo

```md
# Miesieczny Audyt Repo

## Metryki
- Liczba plikow w root
- Liczba artefaktow tymczasowych
- Liczba ostrzezen sciezek w CI

## Dzialania
- [ ] Przeniesienia dokumentacji
- [ ] Archiwizacja logow
- [ ] Aktualizacja .gitignore
- [ ] Aktualizacja runbookow

## Decyzje
- Co zostaje w root
- Co przechodzi do docs/
- Co jest kandydatem do ZALECANE KASOWANIE
```

## Rekomendowana lokalizacja i uzycie

- Lokalizacja szablonow: `docs/guides/REPO_REORGANIZATION_TEMPLATES.md`
- Referencja z instrukcji wdrozeniowych: dodac link do tego pliku w sekcji governance.
