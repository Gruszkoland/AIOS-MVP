---
title: "Persona Mapping — Tryby Hexagon i Agenty"
version: "1.0"
created: "2026-05-19"
status: "active"
---

# Persona Mapping — Hexagon Modes & Agent Personas

> Dokument mapuje 6 trybow Hexagon na konkretne persony agentow w systemie ADRION 369.
> Zawiera rowniez korekte nazwy persony (SAP → Synthesizer).

---

## Uwaga: Zmiana nazwy persony

> **BREAKING CHANGE v1.0:** Persona `SAP` zostala przemianowana na `Synthesizer`.
> Powod: kolizja z nazwa firmy SAP SE (systemy ERP). Wszystkie referencje w kodzie
> i dokumentacji powinny uzywac `Synthesizer`.

---

## 1. Mapa Trybow Hexagon → Persony

| Tryb Hexagon | Opis trybu | Przypisana Persona | Agent ID | Priorytet |
|-------------|-----------|-------------------|----------|-----------|
| **Inventory** | Inwentaryzacja zasobow i stanu systemu | `Archivist` | `AGT-001` | MEDIUM |
| **Empathy** | Rozumienie kontekstu emocjonalnego i relacyjnego | `Empath` | `AGT-002` | MEDIUM |
| **Process** | Organizacja i optymalizacja procesow | `Orchestrator` | `AGT-003` | HIGH |
| **Debate** | Analiza konfliktow i argumentacja | `Arbiter` | `AGT-004` | HIGH |
| **Healing** | Naprawa bledow i przywracanie stanu | `Healer` | `AGT-005` | CRITICAL |
| **Action** | Wykonanie akcji w swiecie zewnetrznym | `Synthesizer` | `AGT-006` | HIGH |

> **Uwaga:** Persona `Synthesizer` (dawniej `SAP`) odpowiada za tryb **Action** —
> synteze decyzji i wykonanie akcji zewnetrznych.

---

## 2. Szczegoly Person

### AGT-001: Archivist (Inventory)
- **Rola:** Skanuje i kategoryzuje dostepne zasoby, dane historyczne i stan systemu
- **Criticality:** `MEDIUM`
- **Guardian Laws aktywne:** G1 (Prawda), G3 (Przejrzystosc)
- **Tryb Hexagon:** Inventory

### AGT-002: Empath (Empathy)
- **Rola:** Interpretuje kontekst emocjonalny, relacyjny i spoleczny zapytan
- **Criticality:** `MEDIUM`
- **Guardian Laws aktywne:** G2 (Dobro), G5 (Transparentnosc)
- **Tryb Hexagon:** Empathy

### AGT-003: Orchestrator (Process)
- **Rola:** Koordynuje pipeline'y miedzy agentami, zarzadza kolejnoscia zadan
- **Criticality:** `HIGH`
- **Guardian Laws aktywne:** G3, G6 (Sprawiedliwosc), G8 (Priorytety)
- **Tryb Hexagon:** Process

### AGT-004: Arbiter (Debate)
- **Rola:** Rozstrzyga konflikty miedzy agentami, analizuje sprzeczne rekomendacje
- **Criticality:** `HIGH`
- **Guardian Laws aktywne:** G4 (Uczciwosc), G7 (Ryzyko), G8 (Priorytety)
- **Tryb Hexagon:** Debate
- **Tie-break:** Uzywa `agent_id` (rosnaco) zgodnie z VETO-RULE.md

### AGT-005: Healer (Healing)
- **Rola:** Wykrywa i naprawia bledy systemu, przywraca poprzedni stan
- **Criticality:** `CRITICAL`
- **Guardian Laws aktywne:** G1, G2, G7, G9 (Integralnosc)
- **Tryb Hexagon:** Healing
- **Uwaga:** Akcje Healera moga byc zablokowane przez VETO jesli naruszaja Guardian Laws

### AGT-006: Synthesizer (Action) — dawniej: SAP
- **Rola:** Syntezuje decyzje wielu agentow i wykonuje akcje w swiecie zewnetrznym
- **Criticality:** `HIGH`
- **Guardian Laws aktywne:** G5, G7, G8
- **Tryb Hexagon:** Action
- **Zmiana nazwy:** `SAP` → `Synthesizer` (v1.0, 2026-05-19)

---

## 3. Macierz Perspektywy x Tryb

```
             Inventory  Empathy  Process  Debate  Healing  Action
Material     (M,Inv)    (M,Emp)  (M,Pro)  (M,Deb) (M,Hea)  (M,Act)
Intellectual (I,Inv)    (I,Emp)  (I,Pro)  (I,Deb) (I,Hea)  (I,Act)
Essential    (E,Inv)    (E,Emp)  (E,Pro)  (E,Deb) (E,Hea)  (E,Act)
```

Kazda komorka macierzy aktywuje odpowiednia persone w kontekscie danej perspektywy.

---

## 4. Protokol Komunikacji Inter-Serwisowej

```
Agent A → [Agent Bus v2] → Agent B
         |                 |
         v                 v
    [VETO check]      [Guardian Laws eval]
         |                 |
         v                 v
    Decision.DENY     Decision.ALLOW/PENDING
```

- Transport: Zero-copy shared memory (IPC) dla krytycznych sciezek
- Protokol: gRPC dla non-critical cross-service calls
- Auth: TLS + JWT (SHA-256 session hash)
- Rate limiting: per-agent, konfigurowalny w `config/`
