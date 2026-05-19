# ADR-001: Trinity-EBDI jako rdzeń frameworku decyzyjnego

**Status:** ZAAKCEPTOWANY
**Data:** 2025-Q3
**Autor:** ADRION Core Team

---

## Kontekst

Potrzeba autonomicznego systemu podejmowania decyzji, który jest jednocześnie:

- etyczny (wymóg biznesowy B1)
- zasobowo efektywny (wymóg B4)
- audytowalny (wymóg B3)

Klasyczne podejścia:

- **ML classifier** — brak kontekstu etycznego, black box, trudne do audytu
- **Rule engine** — sztywne reguły, niemożliwe do uogólnienia
- **LLM prompt** — niestabilne, podatne na prompt injection, brak struktury

## Decyzja

Implementacja 3-stopniowego frameworku 162D:

```
Request → Trinity (3 perspektywy równolegle)
        → Hexagon (6 trybów sekwencyjnie)
        → Guardians (9 praw sekwencyjnie)
        → Decision (APPROVED/DENIED)
```

**Trinity:**

- `Material` — ocena zasobów (CPU/RAM/GPU via psutil)
- `Intellectual` — logiczna poprawność (harmonic mean — wszystkie muszą przejść)
- `Essential` — zgodność z celem (geometric mean — wszystkie muszą być wysokie)

**Hexagon:**
Inventory → Empathy → Process → Debate → Healing → Action

**Guardians:**
9 praw etycznych; ≥2 naruszeń = MANDATORY DENY

## Konsekwencje

### Plusy

- Każda decyzja jest explicite etycznie walidowana
- Pełna audytowalność (każdy etap logowany w Genesis Record)
- Fail-fast: błąd Trinity zatrzymuje pipeline przed Hexagon
- Deterministyczne: te same dane = ten sam wynik

### Minusy / Ryzyka

- Latency: min. 3 pełne etapy zawsze — brak "fast path" dla trywialnych requestów
- Złożoność onboarding: nowi deweloperzy muszą zrozumieć filozofię 3-6-9
- ⚠️ **DŁUG**: obecna implementacja to SIMULACJA — ML scoring nie jest podłączony

## Powiązane ADR

- ADR-002: Fail-fast Guardian Laws
- ADR-003: Local-first LLM

## Kamień milowy

M3 (Brama danych) — rzeczywista implementacja Trinity scoring
