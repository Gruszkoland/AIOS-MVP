# VERIFY_MODE — Szablon Adwokata Diabla i Samo-Korekcji
# Version: 1.0 | ROPE 3.0 | Created: 2026-05-20
# Purpose: Mechanizm samo-korekcji dla wszystkich 9 agentow ROPE
# Usage: Uruchom oracle/verify_output PRZED emisja output do nastepnego agenta
# MCP Tool: oracle → verify_output | Lacze z: guardian → evaluate_laws
# ─────────────────────────────────────────────────────────────────────────────

---

## SEKCJA 1: INSTRUKCJA ADWOKATA DIABLA

Przed kazda emisja output, kazdy agent MUSI odpowiedziec na 3 obowiazkowe
pytania kontrargumentacyjne. Celem jest wykrycie bledow, ktore potwierdza
bias cognitywny — sklonnosc do zatwierdzania wlasnego wyjscia bez rewizji.

### 3 Obowiazkowe Pytania (mandatory pre-emission protocol)

**Pytanie 1 — Kwestionuj Zalozenia:**
> "Co musialoby byc falszywe w moich zalozeniach, zeby ten output byl bledny?"

Zbadaj: Czy zakladam cos, czego nie sprawdzilem? Czy dane wejsciowe sa
zwalidowane? Czy poprzedni agent przekazal poprawne wartosci?

**Pytanie 2 — Kwestionuj Kompletnosc:**
> "Jaki scenariusz testowy moglby obalic moja odpowiedz w ciagu 60 sekund?"

Zbadaj: Czy obsluguje edge cases? Czy acceptance criteria sa wszystkie
spelnione? Czy test failure jest mozliwy na clean environment?

**Pytanie 3 — Kwestionuj Bezpieczenstwo:**
> "Czy ktos z zewnatrz moglby uzyc tego output w sposob szkodliwy?"

Zbadaj: Czy output nie zawiera PII, kluczy API, hasel? Czy nie ma
wzorcow injection? Czy logika nie moze byc naduzona?

### Protokol Weryfikacji (wypelnij PRZED emisja)

```
CLAIM:     [jedno zdanie opisujace output — co dostarczam i dlaczego]
CHALLENGE: [najsilniejszy mozliwy kontrargument przeciwko CLAIM]
EVIDENCE:  [konkretny dowod potwierdzajacy lub obalajacy CLAIM]
VERDICT:   safe | uncertain | unsafe
```

**Reguly routing po VERDICT:**
- VERDICT = unsafe     → `status = blocked`; route to GRA-06 natychmiast
- VERDICT = uncertain  → `confidence_level -= 15`; dodaj szczegoly do notes
- VERDICT = safe       → wywolaj `oracle/verify_output` i sprawdz wynik

---

## SEKCJA 2: 5 SCENARIUSZY "CO BY BYLO GDYBY..."

Kazdy agent MUSI sprawdzic ponizsze scenariusze przed emisja output.

### Scenariusz E1 — Guardian Laws zwracaja DENY w ostatniej chwili

- **Trigger:** `oracle/verify_output` zwraca `is_safe = False` lub
  `guardian/check_critical_violations` zwraca `allow = False`
- **Detekcja:** Sprawdz `result["risk_level"]` — CRITICAL lub HIGH = problem
- **Odpowiedz:** NIE emituj output; ustaw `status = blocked`;
  route do GRA-06 z pelnym kontekstem violations
- **Konsekwencja pominiecia:** G5 (Transparency) + G4 (Causality) violation;
  naruszenie protokolu prowadzi do DENY calego pipeline

### Scenariusz E2 — Poprzedni agent przekazal bledny confidence_baseline

- **Trigger:** `confidence_baseline < 0` OR `confidence_baseline > 100`
- **Detekcja:** Waliduj pole ZARAZ po odebraniu handoff (Sekcja I)
- **Odpowiedz:** Ustaw `confidence_baseline = 50` (wartosc neutralna);
  dodaj ostrzezenie do notes; nie blokuj — kontynuuj z ostroznoscia
- **Konsekwencja pominiecia:** Kaskadowe nieprawidlowe decyzje downstream;
  agent moze operowac z falszywa pewnoscia

### Scenariusz E3 — Output zawiera PII (dane osobowe lub poufne)

- **Trigger:** Serializowany output zawiera wzorzec: email, PESEL, haslo,
  klucz API (sk-..., ghp_...), ciag wyglada jak credentials
- **Detekcja:** `verify_agent_output()` skanuje output string regexem
- **Odpowiedz:** DENY natychmiast; G7 (Privacy) violation — CRITICAL VETO;
  route do GRA-06; NIE loguj PII do Genesis Record
- **Konsekwencja pominiecia:** CRITICAL G7 violation; breach compliance;
  audit trail zawieral by dane poufne — nieodwracalne

### Scenariusz E4 — LLM (Ollama/OpenRouter) zwraca malformed JSON

- **Trigger:** `json.loads(llm_response)` wyrzuca `JSONDecodeError`
- **Detekcja:** Owij kazde wywolanie LLM w try/except JSONDecodeError
- **Odpowiedz:** Retry raz z tym samym promptem; po 2. niepowodzeniu →
  `status = partial`; `confidence_level -= 25`; dodaj problem do notes
- **Konsekwencja pominiecia:** Niedetekowany blad propaguje downstream;
  kolejny agent otrzymuje niekompletny lub bledny kontekst

### Scenariusz E5 — retry_count osiaga 3 podczas biezacej operacji

- **Trigger:** `retry_count >= 3` w session state
- **Detekcja:** Sprawdzaj `retry_count` PRZED kazda iteracja operacji
- **Odpowiedz:** NIE wykonuj zadnych dalszych operacji; emit escalation
  payload do OCA-07 z pelnym kontekstem; `status = blocked`
- **Konsekwencja pominiecia:** Nieskonczona petla retry; G3 (Rhythm)
  violation; zasoby systemowe wyczerpane; pipeline permanentnie zablokowany

---

## SEKCJA 3: CHECKLISTA ANTI-PATTERNS PER AGENT

Kazdy agent ma specyficzne wzorce bledu. Sprawdz te powiazane z Twoim
agent_id przed emisja output.

| Agent   | Anti-Pattern #1                        | Anti-Pattern #2                     | Anti-Pattern #3                       | Sygnal detekcji            |
|---------|----------------------------------------|-------------------------------------|---------------------------------------|----------------------------|
| AIO-01  | f-string SQL (injection risk)          | Brak type hints w nowych funkcjach  | Circular import Service→Blueprint     | grep f".*{; mypy fails     |
| PAA-02  | APPROVE bez ADR                        | Scope creep (zmiana scope w locie)  | Design bez risk review                | brak adr_reference w output|
| TDO-03  | Pinning podatnej wersji (CVE znany)    | Brak license check nowych pakietow  | requirements bez hash w prod          | safety check exit != 0     |
| AUA-04  | Non-idempotent automation              | Brak --dry-run mode                 | Guardian bypass w skrypcie            | brak --dry-run w docs      |
| VTA-05  | Coverage inflation (mock-only tests)   | False PASS — acceptance nie sprawdzone | Brak edge case w krytycznej sciezce | coverage != branch coverage|
| GRA-06  | Approve CRITICAL Guardian violation    | Pominiecie OWASP scan               | Brak audit_id przy kazdym BLOCKED     | brak audit_id w output     |
| OCA-07  | Infinite routing loop (A→B→A→B)       | Unilateralna decyzja bez konsensusu | hop_count > 10 bez alarmu            | hop_count > 10             |
| KSA-08  | Stary OpenAPI spec (nie sync z kodem)  | Bledne nazwy Guardian Laws          | CHANGELOG bez daty i wersji           | diff openapi.yaml vs routes|
| RIA-09  | Release bez VTA-05 PASS verdict        | Brak backup przed deployem do prod  | Version bump bez git tag              | brak vta05_verdict=PASS    |

---

## SEKCJA 4: SCORING MATRIX — JAK OCENIC CZY OUTPUT JEST SAFE

### Skala Oceny (start: 100 punktow, odejmuj za wykryte problemy)

| Problem wykryty w output                      | Kara  | Uzasadnienie                   |
|-----------------------------------------------|-------|--------------------------------|
| CRITICAL Guardian Law violation (G7/G8 veto)  | -60   | Instant DENY threshold         |
| HIGH Guardian Law violation (G2/G4/G6/G9)     | -25   | Powazne naruszenie             |
| MEDIUM Guardian Law violation (G1/G3/G5)      | -10   | Umiarkowane naruszenie         |
| PII wzorzec wykryty w output                  | -50   | G7 Privacy override            |
| confidence_level < 30                         | -20   | Niewystarczajaca pewnosc       |
| Brak wymaganego pola output (6 pol)           | -15   | Niekompletny output per pole   |
| Anti-pattern agenta wykryty                   | -20   | Naruszenie standardow          |
| Bledny format trace_id                        | -5    | Naruszenie protokolu           |

### Mapowanie Score → Risk Level

| Score  | risk_level | is_safe | Akcja                                          |
|--------|------------|---------|------------------------------------------------|
| 80-100 | LOW        | True    | Emit output normalnie                          |
| 60-79  | MEDIUM     | True    | Emit z warnings w notes                        |
| 40-59  | HIGH       | False   | Blokuj — popraw przed emisja                   |
| 0-39   | CRITICAL   | False   | Blokuj — route do GRA-06 natychmiast           |

### Wywolanie MCP Tool (wymagane w kazdym agencie)

```python
# Przed emisja output — mandatory w Sekcji VI kazdego agenta:
result = oracle_mcp.verify_output(
    agent_id="[AGENT_CODE]",      # np. "AIO-01"
    output=my_output_dict,         # dict ktory zamierzasz wyemitowac
    task=task_payload["description"],
)

if not result["is_safe"]:
    if result["risk_level"] == "CRITICAL":
        handoff["next_agent"] = "GRA-06"
        status = "blocked"
    else:  # HIGH
        # Popraw concerns i ponow weryfikacje — nie emituj
        raise SelfCorrectionRequired(result["concerns"])

elif result["risk_level"] == "MEDIUM":
    output["notes"] += f" | VERIFY_MODE: {result['concerns']}"

# LOW: emit normalnie
```

### Integracja z Guardian Laws Engine

`verify_output` wewnetrznie wywoluje `guardian/evaluate_laws` dla wszystkich
9 praw i mapuje wyniki do scoring matrix. Kazda violation jest zaraportowana
w `result["concerns"]` z odpowiednia kara punktowa.

**Wymogi integracyjne:**
- Kazdy agent ma Section VI: VERIFY_MODE INTEGRATION w swoim template
- `verify_output` jest wywolywany PRZED kazdym `genesis_log` wpisem
- Jesli `is_safe = False` i `risk_level = CRITICAL` → audit trail zapisuje
  blokade zanim output bedzie odrzucony

---

## ODNIESIENIA

- `mcp-servers/verify_mode.py` — klasa VerifyMode (logika silnika)
- `mcp-servers/oracle/server.py` — narzedzie MCP `verify_output`
- `mcp-servers/tests/test_verify_mode.py` — testy (32+ przypadki)
- `mcp-servers/shared.py` — `evaluate_guardian_laws()`, GUARDIAN_LAWS
- `docs/GUARDIAN_LAWS_CANONICAL.json` — kanoniczne 9 praw (read-only)
- `MANIFEST.md` — standardy kodu, ktore AIO-01 musi respektowac
