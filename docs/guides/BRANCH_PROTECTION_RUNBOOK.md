# Branch Protection Runbook

## Cel
Ustawić obowiązkowe reguły ochrony gałęzi dla `main` i `master`, aby wymusić governance ADRION.

## Wymagane ustawienia
1. Wejdź do GitHub repository settings: Branches.
2. Dodaj lub edytuj ruleset dla `main` i `master`.
3. Włącz opcje:
- Require a pull request before merging.
- Require approvals: minimum 1.
- Dismiss stale pull request approvals when new commits are pushed.
- Require status checks to pass before merging.
- Require branches to be up to date before merging.
- Require conversation resolution before merging.
- Restrict force pushes.
- Restrict deletions.

## Minimalny zestaw status checks
- ADRION 369 Python CI / test
- Rust CI/CD / all-checks
- Repository Governance / governance-checks

## Rekomendacja rozszerzona
- Włączyć CODEOWNERS requirement.
- Włączyć signed commits requirement.
- Włączyć secret scanning push protection.

## Weryfikacja
1. Otwórz testowy PR z celowo uszkodzonym checkiem.
2. Potwierdź blokadę merge.
3. Napraw check i potwierdź, że merge jest dozwolony.
