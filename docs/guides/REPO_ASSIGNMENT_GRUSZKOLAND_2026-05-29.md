# Repo Assignment - Gruszkoland (2026-05-29)

## 1. Status zapisania zmian (AIOS-MVP root)
- Nie wszystkie pliki z sesji sa zapisane.
- Wystepuja niezacommitowane zmiany w repo glownym i w zagniezdzonych repo.

## 2. Przyporzadkowanie folderow do repozytoriow

### Potwierdzone przez local origin
- `.` -> `Gruszkoland/AIOS-MVP`
- `PROJEKTY/adrion-369` -> `Gruszkoland/adrion-369`
- `PROJEKTY/adrion-369-architecture` -> `Gruszkoland/adrion-architecture` (nazwa repo inna niz folder)
- `PROJEKTY/adrion-mcp-servers` -> `Gruszkoland/adrion-mcp-servers`
- `PROJEKTY/adrion-template-demo` -> `Gruszkoland/adrion-template-demo`

### Dopasowane po nazwie do profilu Gruszkoland (wymaga potwierdzenia origin)
- `PROJEKTY/adrion-deploy` -> `Gruszkoland/adrion-deploy`
- `PROJEKTY/embedding-ab-test-framework` -> `Gruszkoland/embedding-ab-test` (rozne nazwy)
- `PROJEKTY/leadgen-comet-pipeline` -> `Gruszkoland/leadgen-comet` (rozne nazwy)
- `PROJEKTY/kyc-provider-integration-guide` -> `Gruszkoland/kyc-provider-guide` (rozne nazwy)
- `PROJEKTY/Consultacja-Wielomodelowa-AI` -> `Gruszkoland/consultacao-ai` (rozne nazwy)
- `PROJEKTY/Punkt odniesienia` -> `Gruszkoland/punkt-odniesienia` (rozne nazwy)
- `PROJEKTY/n8n-produkcja` -> `Gruszkoland/n8n-workflows-prod` (rozne nazwy)

### Inne repo niewchodzace do profilu Gruszkoland
- `docs/starlight-template` -> `withastro/starlight`

## 3. Blokery techniczne
Dla czesci repo wystapila blokada `dubious ownership` i nie mozna bylo odczytac origin bez dodania safe.directory.

## 4. Zalecenie wykonawcze
1. Potwierdzic safe.directory dla zablokowanych katalogow.
2. Odczytac origin i zaktualizowac mapowanie z "dopasowane po nazwie" na "potwierdzone".
3. Przenosic pliki miedzy repo dopiero po potwierdzeniu origin, aby uniknac pomylki.
