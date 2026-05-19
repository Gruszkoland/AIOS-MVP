# ADRION 369 v4.0 — PROPOZYCJA ROZSZERZEŃ (10 ULEPSZEŃ)

Dokument definiuje standardy techniczne dla ewolucji systemu z v3.0 do v4.0, koncentrując się na niezawodności egzekucji i bezpieczeństwie operacyjnym.

## 1. Trust Score per Agent (TSPA)
- **Opis**: Każdy agent w roju (Librarian, SAP, Auditor, itd.) otrzymuje dynamiczny współczynnik `0.0–1.0`.
- **Mechanizm**: Sukcesy (brak błędów składni, zatwierdzone zmiany) zwiększają TS o 0.05. Błędy lub odrzucenia przez Auditora obniżają TS o 0.2.
- **Próg**: Operacje agenta z TS < 0.6 są blokowane do czasu "re-kalibracji" przez Master Orchestrator lub manualnego zatwierdzenia przez użytkownika.

## 2. Step Auto-Verification (SAV)
- **Opis**: Automatyczna pętla zwrotna po każdym punkcie z pliku `PLAN` lub `todoList`.
- **Mechanizm**: Przed przejściem do następnego kroku, system wywołuje `get_errors` lub `run_task` w celu potwierdzenia, że cel kroku (Definition of Done) został osiągnięty.
- **Blokada**: Brak weryfikacji wstrzymuje egzekucję (Stop-on-Fail).

## 3. Rollback Checkpoint (RBC)
- **Opis**: Automatyczne tworzenie migawek stanu plików przed ryzykownymi operacjami.
- **Mechanizm**: Integracja z Git (staging) lub kopiowanie do ukrytego folderu `.adrion/checkpoints`.
- **Komenda**: `/rollback` przywraca stan sprzed ostatniej serii zmian.

## 4. Session Continuity Bridge (SCB)
- **Opis**: Przenoszenie "pamięci operacyjnej" między różnymi oknami czatu.
- **Mechanizm**: Eksport istotnych faktów z `/memories/session/` do `/memories/repo/v4_bridge.json` w formacie skompresowanych wektorów RAG.

## 5. Context Window Manager (CWM)
- **Opis**: Inteligentne zarządzanie 128k/200k oknem kontekstu.
- **Mechanizm**: Monitoring tokenów w czasie rzeczywistym. Przy 80% zajętości następuje `Recursive Summarization` historii czatu i kompresja logów do `Genesis Record`.

## 6. Conflict Resolver (CR)
- **Opis**: Rozstrzyganie sporów w architekturze Multi-Agent (MoE).
- **Mechanizm**: Jeśli Auditor i Architect mają sprzeczne propozycje, Arbiter (Master Orchestrator) przeprowadza głosowanie ważone Trust Score. Wynik jest logowany jako "Decyzja Arbitralna".

## 7. DSPy Signature Validator (DSV)
- **Opis**: Walidacja kontraktów między agentami.
- **Mechanizm**: Każde zadanie musi posiadać sygnaturę (Input: `context_schema`, Output: `action_schema`). DSV odrzuca zadania o niejasnej strukturze przed ich uruchomieniem.

## 8. Dry Run Mode (DRM)
- **Opis**: Tryb bezpiecznej symulacji (Sandbox).
- **Mechanizm**: System generuje plan zmian i przewidywane wyniki `git diff` bez fizycznego zapisu na dysku. Użytkownik widzi wizualizację "Co się stanie".

## 9. Telemetria EBDI Live (TEL)
- **Opis**: Monitorowanie PAD (Pleasure, Arousal, Dominance) w terminalu/dashboardzie.
- **Mechanizm**: Wyświetlanie paska stanu dla aktywnego agenta. Migający alert przy `Arousal > 0.7` sygnalizuje ryzyko halucynacji lub błędu krytycznego.

## 10. Persona Health Monitor (PHM)
- **Opis**: Detekcja dryfowania charakteru agenta.
- **Mechanizm**: Jeśli odpowiedzi agenta są niespójne z jego rolą (np. Librarian próbuje pisać kod zamiast dokumentować) przez >3 interakcje, Healer wymusza "Identity Reset" do bazowego system_promptu.

---
*Dokument zatwierdzony przez Master Orchestrator v3.0 dla implementacji w cyklu v4.0.*
