# Raport koncowy: Stabilizacja Terminala PowerShell (02-04-2026)

## Co wykonano

- Wprowadzono profil automatyzacji terminala w .vscode/settings.json.
- Ujednolicono taski PowerShell w .vscode/tasks.json do jawnej sciezki powershell.exe.
- Dodano parametry startowe dla niezawodnosci: -NoLogo -NoProfile -ExecutionPolicy Bypass.
- Poprawiono quoting dla taskow opartych o -Command.
- Potwierdzono poprawne wykonanie kluczowych taskow po zmianach.
- Dodano automatyczny walidator standardu taskow PowerShell: scripts/reporting/validate_powershell_tasks.py.
- Podlaczono walidator do bramki ADRION: Local Release Gate (A-11 + Reports).

## Co pozostalo

- Brak krytycznych dzialan blokujacych dla tego incydentu.
- Opcjonalnie: analogiczne ujednolicenie mozna rozszerzyc na nowe taski dodawane w przyszlosci.
- Opcjonalnie: dodac test jednostkowy walidatora dla przypadkow negatywnych.

## Co blokuje

- Nic nie blokuje.

## Rekomendacje kolejnych krokow

1. Dodac krotki standard do README: jak definiowac nowe taski PowerShell.
2. Okresowo uruchamiac task smoke po wiekszych zmianach konfiguracji VS Code.
3. Utrzymywac walidator jako wymagany krok przed release.

## Mikro-streszczenie

- Wykryto zrodlo awarii
- Ujednolicono taski PowerShell
- Dodano bezpieczne argumenty
- Naprawiono blad quoting
- Potwierdzono testy smoke
- Dodano walidator taskow
- Spieto release gate
- Zweryfikowano wynik OK
