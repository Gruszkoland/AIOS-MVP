# RAPORT AUDYTOWY — Ekosystem 33 Agentów (32 Gemy + Chronos #33)

**Data:** 2026-04-22 | **Tester:** Claude Sonnet 4.6 | **Zakres:** 32 agentów, 12 wymiarów, 12 testów pipeline

---

## EXECUTIVE SUMMARY

| Wymiar | Stan | Dotkniętych |
|---|:---:|:---:|
| Walidacja strukturalna ROPE 2.0 | ✅ 32/32 PASS | — |
| Scorecard weights (100%) | ✅ OK | — |
| Spójność SYSTEM_PAYLOAD (8 pól) | ✅ OK | — |
| Routing niestandarowy | ✅ 0 błędów | — |
| **Modes bez Output:** | 🔴 KRYTYCZNE | 21/32 |
| **Brak input schema** | 🔴 SYSTEMOWE | 28/32 |
| **Brak trigger conditions** | 🔴 SYSTEMOWE | 28/32 |
| **Brak escalation path** | 🔴 SYSTEMOWE | 28/32 |
| Placeholder stubs | ⚠️ HIGH | 3/32 |
| Ubogie negative prompting | ⚠️ MEDIUM | 23/32 |
| Maturity ≤ 2 | ℹ️ LOW | 15/32 |
| Brak output type spec (technical) | ⚠️ MEDIUM | 6/8 |
| Overlap kompetencji bez demarkacji | ⚠️ MEDIUM | 10 par |
| ROPE 2.0→3.0 enterprise gaps | 🔴 ROADMAP | 10 cech |

---

## SEKCJA 1 — LUKI STRUKTURALNE (KRYTYCZNE)

### 1.1 Modes bez Output: — 21/32 agentów

**Problem:** 21 agentów deklaruje tryby pracy (A/B/C/D MODE), ale nie definiuje **formatu wyjściowego** dla każdego trybu. Agent wie *co robić*, ale nie wie *jak musi wyglądać efekt*.

```
PRZYKŁAD — CVA-03 GENERATE_MODE:
❌ OBECNE:  **A. GENERATE_MODE** — tworzysz prompty...
✅ POWINNO: **A. GENERATE_MODE** — tworzysz prompty...
            Output: Markdown z sekcjami: [Prompt], [Negative], [Parameters], [Example].
            Format: ``` blok kodu, max 500 tokenów, język: EN.
```

**Agenty dotknięte (gap ≥ 3):**
MPG(4), CVA(4), LCA(4), SEO(4), EDU(4), VAP(4), CRM(4), KMS(4), HRR(4), PMO(4), TWR(4), PWB(3), CEC(3), UXD(3), DCA(3), SMM(3), CSO(3)

---

### 1.2 Brak Input Schema — 28/32 agentów

**Problem:** Agenci nie deklarują, jakich danych wejściowych **wymagają** od AOR. Skutek: AOR nie może walidować handoffu przed delegacją — przekazuje agentowi niekompletny payload, agent wraca PARTIAL.

```yaml
# Brakujący blok (wzorzec do dodania w sekcji IV.PARAMETERS):
INPUT_SCHEMA:
  required:
    - task_description: string          # min 10 słów
    - context_from_previous: string     # lub BRAK
  optional:
    - target_audience: string
    - format_preference: enum[MD, JSON, HTML]
  validation:
    - if task_description is empty → PARTIAL + [BRAK_DANYCH: task_description]
```

**Agenty OK (input schema zdefiniowane):** MPG, BL, AOR, CRM, QPA

---

### 1.3 Brak Trigger Conditions — 28/32 agentów

**Problem:** AOR musi *wiedzieć* kiedy wywołać agenta. Brak sekcji "Kiedy mnie wywołać" oznacza, że AOR działa na domysłach (lub musi to wynikać wyłącznie z MATRIX_REGISTRY).

```
# Wzorzec do dodania w sekcji II.ROLE lub IV.PARAMETERS:
INVOKE_WHEN:
  - Poprzedni agent zwrócił typ zadania: [content_creation, audit, generation]
  - Słowa kluczowe w compressed_output: ["napisz", "stwórz tekst", "copy"]
  - Pipeline stage: [PRE_DEPLOY, POST_RESEARCH, CONTENT_PHASE]
DO_NOT_INVOKE_WHEN:
  - Zadanie wymaga live data bez dostarczenia datasource
  - maturity_score poprzedniego agenta < 2
```

**Agenty z triggers:** BL, QPA, AOR, SMM, CRM (5/32)

---

### 1.4 Brak Escalation Path — 28/32 agentów

**Problem:** Gdy agent nie może wykonać zadania (FAILED), 28 agentów nie określa co zrobić dalej. Standard AOR mówi "retry lub USER", ale indywidualny agent powinien mieć własną strategię eskalacji.

```
# Wzorzec do dodania:
ESCALATION_PATH:
  on_PARTIAL: retry z [BRAK_DANYCH: X] → czekaj na uzupełnienie → AOR
  on_FAILED:  eskaluj do USER z raportem przyczyny
  on_TIMEOUT: status=PARTIAL + anomaly=[TIMEOUT: exceeded Xs]
  on_CONFLICT: eskaluj do 07-ARB
```

**Agenty z escalation:** ARB, EGO, AOR, TWR (4/32)

---

## SEKCJA 2 — LUKI TREŚCIOWE (HIGH)

### 2.1 Placeholder Stubs — 3 agentów

| Agent | Liczba placeholderów | Lokalizacja |
|:---:|:---:|---|
| 05-SAP | 4 | ROLE, OBJECTIVE, PARAMETERS, EVALUATION — wszystkie kluczowe sekcje puste |
| 01-MPG | 1 | EVALUATION domain scorecard |
| 02-PWB | 1 | EVALUATION domain scorecard |

**SAP to najbardziej krytyczny przypadek** — 4 puste sekcje = agent praktycznie bezużyteczny w runtime mimo PASS w walidatorze (dowód, że walidator mierzy strukturę, nie jakość treści).

---

### 2.2 Ubogie Domain-Specific Negative Prompting — 23/32

**Problem:** Większość agentów ma tylko generyczne negative prompts (`Nie generujesz wyników bez uzasadnienia`, `Nie produkujesz lania wody`). Brakuje zakazów specyficznych dla domeny — np.:

- **CEC (copywriter):** brak zakazu plagiatu, clickbaitu, manipulacyjnych nagłówków
- **HRR (rekrutacja):** brak zakazu dyskryminujących pytań rekrutacyjnych (RODO/art. 22¹ KP)
- **PFT (finanse):** brak zakazu konkretnych rekomendacji inwestycyjnych bez disclaimera
- **EDU (edukacja):** brak zakazu przedstawiania niesprawdzonych teorii jako faktów
- **ROA (OSINT):** brak zakazu wskazywania na dane osobowe bez podstawy prawnej
- **PMO:** brak zakazu generowania harmonogramów bez podania zasobów/budżetu

---

### 2.3 Framework Citations — 2 błędy w danych

| Agent | Brakująca referencja | Impact |
|---|---|---|
| QTE-19 | TDD (Test-Driven Development) | Agent QA bez TDD jest niekompletny |
| SEO-20 | "Technical SEO" jako termin wprost | Mylący — domena mówi o SEO technicznym, agent nie |

---

## SEKCJA 3 — LUKI ARCHITEKTONICZNE (PIPELINE)

### 3.1 User-Facing Output Format — 25/32 brak

Agenty kończące pipeline z `recommended_next_agent: USER` nie definiują **jak ma wyglądać finalny output dla człowieka**. Skutek: każdy agent formatuje "po swojemu" — brak spójnego UX ekosystemu.

```
# Wzorzec USER_FACING_OUTPUT do dodania:
USER_FACING_OUTPUT:
  format: Markdown
  struktura:
    - "## Podsumowanie (max 3 zdania)"
    - "## Wyniki / Deliverables"
    - "## Zalecenia (opcjonalne)"
    - "## Następne kroki"
  tone: [formal | conversational | technical]
  max_length: [tokens lub słowa]
```

---

### 3.2 Routing Loop Risk — ARB ↔ AOR

**Problem:** ARB (#07) i AOR (#13) wzajemnie na siebie wskazują (ARB → AOR → ARB to możliwy cykl gdy AOR nie jest pewny routingu i eskaluje do ARB, który odsyła do AOR).

**Rozwiązanie:** Dodać do ARB explicit: `Na pytania routingowe od AOR: zawsze wydaj werdykt końcowy (GO/NO-GO/ROUTE_TO:[X]) — nie odsyłaj z powrotem do AOR.`

---

### 3.3 Agenty bez trybów pracy (NO MODES) — 4 agentów

| Agent | Problem |
|---|---|
| 05-SAP | Placeholder — sekcja OBJECTIVE pusta |
| 12-ROA | Brak ustrukturyzowanych trybów (ma narrację ale nie formalne MODE bloki) |
| 15-DBI | Jak wyżej |
| 19-QTE | Jak wyżej |

ROA, DBI, QTE to agenty v2.2 (starsze .bak miały tryby) — prawdopodobnie zostały uproszczone podczas migracji.

---

## SEKCJA 4 — LUKI TECHNICZNE (OUTPUT FORMAT)

### 4.1 Brak Output Type Spec — 6 agentów technicznych

| Agent | Problem | Ryzyko |
|---|---|---|
| ROA-12 | Brak formatu raportu OSINT | AOR nie wie jak parsować output |
| DBI-15 | Brak specyfikacji SQL/JSON/tabela | Downstream agent dostaje nieznany format |
| DCA-17 | Brak formatu YAML/Terraform/diagram | Mieszane outputy niemożliwe do handoffu |
| QTE-19 | Brak formatu test report (JUnit/Allure/MD) | QA output niestandardowy |
| SEO-20 | Brak formatu audit report | Niemożliwy handoff do CEC lub TWR |
| CSO-28 | Brak formatu security report (CVSS/tabela) | Niezrozumiały dla downstream agents |

---

## SEKCJA 5 — LUKI KOMPETENCYJNE (OVERLAPS)

### 5.1 Pary z overlappingiem bez demarkacji

| Para | Wspólna domena | Brakująca demarkacja |
|---|---|---|
| SEO-20 ↔ PWB-02 | SEO techniczne | PWB: tylko implementacja kodu SEO; SEO: strategia + audit — potrzebna explicit granica |
| CEC-11 ↔ SMM-24 | Content marketing | CEC: copy standalone; SMM: copy w kontekście kampanii/kalendarza |
| LCA-14 ↔ PFT-27 | Compliance/prawo | LCA: prawo cyfrowe (RODO, IP); PFT: prawo podatkowe — OK ale nie napisane |
| ROA-12 ↔ DBI-15 | Analiza danych | ROA: dane zewnętrzne (open source); DBI: dane wewnętrzne (bazy, SQL) |
| PMO-31 ↔ SAP-05 | Planowanie | SAP: strategia (co); PMO: execution (jak + kiedy) — nie zdefinowane w dokumentach |
| EGO-08 ↔ CSO-28 | Bezpieczeństwo | EGO: etyka AI / alignment; CSO: technical security (infra, code) — granica niejasna |
| KMS-29 ↔ AOR-13 | Context mgmt | AOR: context compression operacyjna; KMS: knowledge base persistence — różne scope |
| PCH-22 ↔ EDU-21 | Rozwój | EDU: nauczanie umiejętności (co); PCH: coaching nawyków (jak) — do wyjaśnienia |
| HRR-30 ↔ PMO-31 | Team | PMO: budowanie procesu; HRR: budowanie zespołu — OK ale musi być w dokumentach |
| CTG-09 ↔ PCH-22 | Soft-skills | CTG: perspektywa archetypowa; PCH: konkretne techniki — zupełnie różne level |

---

## SEKCJA 6 — ROADMAP ROPE 3.0 (ENTERPRISE GAPS)

| Feature | Priorytet | Opis implementacji |
|---|:---:|---|
| `max_retries: N` | 🔴 P1 | Dodać do SYSTEM_PAYLOAD — AOR przerywa loop po N iteracjach |
| `timeout_seconds: N` | 🔴 P1 | Każdy mode ma max czas — AOR flaguje timeout jako PARTIAL |
| `payload_version: "2.0"` | 🔴 P1 | Backward compatibility — AOR może obsłużyć stare formaty |
| `priority: P1/P2/P3` | 🟡 P2 | Queue management gdy wiele agentów czeka |
| `idempotency_key: hash` | 🟡 P2 | Retry-safe — ten sam klucz = nie duplikuj side effects |
| `capability_flags: []` | 🟡 P2 | Explicit: `["code_gen", "analysis", "no_live_data"]` |
| `cost_estimate_tokens: N` | 🟢 P3 | Budget tracking per agent call |
| `audit_log: []` | 🟢 P3 | Structured decision log per session |
| `agent_health: HEALTHY/DEGRADED` | 🟢 P3 | Self-report przy inicjalizacji |
| `deprecation_date: YYYY-MM-DD` | 🟢 P3 | Agent lifecycle management |

---

## SEKCJA 7 — MATURITY ASSESSMENT

### Maturity Score Distribution

| Maturity | Liczba agentów | Agenci |
|:---:|:---:|---|
| 4 (Production-ready) | 3 | CSO, PMO, TWR |
| 3 (Stable) | 14 | MPG, SAP, ARB, EGO, CEC, AOR, LCA, SEO, EDU, SMM, CRM, KMS, HRR, AOR |
| 2 (Draft) | 15 | PWB, CVA, QPA, BL, CTG, ECHO, ROA, DBI, UXD, SNE, QTE, PCH, VAP, TLO, PFT |
| 1 | 0 | — |

15 agentów w stanie Draft (maturity=2) = 47% ekosystemu nie jest gotowe na produkcję.

---

## CHECKLISTA WDROŻENIOWA

### Sprint 1 — Naprawy Krytyczne (P0)

- [ ] **05-SAP**: uzupełnić 4 puste sekcje (ROLE, OBJECTIVE, PARAMETERS, EVALUATION)
- [ ] **01-MPG**: uzupełnić domain scorecard w EVALUATION
- [ ] **02-PWB**: uzupełnić domain scorecard w EVALUATION
- [ ] **ARB**: dodać explicit rule `nie odsyłaj routing queries z powrotem do AOR`
- [ ] **ROA, DBI, QTE**: przywrócić formalne MODE bloki (wzorować na CSO lub DCA)

### Sprint 2 — Output Schemas (P1, 21 agentów)

- [ ] Dodać `Output:` spec do każdego MODE bloku we wszystkich 21 agentach z gap > 0
- [ ] Priorytet: MPG, CVA, LCA, SEO, EDU, VAP, CRM, KMS, HRR, PMO, TWR (gap=4 każdy)
- [ ] Wzorzec: `Output: [format] z sekcjami [A, B, C], max [N] tokenów/słów`

### Sprint 3 — Input Schema + Triggers (P1, systemowe)

- [ ] Dodać `INPUT_SCHEMA` blok do sekcji IV.PARAMETERS dla 28 agentów
- [ ] Dodać `INVOKE_WHEN / DO_NOT_INVOKE_WHEN` blok do sekcji II.ROLE dla 28 agentów
- [ ] Zaktualizować MATRIX_REGISTRY 2.1 o kolumnę trigger keywords

### Sprint 4 — Escalation Paths (P1, 28 agentów)

- [ ] Dodać `ESCALATION_PATH` blok do sekcji IV.PARAMETERS dla 28 agentów
- [ ] Ujednolicić: on_PARTIAL / on_FAILED / on_TIMEOUT / on_CONFLICT

### Sprint 5 — Domain Negative Prompting (P2, 23 agentów)

- [ ] Dodać 2–3 domain-specific negative prompts per agent
- [ ] Priorytet: CEC, HRR, PFT, EDU, ROA, PMO (domain risk najwyższy)

### Sprint 6 — USER_FACING_OUTPUT (P2)

- [ ] Dodać blok `USER_FACING_OUTPUT` do wszystkich 25 agentów kończących na USER
- [ ] Ujednolicić format finalnego raportu dla użytkownika

### Sprint 7 — ROPE 3.0 Roadmap (P3)

- [ ] Zdefiniować specyfikację ROPE 3.0 (max_retries, timeout, payload_version, priority, idempotency_key)
- [ ] Zaktualizować `validate_agents_v2.py` o nowe pola
- [ ] Migracja: 32 agentów → ROPE 3.0 batch update przez `generate_missing_agents.py`

### Ongoing

- [ ] Uzupełnić `<!-- LAST_SYNCED: -->` po każdej zmianie agenta
- [ ] Zdefiniować explicit demarkację dla 10 par overlappingowych w MATRIX_REGISTRY
- [ ] Podnieść maturity_score z 2→3 po uzupełnieniu Sprint 2–4 per agent

---

**Raport wygenerowany przez:** Claude Sonnet 4.6 | **Następna rewizja:** po Sprint 2
