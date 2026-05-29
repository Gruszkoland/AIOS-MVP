# Git History Artifact Purge Plan (Non-Destructive Preparation)

Typ dokumentu: How-to + runbook

## Cel

Przygotowac bezpieczny plan usuniecia historycznych artefaktow (`*.db`, duze binaria) z historii Git bez wykonania kroku destrukcyjnego na tym etapie.

## Zakres

- Inwentaryzacja obiektow do potencjalnego purge.
- Backup i checkpoint przed operacja.
- Procedura execution-only-after-approval.

## Krok 1 - Inwentaryzacja (read-only)

1. Wykonaj liste podejrzanych obiektow:
   - `git rev-list --objects --all | findstr /R /I "\.db$ \.(zip|tar|gz|7z)$"`
2. Zweryfikuj rozmiary:
   - `git verify-pack -v .git/objects/pack/*.idx | sort /R /+20`
3. Zapisz wynik do raportu audytowego.

## Krok 2 - Checkpoint i backup

1. Utworz tag checkpoint:
   - `git tag pre-history-purge-YYYYMMDD`
2. Wykonaj backup mirror:
   - `git clone --mirror <repo-url> ../AIOS-MVP-backup-mirror.git`
3. Potwierdz integralnosc backupu (`git fsck`).

## Krok 3 - Dry-run plan

1. Przygotuj wariant `git-filter-repo` (preferowany):
   - usuniecie wzorcow: `*.db`, `coverage/*`, tymczasowe artefakty.
2. Przygotuj wariant awaryjny BFG Repo-Cleaner.
3. Udokumentuj przewidywany zakres zmian (liczba commitow, obiektow, branchy).

## Krok 4 - Approval gate (wymagane)

Warunek uruchomienia kroku destrukcyjnego:

- jawna zgoda wlasciciela repo,
- zatwierdzony plan rollback,
- potwierdzony backup mirror.

Bez spelnienia tych trzech warunkow operacja purge nie jest wykonywana.

## Krok 5 - Execution (po akceptacji)

1. Wykonaj purge na branchu serwisowym.
2. Uruchom walidacje integralnosci i smoke test.
3. Wymus push tylko po osobnym sign-off.

## Rollback

1. Odtworz wskazania z tagu `pre-history-purge-YYYYMMDD`.
2. W razie potrzeby odtworz z mirror backup.
3. Przywroc branch protection i normalny workflow.

## Status

- Etap: Prepared only (non-destructive)
- Wykonanie purge: BLOCKED until explicit approval
