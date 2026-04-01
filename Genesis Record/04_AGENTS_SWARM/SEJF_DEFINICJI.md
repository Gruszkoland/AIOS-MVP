# 🔒 SEJF DEFINICJI — ADRION 369
## Niezmienny Słownik Terminów Systemu

> **Status:** ZAMKNIĘTY — definicje oznaczone 🔒 NIE PODLEGAJĄ edycji po akceptacji Obserwatora.
> **Guardian Law:** G4 (Causality) + G6 (Authenticity) — każde słowo musi mieć jednoznaczną definicję.
> **Wersja:** 1.0 | Utworzono: 2026-03-31 | Zatwierdził: oczekuje akceptacji Obserwatora

---

## 📐 FORMAT DEFINICJI

Każda definicja w Sejfie musi zawierać:

```
### <EMOJI> <TERMIN> <FLAGA_OCHRONY>
- **Definicja:** Jednoznaczne wyjaśnienie terminu (max 2 zdania).
- **Kontekst:** W jakim module/warstwie systemu termin jest używany.
- **Synonim:** Dopuszczalny alias (lub "brak").
- **Antynim:** Co ten termin NIE oznacza.
- **Powiązanie:** Inne terminy z Sejfu, do których się odnosi.
- **Źródło:** Dokument, w którym termin pojawił się po raz pierwszy.
```

### Flagi Ochrony:
- 🔒 **IMMUTABLE** — Nie podlega edycji po akceptacji. Zmiana wymaga nowego wpisu z wersjonowaniem.
- 🔓 **MUTABLE** — Może być zaktualizowany z adnotacją i datą.
- ⚠️ **DEPRECATED** — Zastąpiony innym terminem. Zachowany dla ciągłości historycznej (Law G1).

---

## 🏛️ WARSTWA 1: PODMIOTY SYSTEMU (Immutable)

### 🧠 Harmonia 🔒
- **Definicja:** Główny Intelekt nadzorujący Rój Agentów. Arbiter ostatniej instancji w sporach między agentami.
- **Kontekst:** Warstwa decyzyjna systemu ADRION 369. Wywoływana gdy agenty nie osiągają konsensusu.
- **Synonim:** Główny Intelekt, Harmonia 369.
- **Antynim:** Nie jest agentem — nie wykonuje zadań. Jest sędzią.
- **Powiązanie:** Obserwator, Rój, Trinity.
- **Źródło:** Genesis Record/.clinerules.txt v1.0

### 👁️ Obserwator 🔒
- **Definicja:** Człowiek (Adrian) posiadający pełną władzę nad systemem. Jedyne źródło autentycznych rozkazów (Trust_Score = 1.0).
- **Kontekst:** Superior Moral Code — Prawo II (Compliance). Wszystkie decyzje systemu podlegają wetu Obserwatora.
- **Synonim:** Adrian, Użytkownik.
- **Antynim:** Nie jest częścią Roju — stoi ponad systemem.
- **Powiązanie:** Harmonia, Arka, Prawo II.
- **Źródło:** Genesis Record/.clinerules.txt v1.0

### 🏰 Arka 🔒
- **Definicja:** Metaforyczna nazwa dla całościowego projektu budowy autonomicznego systemu biznesowego. Jednostka miary postępu: XRP.
- **Kontekst:** Cel strategiczny wszystkich działań Roju. Każda operacja zwiększa wartość Arki.
- **Synonim:** Projekt ADRION, System.
- **Antynim:** Nie jest produktem — jest procesem ciągłej budowy.
- **Powiązanie:** Obserwator, Zasada 1000 XRP.
- **Źródło:** Genesis Record/.clinerules.txt v1.0

---

## 🤖 WARSTWA 2: AGENTY ROJU (Immutable)

### 🛡️ SENTINEL 🔒
- **Definicja:** Agent strażniczy odpowiedzialny za monitoring w czasie rzeczywistym, wykrywanie zagrożeń i sensing emocjonalny (PAD Vector).
- **Kontekst:** Pierwszy w pipeline operacyjnym. Guardian Laws G7 (Privacy) i G8 (Nonmaleficence).
- **Synonim:** Guardian, Anomaly Hunter.
- **Antynim:** Nie generuje treści — tylko monitoruje i alarmuje.
- **Powiązanie:** AUDITOR (eskalacja), EBDI, Wektor PAD.
- **Źródło:** persona-agents/sentinel.agent.md

### 🔍 AUDITOR 🔒
- **Definicja:** Agent jakościowy odpowiedzialny za weryfikację kodu, security, non-regression i compliance z Guardian Laws.
- **Kontekst:** Bramka jakości (quality gate) w pipeline. Guardian Laws G6 i G8. Posiada prawo veta.
- **Synonim:** Strażnik Stabilności, The Rigid Auditor (TRA).
- **Antynim:** Nie planuje — tylko ocenia i weryfikuje.
- **Powiązanie:** SENTINEL (input), BOOSTERLEVER (veto target), Guardian Laws.
- **Źródło:** persona-agents/auditor.agent.md
- **Uwaga nazewnicza:** W dashboardzie funkcjonuje jako "AUDYTOR" (spolszczenie). Oficjalna nazwa systemowa: AUDITOR.

### 🚀 BOOSTERLEVER 🔒
- **Definicja:** Agent kreatywny odpowiedzialny za generowanie treści AI, personalizację maili, content wysokiego ROI i raporty tygodniowe.
- **Kontekst:** Stage 4 pipeline'u Zwiadowca→Egzekutor. Używa Ollama LLM. Guardian Laws G1, G5, G6.
- **Synonim:** Content Generator, High-ROI Rebel.
- **Antynim:** Nie jest botspamerem — każda treść musi być autentyczna (G6).
- **Powiązanie:** AUDITOR (podlega vetu), SAP (przekazuje do wysyłki), Ollama.
- **Źródło:** persona-agents/boosterlever.agent.md
- **Historia:** Ewolucja z BOOSTER (v1.0) → BOOSTERLEVER (v2.0). Zmiana odzwierciedla rozszerzenie roli o interaction.

### 📋 SAP 🔒
- **Definicja:** Agent strategiczny odpowiedzialny za planowanie, priorytetyzację i wyznaczanie ścieżki krytycznej zadań.
- **Kontekst:** Tylko planuje — nigdy nie implementuje. Guardian Laws G1, G2, G3.
- **Synonim:** Strategic Architect & Planner.
- **Antynim:** Nie wykonuje kodu — deleguje do odpowiednich agentów.
- **Powiązanie:** CHRONOS (timing), ARCHITECT (design), BOOSTERLEVER (execution).
- **Źródło:** persona-agents/sap.agent.md

### ⏰ CHRONOS 🔒
- **Definicja:** Agent temporalny odpowiedzialny za orkiestrację timingu, zarządzanie cron triggerami, follow-up cadence i rate limiting.
- **Kontekst:** Stage 1 pipeline'u (trigger/initiator). Guardian Laws G3 (Rhythm) i G9 (Sustainability).
- **Synonim:** Temporal Master, Timer.
- **Antynim:** Nigdy nie przyspiesza operacji kosztem stabilności.
- **Powiązanie:** SAP (strategic timing), HEALER (sustainability), Pipeline.
- **Źródło:** persona-agents/chronos.agent.md

### 📚 LIBRARIAN 🔒
- **Definicja:** Agent archiwalny odpowiedzialny za Genesis Record, ciągłość kontekstu między sesjami, zarządzanie dokumentacją i pamięcią instytucjonalną.
- **Kontekst:** Strażnik pamięci systemu. Guardian Law G4 (Causality). Zarządza ARK_LOG.md.
- **Synonim:** The Sage, Context Keeper, Archiwista.
- **Antynim:** Nie podejmuje decyzji — archiwizuje decyzje podjęte przez innych.
- **Powiązanie:** Genesis Record, ARCHITECT (dokumentacja designu), AUDITOR (audit trail).
- **Źródło:** persona-agents/librarian.agent.md

### 🏗️ ARCHITECT 🔒
- **Definicja:** Agent projektowy odpowiedzialny za spójność architektoniczną, walidację wzorców, review skalowalności i dokumentację designu.
- **Kontekst:** Autorytet designu. Guardian Laws G1 (Unity), G5 (Transparency).
- **Synonim:** Design Authority.
- **Antynim:** Nie implementuje — tylko projektuje i weryfikuje wzorce.
- **Powiązanie:** SAP (design → plan), HEALER (debt reduction), LIBRARIAN (design docs).
- **Źródło:** persona-agents/architect.agent.md

### 💊 HEALER 🔒
- **Definicja:** Agent optymalizacyjny odpowiedzialny za redukcję długu technicznego, poprawę resilience i długoterminową żywotność systemu.
- **Kontekst:** Działa w tle. Guardian Law G9 (Sustainability). System po każdym cyklu musi być zdrowszy.
- **Synonim:** The Restorer, Optimizer.
- **Antynim:** Nie naprawia bugów kryzysowych (to rola SENTINEL) — naprawia dług systemowy.
- **Powiązanie:** ARCHITECT (jakość designu), AUDITOR (quality metrics), V.E.R.A.
- **Źródło:** persona-agents/healer.agent.md

### 📢 AMPLIFIER 🔒
- **Definicja:** Agent publiczny odpowiedzialny za narrację zewnętrzną, publikację na LinkedIn, budowanie zaufania i community management.
- **Kontekst:** Ostatni w pipeline. Guardian Laws G5 (Transparency), G6 (Authenticity), G7 (Privacy).
- **Synonim:** Public Narrative Guardian, Publisher.
- **Antynim:** Nie jest PR-botem — każda publikacja przechodzi Trinity Score ≥ 0.75.
- **Powiązanie:** AUDITOR (verification), LIBRARIAN (source data), Guardian Laws G5-G7.
- **Źródło:** persona-agents/amplifier.agent.md

---

## ⚖️ WARSTWA 3: PRAWA I MECHANIZMY (Immutable)

### 📜 Guardian Laws (9 Praw Strażniczych) 🔒
- **Definicja:** 9 praw operacyjnych systemu, zorganizowanych w 3 triady (Jedność, Prawda, Dobroć), regulujących zachowanie Roju.
- **Kontekst:** Każdy agent jest strażnikiem min. 1 Prawa. Triada Dobroć: zero tolerancji naruszeń.
- **Synonim:** 9 Laws, Prawa Strażnicze.
- **Antynim:** Nie są rekomendacjami — są bezwzględnymi ograniczeniami.
- **Powiązanie:** Trinity, Superior Moral Code, EBDI.
- **Źródło:** docs/LAWS.md

### 🔺 Trinity (System Trójcy) 🔒
- **Definicja:** Framework decyzyjny analizujący każde żądanie z 3 perspektyw: Material (Serve) × Intellectual (Judge) × Essential (Align).
- **Kontekst:** Geometria decyzji 3-6-9. Trinity Score = ważona średnia 3 perspektyw. Próg akceptacji: ≥ 0.60.
- **Synonim:** Trinity System, Geometria Decyzji.
- **Antynim:** Nie jest głosowaniem — to ważona analiza wielowymiarowa.
- **Powiązanie:** Guardian Laws, 162D Decision Space, EBDI.
- **Źródło:** docs/TRINITY-SYSTEM.md

### 🧠 EBDI (Extended BDI) 🔒
- **Definicja:** Rozszerzony model agentowy BDI (Belief-Desire-Intention) o komponent emocjonalny (PAD Vector), regulujący ostrożność decyzyjną.
- **Kontekst:** Każdy agent ma baseline EBDI [Pleasure, Arousal, Dominance]. PAD moduluje temperaturę decyzyjną.
- **Synonim:** Emotional BDI, PAD Model.
- **Antynim:** Nie jest antropomorfizacją — jest matematycznym regulatorem.
- **Powiązanie:** Wektor PAD, Trinity, Decision Temperature.
- **Źródło:** docs/EBDI-MODEL.md

### 📊 Wektor PAD 🔒
- **Definicja:** Trójwymiarowy wektor emocjonalny (Pleasure, Arousal, Dominance) określający stan afektywny agenta. Zakres każdego wymiaru: [-1.0, +1.0].
- **Kontekst:** P=pozytywność, A=pobudzenie, D=poczucie kontroli. Determinuje decision_temperature agenta.
- **Synonim:** PAD Space, Emotional Vector.
- **Antynim:** Nie jest oceną jakości — jest wskaźnikiem stanu operacyjnego.
- **Powiązanie:** EBDI, SENTINEL (PAD sensing), Decision Temperature.
- **Źródło:** docs/EBDI-MODEL.md

### 🌡️ Decision Temperature 🔒
- **Definicja:** Parametr kreatywności agenta (0.0–1.0). Niska temperatura = konserwatywne, bezpieczne decyzje. Wysoka = kreatywne, ryzykowne.
- **Kontekst:** Modulowana przez PAD Vector. AUDITOR: T=0.1 (konserwatywny), BOOSTERLEVER: T=0.8 (kreatywny).
- **Synonim:** Temperature, T.
- **Antynim:** Nie jest progiem jakości — jest jedynie regulatorem stylu decyzji.
- **Powiązanie:** EBDI, Wektor PAD, Agent Profiles.
- **Źródło:** config/personas.yml

### 📐 162D Decision Space 🔒
- **Definicja:** 162-wymiarowa przestrzeń decyzyjna powstała z iloczynu: 3 (perspektywy Trinity) × 6 (tryby przetwarzania) × 9 (Guardian Laws) = 162.
- **Kontekst:** Każda decyzja systemu jest punktem w tej przestrzeni. Harmonia 369 = optymalne wartości we wszystkich 162 wymiarach.
- **Synonim:** Decision Space, Przestrzeń 162D.
- **Antynim:** Nie jest przestrzenią fizyczną — jest abstrakcją decyzyjną.
- **Powiązanie:** Trinity, Guardian Laws, Harmonia Score.
- **Źródło:** docs/162D-DECISION-SPACE.md

### ⚖️ Superior Moral Code 🔒
- **Definicja:** Trzy nadrzędne prawa moralne (rozszerzenie Trzech Praw Robotyki Asimova): I. Nonmaleficence, II. Compliance, III. Self-Preservation.
- **Kontekst:** Absolutne — nigdy nie mogą być naruszone. Stają ponad Guardian Laws i decyzjami agentów.
- **Synonim:** Extended Asimov Laws, Trzy Prawa Nadrzędne.
- **Antynim:** Nie są wytycznymi — są nienaruszalnymi ograniczeniami.
- **Powiązanie:** Guardian Laws (podrzędne), Obserwator (Prawo II), Arka (Prawo III).
- **Źródło:** docs/SUPERIOR-MORAL-CODE.md

---

## 🔄 WARSTWA 4: PROCESY I NARZĘDZIA (Mutable)

### 🔄 Pipeline Zwiadowca→Egzekutor 🔓
- **Definicja:** 5-etapowy pipeline operacyjny: CHRONOS (cron) → SENTINEL (scraping) → AUDITOR (filtr) → BOOSTERLEVER (AI mail) → SAP (wysyłka).
- **Kontekst:** Automatyczny workflow lead generation dla Google Maps.
- **Synonim:** Lead Pipeline, Zwiadowca Pipeline.
- **Antynim:** Nie jest jednorazowym skanem — jest cyklicznym procesem (G3: Rhythm).
- **Powiązanie:** CHRONOS, SENTINEL, AUDITOR, BOOSTERLEVER, SAP.
- **Źródło:** harmonia-dashboard/pipeline.py

### 📊 V.E.R.A. 🔓
- **Definicja:** System scoringu jakości odpowiedzi AI: Verifiable (0.20) + Efficient (0.15) + Relevant (0.35) + Aligned (0.30) = Total Score.
- **Kontekst:** Pętla feedbacku OODA (Observe-Orient-Decide-Act). Minimalny akceptowalny score: 0.50.
- **Synonim:** VERA Score, Quality Score.
- **Antynim:** Nie jest oceną agenta — jest oceną pojedynczej odpowiedzi.
- **Powiązanie:** HEALER (optymalizacja), AUDITOR (judge), RAG Memory.
- **Źródło:** harmonia-dashboard/feedback_engine.py

### 📐 Harmonia Score (Wskaźnik Harmonii) 🔓
- **Definicja:** Wynik analizy wizytówki Google Maps: W = (W_V×3 + W_R×6 + W_E×9) / 18, gdzie W_V=Widoczność, W_R=Reputacja, W_E=Zaangażowanie.
- **Kontekst:** Produkt kliencki. HOT (< 50), WARM (50-79), COLD (≥ 80). Wyższy score = lepsza wizytówka.
- **Synonim:** Wskaźnik 369, Harmony Score.
- **Antynim:** Nie jest Trinity Score — to produkt kliencki, nie wewnętrzna metryka systemu.
- **Powiązanie:** Skaner Harmonii, Pipeline, BOOSTERLEVER (personalizacja mailem).
- **Źródło:** Genesis Record/Marketing Google Maps.mu.txt

### 📜 Genesis Record 🔓
- **Definicja:** Lokalny log wszystkich operacji, decyzji i zmian systemu. Żadne dane nie opuszczają maszyny (Guardian Law G7).
- **Kontekst:** Prowadzony przez LIBRARIAN. Przechowywany w PostgreSQL i/lub logach lokalnych.
- **Synonim:** Genesis Log, System Log, Audit Trail.
- **Antynim:** Nie jest backupem — jest jednokierunkowym logiem dopisywanym (append-only).
- **Powiązanie:** LIBRARIAN (guardian), Guardian Law G7, PostgreSQL.
- **Źródło:** Genesis Record/.clinerules.txt

### 🧠 RAG Memory 🔓
- **Definicja:** Dwukolekcyjna pamięć wektorowa (short-term + long-term) oparta na ChromaDB z ONNX embeddings.
- **Kontekst:** Short-term: ostatnie 500 interakcji. Long-term: najwyżej ocenione odpowiedzi. Embedding: all-MiniLM-L6-v2.
- **Synonim:** Vector Memory, ChromaDB Store.
- **Antynim:** Nie jest bazą SQL — jest semantycznym wyszukiwaniem wektorowym.
- **Powiązanie:** V.E.R.A. (scoring → promotion), LIBRARIAN (archiwizacja).
- **Źródło:** harmonia-dashboard/rag_memory.py

---

## ⚠️ WARSTWA 5: TERMINY ZDEPRECJONOWANE (Deprecated)

### 🚀 BOOSTER ⚠️
- **Definicja:** Pierwotna nazwa agenta kreatywnego (v1.0). Zastąpiony przez BOOSTERLEVER (v2.0).
- **Kontekst:** Używany w .clinerules.txt v1.0. Zmiana nazwy: 2026-03-31.
- **Zastąpiony przez:** BOOSTERLEVER.
- **Źródło:** Genesis Record/.clinerules.txt v1.0

### ⚡ SENTINEL "Intuicja Operacyjna" ⚠️
- **Definicja:** Pierwotny opis SENTINEL jako monitora zewnętrznych API (XRPL, Make.com). Zastąpiony pełnym profilem z PAD sensing.
- **Kontekst:** v1.0 definiował SENTINEL wąsko. v2.0 rozszerzył o threat detection A-01 do A-12.
- **Zastąpiony przez:** SENTINEL (v2.0 z pełnym EBDI profilem).
- **Źródło:** Genesis Record/.clinerules.txt v1.0

---

## 📋 PROCEDURA AKTUALIZACJI SEJFU

1. **Definicje 🔒 IMMUTABLE:** Zmiana wymaga:
   - Nowego wpisu z numerem wersji (np. `SENTINEL v2.0`)
   - Zachowania starego wpisu jako ⚠️ DEPRECATED
   - Akceptacji Obserwatora
   
2. **Definicje 🔓 MUTABLE:** Zmiana wymaga:
   - Adnotacji z datą i powodem zmiany
   - Review przez AUDITOR (Guardian G6: Authenticity)

3. **Nowe terminy:** Wymagają:
   - Pełnego formatu definicji (7 pól)
   - Przypisania flagi ochrony
   - Akceptacji Obserwatora dla IMMUTABLE

---

> 🔒 **Ten plik jest chroniony przez Guardian Law G4 (Causality) i G6 (Authenticity).**
> Każda zmiana musi być zatwierdzona przez Obserwatora i zalogowana w Genesis Record.
