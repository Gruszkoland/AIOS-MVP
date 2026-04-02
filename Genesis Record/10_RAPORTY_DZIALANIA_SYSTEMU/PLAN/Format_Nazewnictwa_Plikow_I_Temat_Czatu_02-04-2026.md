# PLAN: Format Nazewnictwa Plików i Temat Czatu

**Data:** 02-04-2026  
**Status:** in-progress

<!-- status: planned -->

**Cel główny:** Zmiana formatu nazewnictwa plików sesji na `Tytuł_Tematu_DD-MM-YYYY.md`, wdrożenie automatycznego generowania tematu z celu planu, rozszerzenie formatu pytania końcowego o wyjaśnienie wdrożenia.

---

## Cel glowny

Zamiana obecnego formatu `YYYY-MM-DD_slug_shortid.md` na czytelny format `Tytuł_Tematu_Semantycznego_DD-MM-YYYY.md`, który:

- Jest generowany na podstawie celu sesji (z promptu lub planu)
- Zawiera datę w formacie europejskim DD-MM-YYYY
- Używa wielkich liter i podkreśleń zamiast myślników
- Eliminuje techniczny `shortid` na rzecz semantycznego tytułu

---

## Kroki wykonawcze

### Krok 1 — Aktualizacja `create_session_reports.py`

- **Cel:** Zmiana funkcji `build_names()` aby generowała format `Tytuł_Tematu_DD-MM-YYYY.md`
- **Kryterium ukończenia:** Plik generuje nazwę `Format_Nazewnictwa_Plikow_I_Temat_Czatu_02-04-2026.md` zamiast `2026-04-02_chat-session_feaeda7c.md`
- **Zależności:** Brak
- **Priorytet:** Wysoki
- **Status:** `planned`

### Krok 2 — Aktualizacja `validate_session_reports.py`

- **Cel:** Aktualizacja walidatora aby rozpoznawał nowy format nazw plików
- **Kryterium ukończenia:** Validator poprawnie wykrywa i waliduje pliki w nowym formacie
- **Zależności:** Krok 1
- **Priorytet:** Wysoki
- **Status:** `planned`

### Krok 3 — Aktualizacja `copilot-instructions.md`

- **Cel:** Zmiana reguły nazewnictwa na nowy format + rozszerzenie formatu pytania końcowego
- **Kryterium ukończenia:** Instrukcje zawierają dokładny opis nowego formatu i wzbogacone pytanie końcowe
- **Zależności:** Brak
- **Priorytet:** Wysoki
- **Status:** `planned`

### Krok 4 — Aktualizacja `tasks.json` (VS Code inputs)

- **Cel:** Dodanie mechanizmu `inputs` do zadań VS Code tak aby użytkownik był pytany o temat przy uruchamianiu zadania
- **Kryterium ukończenia:** Uruchomienie zadania "ADRION: Create Session Reports" powoduje prompt o temat
- **Zależności:** Krok 1
- **Priorytet:** Średni
- **Status:** `planned`

### Krok 5 — Test end-to-end

- **Cel:** Weryfikacja nowego formatu od generowania do walidacji
- **Kryterium ukończenia:** `OK: Walidacja poprawna dla Nowy_Temat_Sesji_02-04-2026.md`
- **Zależności:** Kroki 1-4
- **Priorytet:** Wysoki
- **Status:** `planned`

### Krok 6 — Raport końcowy

- **Cel:** Dokumentacja wykonanych zmian z opisem efektów
- **Kryterium ukończenia:** Plik REPORTS z pełnym opisem wykonanych zmian
- **Zależności:** Krok 5
- **Priorytet:** Normalny
- **Status:** `planned`
