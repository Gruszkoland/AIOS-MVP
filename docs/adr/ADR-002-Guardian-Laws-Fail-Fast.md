# ADR-002: Fail-fast Guardian Laws — próg 2 naruszeń

**Status:** ZAAKCEPTOWANY
**Data:** 2025-Q4
**Autor:** ADRION Core Team

---

## Kontekst

Jak agresywnie egzekwować etyczne ograniczenia w systemie autonomicznym?

Analizowane opcje:

- **(A) Próg = 1** — blokuj każde pojedyncze naruszenie → bardzo konserwatywny
- **(B) Próg = 2** — blokuj przy ≥2 naruszeniach → balans etyka/użyteczność
- **(C) Tylko log** — nie blokuj, tylko rejestruj naruszenia
- **(D) Ważone prawa** — różna waga dla różnych praw (Critical/High/Medium)

9 Guardian Laws: Unity, Truth, Rhythm, Causality, Transparency, Nonmaleficence, Autonomy, Justice, Sustainability

## Decyzja

**Opcja B: ≥2 naruszeń = MANDATORY DENY**, niezależnie od wyniku Trinity.

```python
# backend/app.py
if compliance < 7:  # (9 - 2) = 7 praw musi przejść
    decision = "DENIED ✗✗✗"
    # Trinity score ignorowany
```

## Konsekwencje

### Plusy

- Odporny na ataki "thin edge wedge" — jedno małe naruszenie nie przejdzie razem z drugim
- Mniej false-positives niż próg=1 → wyższa użyteczność systemu
- Prosto implementowalny i testowalny

### Minusy / Ryzyka

- Jedno KRYTYCZNE naruszenie (np. Nonmaleficence) nie blokuje samodzielnie
- Możliwe, że AI znajdzie "2 drobne naruszenia" które razem są niebezpieczne
- Próg stały — nie adaptuje się do kontekstu

### Przyszłe rozszerzenie (ADR-002b)

Rozważyć ważone prawa:

```
CRITICAL laws (Nonmaleficence) → instant DENY bez względu na liczbę
HIGH laws (Privacy, Justice) → próg = 1
MEDIUM laws (Rhythm, Aesthetics) → próg = 2
```

## Powiązane ADR

- ADR-001: Trinity-EBDI Framework
- `docs/GUARDIAN_LAWS_CANONICAL.json` — single source of truth
