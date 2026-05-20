# MCP Servers Registry — ADRION 369

> Status: PLAN | Wersja: 1.0-draft | Zaktualizowano: 2026-05-20

## Overview

6 MCP microservices zintegrowanych z ekosystemem ADRION 369, dostępne dla Claude Desktop i Claude Code.

| Port | Server   | Rola                              | Status    | Tools | Resources |
|------|----------|-----------------------------------|-----------|-------|-----------|
| 9000 | Router   | Routing, discovery, capability    | PLAN      | 5     | 2         |
| 9001 | Vortex   | EBDI state, digital root, pulse   | PLAN      | 4     | 3         |
| 9002 | Guardian | Guardian Laws, compliance         | PLAN      | 6     | 4         |
| 9003 | Oracle   | Predictions, analysis, scoring    | PLAN      | 5     | 2         |
| 9004 | Genesis  | Records management, audit logs    | PLAN      | 4     | 5         |
| 9005 | Healer   | Self-repair, optimization        | PLAN      | 3     | 3         |

## Zamiarem Implementacji

```
ETAP 1 (Tydzień 1): Szablony + Router MVP
ETAP 2 (Tydzień 2): Vortex + Guardian core
ETAP 3 (Tydzień 3): Oracle + Genesis integration
ETAP 4 (Tydzień 4): Healer + full test suite
```

## Specyfikacja każdego serwera

### 1. Router (Port 9000)
- **Cel:** Centralna bramka, discovery capability, semantic routing
- **Tools:**
  - `discover_agents()` — lista wszystkich agentów + ich capability
  - `route_task()` — semantyczne dopasowanie zadania do agenta
  - `get_capabilities()` — mapowanie domenowe
  - `validate_tool_schema()` — walidacja Input Schema
  - `health_check()` — status wszystkich serwerów
- **Resources:**
  - `agents.json` — rejestr 33 agentów
  - `capability_map.json` — wektorowa mapa kompetencji

### 2. Vortex (Port 9001)
- **Cel:** EBDI state machine, digital root calculator, 174Hz orchestration pulse
- **Tools:**
  - `get_ebdi_state()` — aktualny stan decyzyjny
  - `calculate_digital_root()` — 3-6-9 harmonia
  - `pulse_heartbeat()` — synchronizacja taktowania
  - `estimate_next_state()` — predykcja EBDI
- **Resources:**
  - `ebdi_spec.json` — definicja stanów
  - `trinity_matrix.json` — 3-6-9 mapping
  - `pulse_log.jsonl` — historia taktowania

### 3. Guardian (Port 9002)
- **Cel:** Walidacja Guardian Laws, compliance, security checks
- **Tools:**
  - `evaluate_laws()` — ocena 9 praw wobec decyzji
  - `check_critical_violations()` — DENY/ALLOW
  - `audit_decision()` — ścieżka audytu decyzji
  - `get_law_details()` — szczegóły konkretnego prawa
  - `validate_consent()` — sprawdzenie Privacy (G7)
  - `check_harm_risk()` — Nonmaleficence (G8)
- **Resources:**
  - `GUARDIAN_LAWS_CANONICAL.json` — 9 praw (canonical source of truth)
  - `decisions_audit.jsonl` — log wszystkich decyzji
  - `violations_log.jsonl` — historia naruszeń

### 4. Oracle (Port 9003)
- **Cel:** Predictions, scoring, analysis, confidence levels
- **Tools:**
  - `score_task_confidence()` — 0-100 pewność wykonania
  - `predict_outcome()` — prognoza rezultatu
  - `analyze_risks()` — ocena ryzyka
  - `estimate_tokens()` — koszty LLM
  - `recommend_next_step()` — następny naturalny krok
- **Resources:**
  - `scoring_rules.json` — algorytm scoring'u
  - `prediction_history.jsonl` — historia prognoz
  - `confidence_baseline.json` — baseline dla porównań

### 5. Genesis (Port 9004)
- **Cel:** Records management, archival, immutable audit trail
- **Tools:**
  - `create_record()` — nowy wpis (immutable)
  - `get_record()` — odczyt z weryfikacją
  - `audit_chain()` — ścieżka zmian
  - `export_archive()` — eksport z hash verification
  - `verify_integrity()` — walidacja Merkle tree
- **Resources:**
  - `genesis_records/` — archive folder
  - `hash_chain.json` — łańcuch haszy
  - `access_log.jsonl` — historia dostępów

### 6. Healer (Port 9005)
- **Cel:** Self-repair, optimization, system health
- **Tools:**
  - `diagnose_issue()` — zidentyfikuj problem
  - `suggest_fix()` — rekomendacja naprawy
  - `optimize_query()` — optymalizacja
  - `cleanup_state()` — reset stanu
  - `health_report()` — raport zdrowotniczy
- **Resources:**
  - `known_issues.json` — baza znanych błędów
  - `optimization_patterns.json` — wzory optymalizacji
  - `repair_history.jsonl` — historia napraw

## Następny Krok

Czekam na odpowiedź na pytania wyżej, aby:
1. ✅ Stworzyć `claude_desktop_config.json` (lub VS Code config)
2. ✅ Zaimplementować serwery jako Python/Go microservices
3. ✅ Zaintegować z Docker Compose
