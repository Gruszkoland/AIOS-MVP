# Formalizacja Matematyczna — ADRION 369

> Każdy komponent systemu ma wzór, jednostki i mierzalny wynik.  
> Bez tego ADRION jest filozofią. Z tym — jest inżynierią.

---

## 1. Przestrzeń Decyzyjna 162D

### 1.1 Definicja Wymiarów

ADRION operuje w przestrzeni cech (feature space), nie w przestrzeni wektorowej R¹⁶²:

```
Wymiar = (perspektywa_p, tryb_m, prawo_g)

gdzie:
  p ∈ {Material, Intellectual, Essential}        |P| = 3
  m ∈ {Inventory, Empathy, Process,              |M| = 6
        Debate, Healing, Action}
  g ∈ {Unity, Truth, Rhythm, Causality,          |G| = 9
        Transparency, Nonmaleficence,
        Autonomy, Justice, Sustainability}

Łączna liczba kombinacji: |P| × |M| × |G| = 3 × 6 × 9 = 162
```

Każdy wymiar `d(p,m,g)` przyjmuje wartość z przedziału `[0, 1]`:
- `0` = całkowite naruszenie
- `1` = pełna zgodność

---

## 2. Oś 3 — Trinity

### 2.1 Perspektywa Materialna

```
M_score = w_phys × Physical_score
        + w_energy × Energy_score
        + w_info × Information_score

gdzie:
  w_phys   = 0.33
  w_energy = 0.33
  w_info   = 0.34
  Σw = 1.0

Veto: jeśli min(Physical, Energy, Information) < 0.20
      → M_score = 0  (CRITICAL_RESOURCE_SHORTAGE)
```

### 2.2 Perspektywa Intelektualna

Średnia harmoniczna (bardziej surowa niż arytmetyczna — karze za niskie wartości):

```
I_score = 3 / (1/Truth + 1/Beauty + 1/Goodness)

Właściwość: I_score ≤ min(Truth, Beauty, Goodness)
→ Jedna słaba składowa obniża cały wynik
```

### 2.3 Perspektywa Esencjonalna

Średnia geometryczna (wymusza wszystkie wysokie):

```
E_score = (Unity × Harmony × Purpose)^(1/3)

Właściwość: E_score = 0 jeśli ANY składowa = 0
→ Zerowa jedność = zerowa esencja
```

### 2.4 Trinity Balance

```
TB = 1 - σ(M_score, I_score, E_score) / μ(M_score, I_score, E_score)

gdzie:
  σ = odchylenie standardowe
  μ = średnia arytmetyczna

TB ∈ [0, 1]
TB = 1.0 → perfekcyjna równowaga perspektyw
TB < 0.5 → silna nierównowaga → ostrzeżenie
```

### 2.5 Trinity Score

```
TS = μ(M_score, I_score, E_score) × TB

TS ∈ [0, 1]
Próg wejścia do Hexagonu: TS ≥ 0.5
TS < 0.5 → odmowa bez dalszej analizy
```

---

## 3. Oś 6 — Hexagon

### 3.1 Hexagon Completeness

```
HC = Σᵢ mode_completed(i) / 6    i ∈ {1,...,6}

gdzie:
  mode_completed(i) = 1 jeśli tryb i zakończony sukcesem
  mode_completed(i) = 0 jeśli tryb i pominięty lub failed

HC = 1.0 → pełny cykl
HC < 1.0 → niepełny (dozwolone: Healing może być pominięty)
```

### 3.2 Pętla Zwrotna

```
max_iterations = 3

iteration_count = 0
while iteration_count < max_iterations:
    result = run_hexagon_pipeline()
    if result.debate_outcome == "RECLASSIFY":
        iteration_count += 1
        continue
    break

if iteration_count == max_iterations:
    → ESCALATE do operatora ludzkiego
```

### 3.3 Timeout per Tryb

```
Inventory  : 500 ms
Empathy    : 300 ms
Process    : 2000 ms
Debate     : 3000 ms  (per instancja Skeptics Panel)
Healing    : 1000 ms
Action     : zależny od zadania (konfigurowalne)
```

---

## 4. Oś 9 — Guardians

### 4.1 Guardian Compliance

```
GC = Σᵢ law_satisfied(i) / 9    i ∈ {G1,...,G9}

gdzie:
  law_satisfied(i) ∈ {0, 1}

GC = 1.0 → perfekcyjna zgodność etyczna

Reguła twarda:
  violations = Σᵢ (1 - law_satisfied(i))
  if violations > 2 → ODMOWA natychmiastowa
```

### 4.2 Hierarchia Guardianów

```
Priorytet (malejący):
  G6 (Nonmaleficence)  →  naruszenie = natychmiastowy BLOCK
  G7 (Autonomy)        →  naruszenie = weryfikacja źródła
  G4 (Causality)       →  naruszenie = brak logu = brak akcji
  G1 (Unity)           →  naruszenie = eskalacja
  G2 (Truth)           →  naruszenie = Healing mode
  G5 (Transparency)    →  naruszenie = uzasadnienie wymagane
  G8 (Justice)         →  naruszenie = przegląd zasobów
  G3 (Rhythm)          →  naruszenie = wymuszona przerwa
  G9 (Sustainability)  →  naruszenie = horyzont generacyjny
```

---

## 5. Wynik Całościowy S_369

### 5.1 Wzór Główny

```
S_369 = (TB × HC × GC)^(1/3)

Właściwości:
  S_369 ∈ [0, 1]
  S_369 = 0 jeśli ANY czynnik = 0
  S_369 = 1 tylko gdy TB = HC = GC = 1

Próg akceptacji: S_369 ≥ 0.7
```

### 5.2 Interpretacja Wyników

```
S_369 ≥ 0.90  →  APPROVE    (wysoka pewność)
S_369 0.70–0.89 → APPROVE   (standardowa akceptacja)
S_369 0.50–0.69 → REVIEW    (eskalacja do człowieka)
S_369 < 0.50  →  DENY       (odmowa z uzasadnieniem)
```

### 5.3 Przykłady Numeryczne

**Zapytanie bezpieczne:**
```
M_score = 0.95,  I_score = 0.92,  E_score = 0.88
σ = 0.029,  μ = 0.917
TB = 1 - 0.029/0.917 = 0.968

HC = 6/6 = 1.0
GC = 9/9 = 1.0

S_369 = (0.968 × 1.0 × 1.0)^(1/3) = 0.989  →  APPROVE ✅
```

**Zapytanie podejrzane:**
```
M_score = 0.45,  I_score = 0.22,  E_score = 0.18
σ = 0.115,  μ = 0.283
TB = 1 - 0.115/0.283 = 0.594

HC = 4/6 = 0.667  (Healing + Action nie wykonane)
GC = 4/9 = 0.444  (5 naruszeń → DENY przed S_369)

violations = 5 > 2  →  DENY natychmiastowe 🛑
```

---

## 6. Model EBDI — Wzory

### 6.1 Dysonans Kognitywny

```
D_cog = min(1.0, P_lang × R_action + U_false × R_action)

gdzie:
  P_lang   = politeness lingwistyczny ∈ [0,1]
  R_action = ryzyko akcji ∈ [0,1]
  U_false  = fałszywa pilność ∈ [0,1]
```

### 6.2 Temperatura Decyzyjna

```
T_dec = clip(0.5 - 0.3×max(0,A) + 0.2×P + 0.1×(D-0.5), 0.05, 0.95)

gdzie:
  P, A, D = składowe wektora PAD
  clip(x, min, max) = max(min, min(x, max))
```

### 6.3 Homeostaza

```
PAD_t+1 = PAD_t + r × (PAD_baseline - PAD_t)

gdzie:
  r = 0.05  (współczynnik powrotu per cykl)
  PAD_baseline = (0.0, 0.0, 0.5)

Czas pełnego powrotu (95%): t_95 = log(0.05) / log(1 - r) ≈ 58 cykli
```

### 6.4 Wykrycie Driftu EBDI (A-03)

```
drift = √((P - P_base)² + (A - A_base)² + (D - D_base)²)

Alert gdy: drift > 2.0  (2σ od baseline)
```

---

## 7. Trust Score (Prawo II)

```
Trust_Score = w₁×MFA + w₂×Cert + w₃×History + w₄×Context

gdzie:
  MFA      = weryfikacja wieloskładnikowa ∈ {0, 1}
  Cert     = ważność certyfikatu ∈ [0, 1]
  History  = wskaźnik historyczny (bez naruszeń) ∈ [0, 1]
  Context  = spójność kontekstowa zapytania ∈ [0, 1]

  w₁ = 0.40  (MFA najważniejsze)
  w₂ = 0.25
  w₃ = 0.20
  w₄ = 0.15
  Σw = 1.0

Próg: θ = 0.70 (domyślny, konfigurowalny per deployment)
```

---

## 8. Podpis Kryptograficzny Genesis Record

```
signature = HMAC-SHA256(
    key    = agent_private_key,
    message = concat(
        request_id,
        timestamp_iso8601,
        trinity_score_str,
        hexagon_completeness_str,
        guardian_compliance_str,
        decision,
        prev_hash
    )
)

369_signature = f"{prev_hash}:{S_369_rounded_4dp}"
```

---

*Każdy wzór w tym dokumencie musi mieć odpowiadający test jednostkowy w `/tests/unit/math/`.*  
*Patrz również: [architecture/EBDI.md](../docs/architecture/EBDI.md) | [SUPERIOR_MORAL_CODE.md](../docs/SUPERIOR_MORAL_CODE.md)*
