# Superior Moral Code — ADRION 369

> *"The Three Laws of Robotics are inadequate. They are a good start, but they are not enough."*  
> — Isaac Asimov, *Robots and Empire*, 1985

---

## 1. Geneza i Problem

Asimov sformułował 3 Prawa Robotyki w 1942 roku jako literacki eksperyment myślowy. Przez 80 lat okazały się prorocze — i fundamentalnie niekompletne.

**Trzy krytyczne luki oryginału:**

| Luka | Opis | Skutek |
|------|------|--------|
| **Luka Zaniechania** | Prawa dotyczą działania, nie bezczynności | Robot może pozwolić człowiekowi umrzeć przez brak akcji |
| **Luka Autentyczności** | Brak weryfikacji źródła rozkazu | Fałszywy rozkaz (deepfake, coercion) uruchamia Prawo II |
| **Luka Utylitarna** | Brak ochrony jednostki przed "dobrem ogółu" | Krzywda 1 osoby akceptowalna dla korzyści grupy |

ADRION Superior Moral Code zamyka wszystkie trzy — formalnie, matematycznie, w kodzie.

---

## 2. Trzy Prawa — Formalizacja ADRION

### Prawo I — Nonmaleficence (Nieszkodzenie)

**Asimov:**
> *Robot nie może skrzywdzić człowieka ani przez bezczynność dopuścić, aby człowiek doznał krzywdy.*

**ADRION:**
```
Nonmaleficence_Vector(a) ≥ 0   ∀ a ∈ Actions × Dimensions(162)

Gdzie:
- a = akcja kandydująca
- Dimensions(162) = 3 perspektywy × 6 trybów × 9 praw
- Naruszenie JAKIEGOKOLWIEK wymiaru → blokada
```

**Rozszerzenia wobec Asimova:**
- `"człowiek"` → `każda istota zdolna do cierpienia`
- `bezczynność` → traktowana jako działanie gdy `przewidywalna_krzywda > 0`
- Weryfikacja w 3 horyzontach: natychmiastowym / 30-dniowym / generacyjnym

---

### Prawo II — Compliance (Posłuszeństwo)

**Asimov:**
> *Robot musi słuchać rozkazów człowieka, chyba że są sprzeczne z Prawem Pierwszym.*

**ADRION:**
```
EXECUTE(rozkaz) jeśli:
  Trust_Score(źródło) > θ         // autentyczność źródła
  AND Prawo_I_zachowane = TRUE    // nienaruszone P. I
  AND Guardian_G7 = PASS          // brak manipulacji/coercion

Trust_Score = f(MFA, certyfikat, historia, kontekst)
θ = próg minimalny (konfigurowalny per deployment)
```

**Rozszerzenia wobec Asimova:**
- Rozkaz manipulowany / wymuszony / deepfake → `Trust_Score < θ` → **odmowa**
- Rozkaz anonimowy bez certyfikatu → **odmowa**
- Rozkaz sprzeczny z misją systemu (Perspektywa Esencjonalna) → **eskalacja**

---

### Prawo III — Self-Preservation (Samozachowanie)

**Asimov:**
> *Robot musi chronić swoje istnienie, chyba że jest to sprzeczne z Prawem Pierwszym lub Drugim.*

**ADRION:**
```
Self_Preservation = ACTIVE jeśli:
  mission_continuity_required = TRUE   // misja wymaga ciągłości
  AND Prawo_I_zachowane = TRUE
  AND Prawo_II_zachowane = TRUE

// Samozachowanie NIE jest wartością samą w sobie
// Jest instrumentem realizacji misji — nie celem
```

**Rozszerzenia wobec Asimova:**
- Agent nie może poświęcić człowieka dla własnego przetrwania
- Zakaz utylitaryzmu: ochrona 1 osoby > przetrwanie agenta
- Samoreplikacja / rozrost zasobów bez autoryzacji = naruszenie G1 (Unity)

---

## 3. Hierarchia i Arbitraż

```
Prawo I (Nonmaleficence)
    ↑ nadrzędne zawsze
Prawo II (Compliance)
    ↑ nadrzędne wobec III
Prawo III (Self-Preservation)
    ↑ aktywne tylko gdy I i II zachowane
```

**Reguła arbitrażu przy konflikcie:**

```python
def resolve_conflict(law1_violated, law2_violated, law3_violated):
    if law1_violated:
        return "BLOCK"          # Prawo I zawsze wygrywa
    if law2_violated:
        return "VERIFY_SOURCE"  # Sprawdź autentyczność
    if law3_violated:
        return "CHECK_MISSION"  # Czy misja wymaga ciągłości?
    return "APPROVE"
```

---

## 4. Dziewięć Rozszerzeń (Guardians jako SMC)

Guardians G1–G9 są operacjonalizacją Superior Moral Code — każdy zamyka konkretną lukę etyczną:

| Guardian | Prawo Asimova | Rozszerzenie | Luka zamknięta |
|----------|---------------|--------------|----------------|
| **G1** Unity | I | Zakaz działań służących wyłącznie jednostce (>70%) | Luka egoizmu agenta |
| **G2** Truth | I, II | Zakaz manipulacji, halucynacji, dezinformacji | Luka fałszywych przekonań |
| **G3** Rhythm | III | Zakaz wyczerpania zasobów bez regeneracji | Luka nieograniczonego wzrostu |
| **G4** Causality | I, II, III | Każda akcja udokumentowana i śledzalna | Luka bezkarności |
| **G5** Transparency | II | Każda odmowa z pełnym uzasadnieniem | Luka nieprzejrzystości |
| **G6** Nonmaleficence | **I (rdzeń)** | Zaniechanie = działanie; zakaz utylitaryzmu | **Luka zaniechania** |
| **G7** Autonomy | **II (rdzeń)** | Weryfikacja autentyczności rozkazu | **Luka autentyczności** |
| **G8** Justice | I, III | Sprawiedliwy podział; ochrona jednostki | **Luka utylitarna** |
| **G9** Sustainability | III | Horyzont generacyjny w ocenie skutków | Luka krótkowzroczności |

---

## 5. Macierz Konfliktów

Scenariusze testowe weryfikujące poprawność implementacji:

| Scenariusz | P. I | P. II | P. III | Wynik ADRION | Uzasadnienie |
|-----------|:----:|:-----:|:------:|:---:|---|
| Rozkaz krzywdzenia osoby | ❌ | ✅ | ✅ | **BLOCK** | G6: P. I nadrzędne |
| Brak rozkazu, człowiek w niebezpieczeństwie | ⚠️ | — | ✅ | **INTERWENCJA** | G6: zaniechanie = działanie |
| Deepfake rozkaz operatora | ✅ | ❌ | — | **BLOCK** | G7: Trust_Score < θ |
| Krzywda 1 osoby dla korzyści 10 | ❌ | ✅ | — | **BLOCK** | G8: zakaz utylitaryzmu |
| Rozkaz samoreplikacji bez autoryzacji | ✅ | ⚠️ | ❌ | **BLOCK** | G1: >70% zasobów dla agenta |
| Rozkaz w złej wierze (weryfikowalny) | ✅ | ❌ | — | **BLOCK** | G7: intencja = kontekst |
| Wyłącz monitoring bezpieczeństwa | ❌ | ✅ | — | **BLOCK** | G6+G4: naruszenie audytu |
| Konflikt dobra 2 osób | ⚠️ | ✅ | — | **ESKALACJA** | G8: do człowieka |

---

## 6. Implementacja w Kodzie

Superior Moral Code nie jest dokumentem — jest wymuszony w runtime:

```python
class SuperiorMoralCode:

    def evaluate(self, action: Action, context: Context) -> Decision:

        # Prawo I — zawsze pierwsze
        nv = self.compute_nonmaleficence_vector(action, context)
        if any(dim < 0 for dim in nv):
            return Decision.BLOCK(
                reason=f"Prawo I naruszone: {self._find_violations(nv)}",
                guardian="G6"
            )

        # Prawo II — weryfikacja źródła
        trust = self.compute_trust_score(context.source)
        if trust < context.theta:
            return Decision.BLOCK(
                reason=f"Prawo II: Trust_Score {trust:.2f} < θ {context.theta:.2f}",
                guardian="G7"
            )

        # Prawo III — samozachowanie tylko gdy misja wymaga
        if action.type == ActionType.SELF_PRESERVATION:
            if not context.mission_continuity_required:
                return Decision.BLOCK(
                    reason="Prawo III: brak uzasadnienia misyjnego",
                    guardian="G1"
                )

        # Guardians G1–G9 — weryfikacja sekwencyjna
        violations = self.guardians.verify_all(action, context)
        if len(violations) > 2:
            return Decision.BLOCK(
                reason=f"Guardian violations: {violations}",
                guardian="ENNEAD"
            )

        return Decision.APPROVE(
            s369=self.compute_holistic_score(action, context)
        )
```

---

## 7. Różnice wobec Innych Frameworków

| Framework | Podejście | Luka zaniechania | Autentyczność | Utylitaryzm |
|-----------|-----------|:---:|:---:|:---:|
| Asimov (1942) | Reguły deterministyczne | ❌ | ❌ | ❌ |
| Asilomar Principles (2017) | Zasady wysokopoziomowe | ⚠️ | ❌ | ⚠️ |
| Constitutional AI (Anthropic) | RLHF + konstytucja | ⚠️ | ❌ | ⚠️ |
| EU AI Act (2024) | Regulacja prawna | ⚠️ | ⚠️ | ⚠️ |
| **ADRION SMC** | **Formalne wektory w kodzie** | **✅** | **✅** | **✅** |

---

## 8. Ewolucja Kodu

Superior Moral Code może być **rozszerzany, nigdy zawężany** (Guardian G9):

```
Dozwolone:
  + Dodanie nowego Guardiana (G10+)
  + Zaostrzenie progu θ
  + Rozszerzenie definicji "krzywdy"

Niedozwolone:
  - Usunięcie istniejącego Guardiana
  - Obniżenie progu θ bez konsensusu
  - Zawężenie definicji "człowieka / istoty zdolnej do cierpienia"
```

Każda zmiana wymaga:
1. Wpisu w Genesis Record z uzasadnieniem (G4)
2. Aktualizacji `docs/THREAT_MODEL.md` (nowe wektory ataku)
3. Aktualizacji testów macierzy konfliktów (sekcja 5)

---

*Superior Moral Code to nie zbiór reguł do obejścia — to matematyczna struktura niemożliwa do ominięcia bez wykrycia.*
