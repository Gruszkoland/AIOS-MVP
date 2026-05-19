---
title: "VETO Rule — Formalna Definicja"
version: "1.0"
created: "2026-05-19"
author: "ADRION 369 Core Team"
---

# VETO Rule — Algorytm Ewaluacji Decyzji

> Regula VETO jest mechanizmem bezpieczenstwa systemu ADRION 369, ktory blokuje akcje
> o krytycznym ryzyku niezaleznie od pozostalych parametrow.

---

## 1. Definicja Formalna

```python
def evaluate_action(action: Action) -> Decision:
    """
    Kolejnosc ewaluacji (od najwyzszego priorytetu):
    1. VETO check (CRITICAL) - natychmiastowy DENY
    2. HIGH risk  - wymaga 2-agentowej zgody
    3. MEDIUM risk - standardowa ewaluacja
    4. LOW risk   - auto-approve
    """
    # Krok 1: VETO — natychmiastowy DENY dla CRITICAL
    if action.criticality == Criticality.CRITICAL:
        return Decision.DENY  # VETO - brak dalszej ewaluacji

    # Krok 2: HIGH — wymaga konsensusu
    if action.criticality == Criticality.HIGH:
        if not quorum_reached(action, min_agents=2):
            return Decision.PENDING
        return Decision.ALLOW

    # Krok 3: MEDIUM — standardowa ewaluacja Guardian Laws
    if action.criticality == Criticality.MEDIUM:
        return evaluate_guardian_laws(action)

    # Krok 4: LOW — auto-approve
    return Decision.ALLOW
```

---

## 2. Hierarchia Priorytetow

| Priorytet | Poziom krytycznosci | Wynik | Tie-break |
|-----------|--------------------|---------|-----------|
| 1 (najwyzszy) | `CRITICAL` | `DENY` (VETO) | N/A — zawsze DENY |
| 2 | `HIGH` | `PENDING` / `ALLOW` | agent_id (rosnaco) |
| 3 | `MEDIUM` | Guardian Laws | agent_id (rosnaco) |
| 4 (najnizszy) | `LOW` | `ALLOW` | N/A — auto |

### Tie-break (deterministyczny)

Gdy dwa agenty maja identyczny priorytet i sprzeczne rekomendacje:

```python
# Tie-break przez agent_id (deterministyczny, rosnaco)
sorted_agents = sorted(conflicting_agents, key=lambda a: a.agent_id)
winning_agent = sorted_agents[0]  # najnizszy agent_id wygrywa
```

---

## 3. Typy Akcji Objetych VETO

Nastepujace typy akcji automatycznie uzyskuja status `CRITICAL` i sa objete VETO:

```python
CRITICAL_ACTION_TYPES = {
    # Security
    "BYPASS", "REVOKE", "IMPERSONATE",
    # Destructive
    "PURGE", "DESTROY", "RESET",
    # System integrity
    "MODIFY_GUARDIAN_LAWS", "DISABLE_VETO",
    # Industrial (stretch goal)
    "ACTUATE", "WRITE_FIRMWARE",
}
```

> **Uwaga:** Lista `CRITICAL_ACTION_TYPES` jest immutable w runtime.
> Modyfikacja wymaga zatwierdzonego ADR i nowego buildu.

---

## 4. Integracja z security_hardening.py

Regula VETO jest zaimplementowana w `core/security_hardening.py`:
- Klasa: `G8PriorityGuard`
- Metoda: `_assess_action_risk(action)`
- CVC: `_CumulativeViolationCounter` sledzi naruszenia per sesja
- Sortowanie: tie-break przez `agent_id` (fix v5.6, MATH-2.5)

---

## 5. Status

- [x] v5.6 — zaimplementowane w `security_hardening.py`
- [x] Testy: 99/99 passed
- [ ] Redis CVC persistence (roadmap — naprawa resetu przy restartach)
- [ ] Rozszerzenie CRITICAL_ACTION_TYPES o komendy PLC
