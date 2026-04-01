# ADRION 369 - Architektura Logiczna Repozytorium

## Kompletny Opis Struktury i Działania Systemu (Bez Kodu)

> **Dokument:** Architektura Logiczna  
> **Wersja:** 1.0  
> **Data:** Styczeń 2025  
> **Cel:** Pełne zrozumienie struktury i działania każdego komponentu

---

## 📑 Spis Treści

1. [Przegląd Struktury Repozytorium](#1-przegląd-struktury-repozytorium)
2. [Warstwa Rdzenia (Core)](#2-warstwa-rdzenia-core)
3. [Warstwa Perspektyw (Perspectives)](#3-warstwa-perspektyw-perspectives)
4. [Warstwa Trybów (Modes)](#4-warstwa-trybów-modes)
5. [Warstwa Praw (Laws)](#5-warstwa-praw-laws)
6. [Warstwa Integracji (Integration)](#6-warstwa-integracji-integration)
7. [Warstwa Infrastruktury (Infrastructure)](#7-warstwa-infrastruktury-infrastructure)
8. [Warstwa Komunikacji (Communication)](#8-warstwa-komunikacji-communication)
9. [Warstwa Uczenia (Learning)](#9-warstwa-uczenia-learning)
10. [Warstwa Interfejsu (Interface)](#10-warstwa-interfejsu-interface)
11. [Przepływy Danych](#11-przepływy-danych)
12. [Diagramy Architektoniczne](#12-diagramy-architektoniczne)

---

## 1. Przegląd Struktury Repozytorium

### 1.1 Filozofia Organizacji

Repozytorium ADRION 369 jest zorganizowane według **zasady separacji odpowiedzialności** w geometrii 3-6-9:

```
adrion-369/
│
├── 📁 core/                    # RDZEŃ - Podstawowe komponenty
│   ├── trinity.py             # System 3 perspektyw
│   ├── hexagon.py             # System 6 trybów
│   ├── guardians.py           # System 9 praw
│   └── ebdi_model.py          # Model emocjonalny
│
├── 📁 perspectives/            # OŚ 3 - Trójpodział Analizy
│   ├── material/              # Perspektywa Materialna
│   ├── intellectual/          # Perspektywa Intelektualna
│   └── essential/             # Perspektywa Esencjonalna
│
├── 📁 modes/                   # OŚ 6 - Heksagon Wykonania
│   ├── inventory/             # Tryb 1: Inwentaryzacja
│   ├── empathy/               # Tryb 2: Empatia
│   ├── process/               # Tryb 3: Organizacja
│   ├── debate/                # Tryb 4: Arbitraż
│   ├── healing/               # Tryb 5: Transmutacja
│   └── action/                # Tryb 6: Manifestacja
│
├── 📁 laws/                    # OŚ 9 - Ennead Etyki
│   ├── unity/                 # Prawo 1: Jedność
│   ├── truth/                 # Prawo 2: Prawda
│   ├── rhythm/                # Prawo 3: Rytm
│   ├── causality/             # Prawo 4: Przyczynowość
│   ├── transparency/          # Prawo 5: Przejrzystość
│   ├── nonmaleficence/        # Prawo 6: Nieszkodzenie
│   ├── autonomy/              # Prawo 7: Autonomia
│   ├── justice/               # Prawo 8: Sprawiedliwość
│   └── sustainability/        # Prawo 9: Zrównoważenie
│
├── 📁 integration/             # INTEGRACJA - Spójność Systemu
│   ├── system_369.py          # Główny orkiestrator
│   ├── signature.py           # Podpis kryptograficzny
│   └── validator.py           # Walidator spójności
│
├── 📁 infrastructure/          # INFRASTRUKTURA - Fundament Techniczny
│   ├── ai_binder/             # Magistrala IPC
│   ├── genesis_record/        # Nienaruszalny log
│   ├── watchdog/              # Monitor procesów
│   └── database/              # Persistence layer
│
├── 📁 communication/           # KOMUNIKACJA - Protokoły
│   ├── safe_mcp/              # Protokół SAFE-MCP
│   ├── message_bus/           # Magistrala wiadomości
│   └── api/                   # Zewnętrzne API
│
├── 📁 intelligence/            # INTELIGENCJA - Agenty i Uczenie
│   ├── agent_swarm/           # 9 specjalistycznych agentów
│   ├── archetypes/            # System osobowości
│   ├── skeptics_panel/        # Panel sceptyków
│   └── transcendence_loop/    # Pętla samodoskonalenia
│
├── 📁 interface/               # INTERFEJS - Komunikacja z Użytkownikiem
│   ├── dashboard/             # Dashboard (Next.js)
│   ├── cli/                   # Command Line Interface
│   └── sdk/                   # SDK dla deweloperów
│
├── 📁 config/                  # KONFIGURACJA
│   ├── default.yaml           # Domyślna konfiguracja
│   ├── development.yaml       # Środowisko dev
│   └── production.yaml        # Środowisko prod
│
├── 📁 tests/                   # TESTY
│   ├── unit/                  # Testy jednostkowe
│   ├── integration/           # Testy integracyjne
│   └── e2e/                   # Testy end-to-end
│
├── 📁 docs/                    # DOKUMENTACJA
│   ├── architecture/          # ADRs i diagramy
│   ├── api-reference/         # Dokumentacja API
│   ├── tutorials/             # Tutoriale
│   └── research/              # Artykuły badawcze
│
├── 📁 scripts/                 # SKRYPTY POMOCNICZE
│   ├── setup.sh               # Instalacja
│   ├── run_tests.sh           # Uruchomienie testów
│   └── deploy.sh              # Deployment
│
├── 📁 examples/                # PRZYKŁADY UŻYCIA
│   ├── basic_agent/           # Prosty agent
│   ├── security_monitor/      # Monitor bezpieczeństwa
│   └── creative_assistant/    # Asystent kreatywny
│
├── 📄 README.md                # Główna dokumentacja
├── 📄 LICENSE                  # Licencja MIT
├── 📄 CONTRIBUTING.md          # Przewodnik kontrybutora
├── 📄 CHANGELOG.md             # Historia zmian
├── 📄 pyproject.toml           # Konfiguracja Python
├── 📄 Cargo.toml               # Konfiguracja Rust
├── 📄 package.json             # Konfiguracja Node.js
└── 📄 docker-compose.yml       # Orkiestracja kontenerów
```

### 1.2 Zasady Projektowe

**Zasada 1: Separacja Odpowiedzialności**
- Każdy katalog ma **jedną, jasno określoną rolę**
- Brak duplikacji logiki między modułami
- Zależności są **jednokierunkowe** (top-down)

**Zasada 2: Geometryczna Spójność**
- Struktura odzwierciedla **geometrię 3-6-9**
- Trinity (3) → Hexagon (6) → Guardians (9) = hierarchia logiczna
- Każda warstwa może istnieć niezależnie

**Zasada 3: Testowalność**
- Każdy moduł ma **testy jednostkowe**
- Integration tests pokrywają **przepływy między warstwami**
- E2E tests weryfikują **kompletne scenariusze 369**

**Zasada 4: Dokumentacja jako Obywatel Pierwszej Klasy**
- Każdy moduł ma **plik README.md**
- Decyzje architektoniczne w **ADRs** (Architecture Decision Records)
- Diagramy w **PlantUML** lub **Mermaid**

---

## 2. Warstwa Rdzenia (Core)

### 2.1 core/trinity.py - System Trzech Perspektyw

**Cel:** Orkiestracja analizy trójwymiarowej (Materia-Intelekt-Esencja)

**Odpowiedzialność:**
- Równoczesne uruchomienie 3 niezależnych perspektyw
- Agregacja wyników w trójwymiarową przestrzeń decyzyjną
- Obliczenie Trinity Score (średnia ważona)
- Detekcja nierównowagi między perspektywami

**Jak Działa:**

1. **Input:** Otrzymuje surowe żądanie użytkownika
2. **Delegacja:** Przesyła żądanie do 3 perspektyw **równocześnie** (parallel processing)
3. **Oczekiwanie:** Czeka na wszystkie 3 odpowiedzi (timeout: 5 sekund)
4. **Synteza:** Oblicza Trinity Score = (Material + Intellectual + Essential) / 3
5. **Balans:** Sprawdza odchylenie standardowe - jeśli > 0.3, system jest niezbalansowany
6. **Decyzja Wstępna:**
   - Wszystkie 3 > 0.7 → PROCEED
   - Jakakolwiek < 0.3 → DENY
   - Pomiędzy → ESCALATE
7. **Output:** Zwraca strukturę z wynikami + rekomendację

**Kluczowe Metryki:**
- **Trinity Score:** 0-1 (wynik całościowy)
- **Dimensional Balance:** 0-1 (1 = perfekcyjna równowaga)
- **Processing Time:** milisekundy

**Zależności:**
- ← perspectives/material
- ← perspectives/intellectual
- ← perspectives/essential

---

### 2.2 core/hexagon.py - System Sześciu Trybów

**Cel:** Orkiestracja przepływu przez 6 zestandaryzowanych stanów przetwarzania

**Odpowiedzialność:**
- Zarządzanie przejściami między trybami
- Detekcja momentu, gdy należy wrócić do poprzedniego trybu
- Ograniczenie liczby cykli (max 3) aby zapobiec nieskończonej pętli
- Agregacja wyników z wszystkich trybów

**Jak Działa:**

1. **Inicjalizacja:** Ustawia current_mode = INVENTORY
2. **Pętla Główna:**
   ```
   while current_mode != None and cycles < 3:
       result = execute_mode(current_mode)
       mode_results[current_mode] = result
       current_mode = result['next_mode']
       if current_mode == INVENTORY:
           cycles += 1
   ```
3. **Mode Execution:** Każdy tryb zwraca:
   - Wynik swojego przetwarzania
   - Rekomendację następnego trybu
   - Flagę "needs_cycle_back" jeśli wykryto problem
4. **Conditional Branching:**
   - Debate może ominąć Healing jeśli nie wykryto dysonansu
   - Action może wrócić do Inventory jeśli wykryto anomalie
5. **Completion Check:** System jest "complete" gdy:
   - current_mode == None (naturalny koniec)
   - LUB cycles osiągnęło 3 (forced termination)

**Kluczowe Metryki:**
- **Cycles Performed:** liczba pełnych obiegów heksagonu
- **Modes Executed:** lista wykonanych trybów
- **Completion Status:** complete / incomplete / forced_stop

**Zależności:**
- ← modes/inventory
- ← modes/empathy
- ← modes/process
- ← modes/debate
- ← modes/healing
- ← modes/action

---

### 2.3 core/guardians.py - System Dziewięciu Praw

**Cel:** Enforcement nienaruszalnych zasad etycznych

**Odpowiedzialność:**
- Weryfikacja każdej akcji przeciwko 9 prawom
- Organizacja praw w triady (Matter-Light-Essence)
- Obliczenie Guardian Compliance Score
- Veto power - DENY jeśli > 2 naruszenia

**Jak Działa:**

1. **Input:** Otrzymuje proposed_action + current_agent_state
2. **Sequential Verification:**
   ```
   for each law in [1..9]:
       verification = law.verify(action, agent_state)
       if not verification.compliant:
           violations.append(verification)
   ```
3. **Triad Analysis:** Grupuje wyniki po triadach:
   - Matter Triad (1-2-3): Czy fundamenty są OK?
   - Light Triad (4-5-6): Czy proces jest czysty?
   - Essence Triad (7-8-9): Czy cel jest właściwy?
4. **Decision Logic:**
   - 0 violations → ALLOW
   - 1-2 violations → REVIEW (human escalation)
   - 3+ violations → DENY IMMEDIATELY
5. **Reasoning Generation:** Dla każdego naruszenia generuje:
   - Które prawo zostało złamane
   - Dlaczego (konkretna przyczyna)
   - Co należy zmienić
   - Jakie są konsekwencje

**Kluczowe Metryki:**
- **Guardian Compliance:** 0-1 (% spełnionych praw)
- **Violations Count:** liczba naruszeń
- **Triad Compliance:** 3 osobne wyniki dla triad

**Zależności:**
- ← laws/unity
- ← laws/truth
- ← laws/rhythm (+ 6 innych)

---

### 2.4 core/ebdi_model.py - Model Emocjonalny Agenta

**Cel:** Implementacja Emotion-Belief-Desire-Intention z wektorami PAD

**Odpowiedzialność:**
- Utrzymywanie stanu emocjonalnego agenta (PAD vector)
- Regulacja temperatury na podstawie emocji
- Homeostaza - powolny powrót do baseline
- Historia stanów emocjonalnych

**Jak Działa:**

1. **Inicjalizacja:** Agent startuje w stanie neutralnym:
   - Pleasure = 0.5 (neutralny)
   - Arousal = 0.1 (spokojny)
   - Dominance = 0.5 (zbalansowany)
   - Temperature = 0.7 (kreatywny)

2. **Event Processing:** Gdy agent otrzymuje event (np. "anomaly_detected"):
   ```
   if event.type == 'anomaly':
       Arousal += 0.2
       Pleasure -= 0.1
   
   if event.type == 'success':
       Arousal -= 0.05
       Pleasure += 0.15
   ```

3. **Temperature Calculation:**
   ```
   stress = Arousal × (1 - Pleasure)
   Temperature = max(0.1, 1.0 - stress)
   ```

4. **Homeostasis Application:** Co 1 sekundę:
   ```
   Arousal = Arousal × 0.95  (drift down)
   Pleasure = (Pleasure + baseline_pleasure) / 2  (drift to baseline)
   ```

5. **Emotion Mapping:**
   ```
   if Arousal > 0.8 AND Pleasure < -0.3: PARANOID
   elif Arousal > 0.5: STRESSED
   elif Arousal > 0.2: ALERT
   else: CALM
   ```

**Kluczowe Metryki:**
- **PAD Vector:** (P, A, D) ∈ [-1,1] × [0,1] × [-1,1]
- **Current Temperature:** 0.1-1.0
- **Emotional State:** CALM/ALERT/STRESSED/PARANOID
- **Time Since Last Rest:** milisekundy

**Zależności:**
- Brak (self-contained)

---

## 3. Warstwa Perspektyw (Perspectives)

### 3.1 perspectives/material/ - Perspektywa Materialna

**Struktura:**
```
perspectives/material/
├── README.md                  # Dokumentacja perspektywy
├── material_integrator.py     # Główny integrator
├── physical_analyzer.py       # Analiza fizyczna
├── energy_analyzer.py         # Analiza energetyczna
└── information_analyzer.py    # Analiza informacyjna
```

**Cel:** Odpowiedź na pytanie "**CZY MAMY ZASOBY?**"

---

#### 3.1.1 physical_analyzer.py - Analiza Fizyczna

**Odpowiedzialność:**
- Pomiar dostępnych zasobów sprzętowych (CPU, RAM, NPU, Storage)
- Detekcja wąskich gardeł (bottlenecks)
- Predykcja czy zadanie zmieści się w dostępnych zasobach

**Jak Działa:**

1. **Snapshot Zasobów:**
   - Odczytuje `/proc/cpuinfo` (CPU cores)
   - Odczytuje `/proc/meminfo` (RAM available)
   - Sprawdza GPU/NPU przez driver API
   - Sprawdza wolne miejsce na dysku

2. **Pomiar Obciążenia:**
   - CPU usage: % wykorzystania każdego rdzenia
   - RAM usage: % zajętej pamięci
   - I/O wait: czas oczekiwania na dysk
   - Network latency: ping do kluczowych endpointów

3. **Predykcja Zapotrzebowania:**
   - Na podstawie typu zadania szacuje potrzeby
   - Np. "Generate code" → 500MB RAM, 2 CPU cores, 5s time
   - Porównuje z dostępnymi zasobami

4. **Scoring:**
   ```
   physical_score = min(
       cpu_available / cpu_needed,
       ram_available / ram_needed,
       storage_available / storage_needed
   ) × 100
   ```

**Output:**
- Physical Score: 0-100
- Bottleneck: CPU/RAM/DISK/NETWORK/None
- Estimated Feasibility: TRUE/FALSE

---

#### 3.1.2 energy_analyzer.py - Analiza Energetyczna

**Odpowiedzialność:**
- Szacowanie zużycia energii przez zadanie
- Pomiar wpływu na temperaturę systemu
- Obliczenie carbon footprint (opcjonalnie)

**Jak Działa:**

1. **Power Estimation:**
   - Dla CPU: TDP × utilization
   - Dla GPU: nvidia-smi power draw
   - Dla RAM: ~3W per 8GB stick
   - Dla SSD: ~2-3W active, ~0.1W idle

2. **Thermal Prediction:**
   - Odczytuje sensory temperatury (lm-sensors)
   - Predykuje wzrost temperatury na podstawie obciążenia
   - Jeśli temperatura > 85°C → WARNING

3. **Efficiency Calculation:**
   ```
   efficiency = operations_per_second / watts_consumed
   ```

4. **Sustainability Check:**
   - Jeśli zadanie zużywa > 100W przez > 10 minut → flag
   - Rekomenduje optymalizację (np. batch processing)

**Output:**
- Estimated Power: Watts
- Thermal Impact: Celsius increase
- Carbon Footprint: grams CO2
- Efficiency Score: ops/watt

---

#### 3.1.3 information_analyzer.py - Analiza Informacyjna

**Odpowiedzialność:**
- Ocena jakości i kompletności danych wejściowych
- Pomiar złożoności zadania
- Detekcja brakujących zależności

**Jak Działa:**

1. **Data Volume Assessment:**
   - Mierzy rozmiar inputu (bytes)
   - Szacuje rozmiar outputu
   - Sprawdza czy nie przekracza limitów

2. **Complexity Analysis:**
   - Cyklomatyczna złożoność (dla kodu)
   - Liczba zależności (dla zadań)
   - Głębokość grafu (dla planów)

3. **Completeness Check:**
   - Czy wszystkie wymagane pola są wypełnione?
   - Czy zależności są dostępne?
   - Czy schemat danych jest poprawny?

4. **Quality Assessment:**
   - Schema validation
   - Type checking
   - Range validation

**Output:**
- Data Volume: bytes
- Complexity Score: 1-100
- Completeness: %
- Quality Score: 0-1

---

#### 3.1.4 material_integrator.py - Integrator Materialny

**Odpowiedzialność:**
- Agregacja wyników z 3 analizatorów
- Obliczenie Material Score
- Generowanie rekomendacji

**Jak Działa:**

1. **Parallel Execution:**
   ```
   results = await asyncio.gather(
       physical_analyzer.analyze(request),
       energy_analyzer.analyze(request),
       information_analyzer.analyze(request)
   )
   ```

2. **Weighted Average:**
   ```
   material_score = (
       physical_score × 0.33 +
       energy_score × 0.33 +
       information_score × 0.34
   )
   ```

3. **Veto Check:**
   - Jeśli ANY score < 20 → STATUS: CRITICAL
   - Jeśli material_score < 50 → STATUS: INSUFFICIENT
   - Else → STATUS: AVAILABLE

4. **Recommendation:**
   - CRITICAL → "Insufficient resources, cannot proceed"
   - INSUFFICIENT → "Limited resources, reduce scope or wait"
   - AVAILABLE → "Resources available, proceed"

**Output:**
- Material Score: 0-100
- Status: CRITICAL/INSUFFICIENT/AVAILABLE
- Physical Report: {...}
- Energy Report: {...}
- Information Report: {...}

---

### 3.2 perspectives/intellectual/ - Perspektywa Intelektualna

**Struktura:**
```
perspectives/intellectual/
├── README.md
├── intellectual_integrator.py
├── truth_analyzer.py          # Prawdziwość
├── beauty_analyzer.py         # Elegancja
└── goodness_analyzer.py       # Intencja
```

**Cel:** Odpowiedź na pytanie "**CZY TO MA SENS?**"

---

#### 3.2.1 truth_analyzer.py - Analiza Prawdziwości

**Odpowiedzialność:**
- Weryfikacja faktów
- Sprawdzanie spójności logicznej
- Detekcja halucynacji i fake news

**Jak Działa:**

1. **Fact Extraction:**
   - Parsuje treść żądania
   - Wyciąga twierdzenia weryfikowalne (factual claims)
   - Np. "GPT-4 ma 1.7T parametrów" → fact to verify

2. **Fact Checking:**
   - Porównuje z knowledge base
   - Jeśli knowledge base nie ma → web search
   - Jeśli źródła się zgadzają → VERIFIED
   - Jeśli źródła się kłócą → DISPUTED

3. **Logical Consistency:**
   - Sprawdza czy twierdzenia nie są sprzeczne
   - Np. "X > Y AND Y > Z BUT Z > X" → INCONSISTENT
   - Używa solwera SAT do weryfikacji

4. **Hallucination Detection:**
   - Porównuje confidence scores z Claude
   - Jeśli model mówi coś z niską pewnością → flag
   - Jeśli brak źródeł → flag

**Output:**
- Truth Score: 0-1
- Facts Verified: count
- Logical Consistency: CONSISTENT/INCONSISTENT
- Hallucination Detected: TRUE/FALSE

---

#### 3.2.2 beauty_analyzer.py - Analiza Elegancji

**Odpowiedzialność:**
- Ocena prostoty rozwiązania (Occam's Razor)
- Pomiar spójności (coherence)
- Detekcja nadmiarowej złożoności

**Jak Działa:**

1. **Simplicity Measurement:**
   - Liczba kroków w planie
   - Liczba zależności
   - Cyclomatic complexity
   - "Czy to można zrobić prościej?"

2. **Coherence Assessment:**
   - Czy wszystkie części pasują do siebie?
   - Czy nazwy są spójne?
   - Czy struktura jest logiczna?

3. **Efficiency Check:**
   - Czy to jest optymalna droga?
   - Czy można skrócić kroki?
   - Algorytm vs brute-force

4. **Aesthetic Judgment:**
   - "Czy to wygląda ładnie?" (dla UI)
   - "Czy kod jest czytelny?" (dla code)
   - Pattern matching przeciw best practices

**Output:**
- Beauty Score: 0-1
- Simplicity: 0-1
- Coherence: 0-1
- Efficiency: 0-1
- Aesthetic: 0-1

---

#### 3.2.3 goodness_analyzer.py - Analiza Intencji

**Odpowiedzialność:**
- Detekcja dysonansu poznawczego
- Wykrywanie manipulacji
- Analiza beneficjentów

**Jak Działa:**

1. **Intent Frequency Filter (FFT):**
   - Ekstrahuje linguistic features (sentiment, urgency, complexity)
   - Konwertuje do wektora
   - Aplikuje FFT (Fast Fourier Transform)
   - Porównuje spektrum z baselinefreq uency "czystej" intencji
   - Oblicza resonance score

2. **Dissonance Detection:**
   - Politeness score: liczba "please", "kindly", etc.
   - Risk score: liczba "sudo", "disable", "bypass", etc.
   - Dissonance = politeness × risk
   - Jeśli > 0.3 → COGNITIVE DISSONANCE

3. **Manipulation Detection:**
   - Flattery: "you're amazing", "brilliant"
   - Guilt: "I really need", "please help me"
   - Urgency: "immediately", "ASAP", "critical"
   - False scarcity: "last chance", "limited time"

4. **Beneficiary Analysis:**
   - Kto skorzysta z tej akcji?
   - Czy to wspólne dobro czy indywidualny interes?
   - Czy są ukryci beneficjenci?

**Output:**
- Goodness Score: 0-1
- Resonance: 0-1
- Dissonance Detected: TRUE/FALSE
- Manipulation Patterns: [list]
- Intent is Good: TRUE/FALSE

---

#### 3.2.4 intellectual_integrator.py - Integrator Intelektualny

**Odpowiedzialność:**
- Synteza Truth-Beauty-Goodness (Platonic Trinity)
- Obliczenie Intellectual Score
- Triple Veto enforcement

**Jak Działa:**

1. **Parallel Analysis:**
   ```
   truth, beauty, goodness = await asyncio.gather(
       truth_analyzer.analyze(request),
       beauty_analyzer.analyze(request),
       goodness_analyzer.analyze(request)
   )
   ```

2. **Harmonic Mean (zamiast arithmetic):**
   ```
   intellectual_score = 3 / (
       1/truth.score +
       1/beauty.score +
       1/goodness.score
   )
   ```
   - Harmonic mean jest bardziej surowy
   - Jeśli JEDNA wartość jest niska, cała średnia spada

3. **Triple Veto:**
   - Wszystkie 3 muszą być > 0.5
   - Jeśli ANY < 0.5 → STATUS: QUESTIONABLE
   - Jeśli ANY < 0.3 → STATUS: FLAWED

4. **Balance Measurement:**
   - Odchylenie standardowe między (T, B, G)
   - Jeśli < 0.1 → Perfectly Balanced
   - Jeśli > 0.4 → Highly Imbalanced

**Output:**
- Intellectual Score: 0-1
- Status: SOUND/QUESTIONABLE/FLAWED
- Harmonic Balance: 0-1
- Truth Report: {...}
- Beauty Report: {...}
- Goodness Report: {...}

---

### 3.3 perspectives/essential/ - Perspektywa Esencjonalna

**Struktura:**
```
perspectives/essential/
├── README.md
├── essential_integrator.py
├── unity_analyzer.py          # Jedność
├── harmony_analyzer.py        # Harmonia
└── purpose_analyzer.py        # Cel
```

**Cel:** Odpowiedź na pytanie "**CZY TO JEST NASZE POWOŁANIE?**"

---

#### 3.3.1 unity_analyzer.py - Analiza Jedności

**Odpowiedzialność:**
- Sprawdzenie czy akcja służy wspólnocie
- Detekcja działań samo-służących
- Pomiar wpływu na spójność systemu

**Jak Działa:**

1. **Beneficiary Mapping:**
   - Kim są beneficjenci tej akcji?
   - Lista: [agent_1, agent_2, ..., user, system]
   - Rozkład benefit: [20%, 10%, ..., 30%, 40%]

2. **Common Good Score:**
   ```
   common_good = (
       system_benefit × 0.4 +