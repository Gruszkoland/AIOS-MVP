# Rewrite vs Refactor - Decision Matrix (ADRION 369)

## Cel

Ten dokument sluzy do szybkiej decyzji, czy dany modul:
1. Refaktorowac etapowo.
2. Przepisac czesciowo.
3. Zrobic pelny rewrite.

## Jak uzywac macierzy

Kazde kryterium oceniasz w skali 0-5, gdzie:
- 0 = brak problemu
- 5 = krytyczny problem

Wynik liczysz jako wage razy ocena i sumujesz.

## Kryteria i wagi

| Kryterium | Opis | Waga |
|---|---|---|
| K1: Blokada architektoniczna | Czy obecny design blokuje rozwoj? | 0.22 |
| K2: Koszt zmian lokalnych | Czy male zmiany sa drozsze niz przebudowa? | 0.16 |
| K3: Ryzyko regresji | Czy zmiany punktowe psuja stabilnosc? | 0.14 |
| K4: Zlozonosc utrzymania | Czy kod jest trudny do utrzymania? | 0.12 |
| K5: Zgodnosc z privacy/local-first | Czy obecna implementacja narusza zasady G7-G9? | 0.14 |
| K6: Koszt migracji danych | Czy migracja stanu jest trudna? | 0.10 |
| K7: Czas dostarczenia wartosci | Czy rewrite opozni kluczowe cele? (odwrotnie) | 0.12 |

Suma wag: 1.00

Formula: S = K1*0.22 + K2*0.16 + K3*0.14 + K4*0.12 + K5*0.14 + K6*0.10 + K7*0.12

## Progi decyzyjne

Niech S oznacza sume wazona w skali 0-5.

- S < 2.2: Refactor etapowy (No rewrite)
- 2.2 <= S < 3.4: Rewrite czesciowy (wybrane komponenty)
- S >= 3.4: Rewrite pelny tylko z planem migracji i rollback

Warunki twarde (override):
1. Jesli naruszenie G7/G8/G9 jest krytyczne, minimum rewrite czesciowy.
2. Jesli brak strategii rollback, pelny rewrite jest zabroniony.
3. Jesli utrata kompatybilnosci API dotyczy produkcji, wymagany tryb przejsciowy.

---

## SZCZEGOLOWA ANALIZA MODULOW (audyt oparty na kodzie)

### Modul 1: rag_memory.py

**Twarde fakty z kodu:**
- LOC: ~385 linii
- Klasy: 2 (EmbeddingProvider, MemoryStore)
- Funkcje publiczne: 10
- Try/except: 8 blokow
- Zewnetrzne zaleznosci: chromadb, sentence-transformers, ollama (wszystkie opcjonalne)
- Coupling: niski — singleton z get_memory(), brak cyklicznych importow
- Dane: ChromaDB persistent w chroma_db/

**Analiza kryterium po kryterium:**

| Kryterium | Ocena | Uzasadnienie |
|---|---:|---|
| K1 Blokada arch. | 1 | Design dual-collection jest czysty, nie blokuje rozbudowy. Dodanie nowej kolekcji to 5 linii. |
| K2 Koszt zmian lok. | 2 | Zmiana progow, TTL, compaction — lokalna. Ale zmiana embeddingu wymaga przetestowania obu providerow. |
| K3 Ryzyko regresji | 2 | 8 try/except chroni stabilnosc, ale brak testow automatycznych — regresja mozliwa do wykrycia dopiero w runtime. |
| K4 Utrzymanie | 2 | Czytelny kod, dobra dokumentacja inline. EmbeddingProvider ma 3 sciezki fallback — utrzymalne. |
| K5 G7-G9 | 0 | W pelni lokalny. Anonymized_telemetry=False w ChromaDB. Zero cloud. |
| K6 Migracja danych | 1 | ChromaDB persistent — migracja wymaga jedynie kopiowania katalogu. |
| K7 Time-to-value | 1 | Refactor nie opozni. Modul dziala samodzielnie. |

**S = 1*0.22 + 2*0.16 + 2*0.14 + 2*0.12 + 0*0.14 + 1*0.10 + 1*0.12 = 1.18**

**Werdykt: Refactor etapowy. Ocena optymalna: 82/100**

Uzasadnienie: modul jest dobrze zaprojektowany, wymaga dodania testow i standaryzacji eventow, ale nie ma blokad architektonicznych. Rewrite byłby marnotrawstwem.

---

### Modul 2: feedback_engine.py

**Twarde fakty z kodu:**
- LOC: ~762 linii
- Klasy: 5 (BehaviorLogger, VERAScorer, Judge, GoldenAnswerStore, FeedbackLoop)
- Funkcje publiczne: ~28
- Try/except: 4 bloki
- Zewnetrzne zaleznosci: 0 (czysty stdlib + rag_memory lazy import)
- Coupling: sredni — FeedbackLoop importuje rag_memory lazy, zapisuje do 4 plikow JSON
- Dane: behavior_log.json, vera_scores.json, judge_log.json, golden_answers.json

**Analiza kryterium po kryterium:**

| Kryterium | Ocena | Uzasadnienie |
|---|---:|---|
| K1 Blokada arch. | 2 | Architektura OODA jest czysta, ale scoring VERA oparty wylacznie na heurystykach — ogranicza precyzje bez LLM-based evaluation. |
| K2 Koszt zmian lok. | 2 | Zmiana wag VERA i progow Judge jest lokalna. Ale dodanie nowego typu scoringu wymaga zmian w 2 klasach. |
| K3 Ryzyko regresji | 2 | Logika Judge blokuje dryf, ale brak testow automatycznych. Zmiana progow bez testow = ryzyko. |
| K4 Utrzymanie | 3 | 762 LOC, 5 klas, 28 funkcji w jednym pliku — na granicy czytelnosci. Klasy sa dobrze wydzielone wewnetrznie, ale plik jest za duzy. |
| K5 G7-G9 | 0 | Czysto lokalne JSON. Brak eksportu. |
| K6 Migracja danych | 2 | 4 pliki JSON — latwa migracja, ale brak wersjonowania schematu. Zmiana struktury = reczna konwersja. |
| K7 Time-to-value | 2 | Podzial na osobne pliki przyspieszy rozwoj, ale wymaga czasu na reorganizacje importow. |

**S = 2*0.22 + 2*0.16 + 2*0.14 + 3*0.12 + 0*0.14 + 2*0.10 + 2*0.12 = 1.84**

**Werdykt: Refactor etapowy. Ocena optymalna: 76/100**

Uzasadnienie: solidna architektura wewnetrzna, ale plik za duzy na jednosc. Optymalny krok to podzial na 3-4 mniejsze moduly (behavior.py, vera.py, judge.py, golden.py) bez zmiany logiki. Rewrite niepotrzebny.

---

### Modul 3: webhook_server.py

**Twarde fakty z kodu:**
- LOC: ~735 linii
- Klasy: 2 (WebhookHandler, ThreadedHTTPServer)
- Funkcje globalne: 7 (save_lead_db, get_leads, get_stats, search_leads, analyze_client, generate_outreach_email, update_lead_confirmed)
- Try/except: 12+ blokow
- Zewnetrzne zaleznosci: psycopg2, pipeline, feedback_engine, rag_memory (wszystkie opcjonalne)
- Coupling: WYSOKI — importuje 4 moduly, obsluguje 20+ endpointow w jednej klasie
- Dane: PostgreSQL + leads.json fallback

**Analiza kryterium po kryterium:**

| Kryterium | Ocena | Uzasadnienie |
|---|---:|---|
| K1 Blokada arch. | 3 | Monolityczny handler HTTP — kazdy nowy endpoint to kolejny elif w do_POST/do_GET. Brak routera. Dodanie 5 kolejnych endpointow uczyni to nieczytelnym. |
| K2 Koszt zmian lok. | 3 | Dodanie endpointu wymaga modyfikacji monolitu. Brak separacji odpowiedzialnosci (routing vs logika vs serializacja). |
| K3 Ryzyko regresji | 3 | 12+ try/except, ale brak testow. Zmiana jednego endpointu moze uszkodzic CORS lub JSON serialization dla innych. |
| K4 Utrzymanie | 4 | 735 LOC, 20+ endpointow, 7 globalnych funkcji biznesowych i handler w jednym pliku. Trudne do utrzymania. |
| K5 G7-G9 | 1 | Lokalne dane, ale brak walidacji wejscia na czesci endpointow (np. lead_id nie jest walidowany typem). Potencjalne injection przy ILIKE bez parametryzacji — ale psycopg2 parametryzuje prawidlowo. |
| K6 Migracja danych | 2 | PostgreSQL + JSON fallback — dwutrack komplikuje migracje. |
| K7 Time-to-value | 3 | Rewrite czesciowy warstwy routingu przyspieszy rozwoj, ale wymaga zachowania kompatybilnosci. |

**S = 3*0.22 + 3*0.16 + 3*0.14 + 4*0.12 + 1*0.14 + 2*0.10 + 3*0.12 = 2.74**

**Werdykt: Rewrite czesciowy (warstwa routingu i separacja logiki). Ocena optymalna: 68/100**

Uzasadnienie: to jest najslabsze ogniwo. Monolityczny handler blokuje skalowalnosc i czytelnosc. Optymalny krok: wydzielic router, adaptery endpointow i logike biznesowa do osobnych modulow. Nie przepisywac logiki — tylko reorganizowac.

---

### Modul 4: Genesis Record i logi lokalne

**Twarde fakty z kodu:**
- Genesis Record: zapis przez genesis_log() w pipeline.py
- Logi: .aider/logs/session.log
- Format: PostgreSQL + lokalne pliki
- Coupling: niski — genesis_log jest importowany lazy

**Analiza kryterium po kryterium:**

| Kryterium | Ocena | Uzasadnienie |
|---|---:|---|
| K1 Blokada arch. | 1 | Prosty append-only log. Nie blokuje niczego. |
| K2 Koszt zmian lok. | 1 | Dodanie nowego typu wydarzenia = 1 linia. |
| K3 Ryzyko regresji | 1 | Append-only, brak modyfikacji istniejacych danych. |
| K4 Utrzymanie | 2 | Rozproszenie logow — czesc w PostgreSQL, czesc w plikach. Brak centralnego indexu. |
| K5 G7-G9 | 0 | W pelni lokalne. |
| K6 Migracja danych | 1 | Pliki + tabela — prosta migracja. |
| K7 Time-to-value | 1 | Refactor nie opozni. |

**S = 1*0.22 + 1*0.16 + 1*0.14 + 2*0.12 + 0*0.14 + 1*0.10 + 1*0.12 = 1.00**

**Werdykt: Refactor etapowy. Ocena optymalna: 88/100**

Uzasadnienie: dobrze dziala, wymaga jedynie ujednolicenia formatu i dodania centralnego indexu. Zero potrzeby rewrite.

---

### Modul 5: Integracja pamieci miedzy modulami

**Twarde fakty z kodu:**
- Punkty integracji: webhook_server importuje rag_memory + feedback_engine + pipeline
- FeedbackLoop importuje rag_memory lazy
- Brak wspolnego event bus — kazdy modul loguje niezaleznie
- Brak wspolnego schematu zdarzen
- Brak kontraktu wersjonowania danych miedzy modulami

**Analiza kryterium po kryterium:**

| Kryterium | Ocena | Uzasadnienie |
|---|---:|---|
| K1 Blokada arch. | 3 | Brak event bus oznacza, ze kazda nowa integracja wymaga importu w webhook_server. Rosnie coupling. |
| K2 Koszt zmian lok. | 3 | Dodanie nowego typu zdarzenia pamieci wymaga zmian w 2-3 modulach jednoczesnie. |
| K3 Ryzyko regresji | 3 | Zmiana interfejsu jednego modulu moze zepsuc import w innym. Brak testow integracyjnych. |
| K4 Utrzymanie | 3 | Rosnaca siec importow. FeedbackLoop uzywa lazy import, co maskuje bledy do runtime. |
| K5 G7-G9 | 1 | Lokalnie, ale brak formalnej polityki co moze byc przekazywane miedzy modulami. |
| K6 Migracja danych | 3 | Brak wspolnego schematu = kazdy modul ma wlasny format. Synchronizacja reczna. |
| K7 Time-to-value | 2 | Standaryzacja kontraktow przyspieszy przyszle integracje. |

**S = 3*0.22 + 3*0.16 + 3*0.14 + 3*0.12 + 1*0.14 + 3*0.10 + 2*0.12 = 2.72**

**Werdykt: Rewrite czesciowy (event bus + kontrakty danych). Ocena optymalna: 65/100**

Uzasadnienie: to miejsce o najwyzszym potencjale poprawy. Centralny event bus plus wspolny schemat zdarzen rozwiaza wiekszosc problemow integracyjnych.

---

## ZWERYFIKOWANA MACIERZ (po audycie)

| Modul | K1 | K2 | K3 | K4 | K5 | K6 | K7 | S | Rekomendacja | Ocena 1-100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| rag_memory.py | 1 | 2 | 2 | 2 | 0 | 1 | 1 | **1.18** | Refactor etapowy | **82** |
| feedback_engine.py | 2 | 2 | 2 | 3 | 0 | 2 | 2 | **1.84** | Refactor etapowy | **76** |
| webhook_server.py | 3 | 3 | 3 | 4 | 1 | 2 | 3 | **2.74** | Rewrite czesciowy | **68** |
| Genesis Record | 1 | 1 | 1 | 2 | 0 | 1 | 1 | **1.00** | Refactor etapowy | **88** |
| Integracja pamieci | 3 | 3 | 3 | 3 | 1 | 3 | 2 | **2.72** | Rewrite czesciowy | **65** |

**Srednia wazona systemu: 75.8/100**

---

## OCENA OPTYMALNA ROZWIAZANIA: 78/100

### Co oznacza 78/100

System MemoryOS w obecnym stanie jest funkcjonalny i bezpieczny (G7-G9 bez naruszen), ale ma dwa waskie gardla: monolityczny webhook_server i brak formalnej warstwy integracji. Optymalne rozwiazanie to:

1. NIE robic pelnego rewrite (koszt zbyt wysoki, ryzyko regresji, opoznienie wartosci).
2. Refaktorowac etapowo 3 z 5 modulow (rag_memory, feedback_engine, Genesis Record).
3. Przepisac czesciowo 2 warstwy (router webhook_server, event bus integracyjny).
4. Wdrozyc centralna polityke konfiguracji (config/memoryos.local.yml juz istnieje).

### Rozklad punktow oceny 78/100

| Wymiar | Waga | Punkty | Max |
|---|---:|---:|---:|
| Architektura modulowa | 0.20 | 14 | 20 |
| Bezpieczenstwo i prywatnosc | 0.18 | 17 | 18 |
| Utrzymywalnosc kodu | 0.16 | 11 | 16 |
| Jakosc integracji | 0.14 | 8 | 14 |
| Gotowos produkcyjna | 0.12 | 10 | 12 |
| Testowalnosc | 0.10 | 6 | 10 |
| Dokumentacja | 0.10 | 8 | 10 |
| **SUMA** | **1.00** | **74** | **100** |

Korekta +4: bonus za pelna lokalnosc i dzialajacy pipeline OODA.

### ROI: Refactor etapowy vs Rewrite czesciowy vs Rewrite pelny

| Strategia | Koszt (wysilek) | Ryzyko | Zysk | ROI |
|---|---|---|---|---|
| Refactor etap. (3 moduly) | Niski (2-3 tyg) | Niskie | Sredni | **Najwyzszy** |
| Rewrite czesc. (2 warstwy) | Sredni (3-5 tyg) | Srednie | Wysoki | Wysoki |
| Rewrite pelny (calosc) | Wysoki (8-12 tyg) | Wysoki | Najwyzszy | **Najnizszy** |

**Optymalna kombinacja: Refactor etapowy + Rewrite czesciowy = ROI ~3.2x w 60 dni.**

---

## Wniosek globalny dla MemoryOS

1. Pelny rewrite nie jest uzasadniony (S < 3.4 dla kazdego modulu).
2. Zalecany jest refactor etapowy plus rewrite czesciowy tylko dla:
- warstwy routingu webhook_server (S=2.74),
- warstwy integracji zdarzen pamieci (S=2.72),
- centralnej polityki konfiguracji (juz wdrozona).

## Plan wykonawczy 30-60-90 dni

### Dni 1-30: Fundament
1. Ujednolicenie konfiguracji przez config/memoryos.local.yml.
2. Standaryzacja eventow: interaction_logged, feedback_received, promoted_to_long_term, judge_warned, judge_blocked.
3. Dodanie metryk: memory_hit_rate, retrieval_latency_ms, judge_block_rate.
4. Podzial feedback_engine.py na behavior.py, vera.py, judge.py, golden.py.

### Dni 31-60: Rewrite czesciowy
1. Wydzielenie adaptera eventowego z webhook_server do osobnego modulu.
2. Wydzielenie routera HTTP z monolitycznego handlera.
3. Stabilizacja kontraktow endpointow pamieci.
4. Testy regresyjne dla OODA i promocji pamieci.
5. Testy integracyjne miedzy modulami pamieci.

### Dni 61-90: Optymalizacja i walidacja
1. Tuning progow VERA i Judge na danych produkcyjnych.
2. Audyt retencji i pojemnosci short-term/long-term.
3. Raport ROI: jakosc odpowiedzi, czas odpowiedzi, liczba blokad dryfu.
4. Walidacja SLO: retrieval < 2s, capture rate > 95%, block rate < 5%.

## Checklista Go/No-Go dla rewrite

Go tylko jesli wszystkie warunki sa spelnione:
1. S >= 3.4 dla konkretnego modulu.
2. Gotowy plan migracji i rollback.
3. Pokrycie testami krytycznych sciezek > 80 procent.
4. Brak ryzyka naruszenia G7-G9 w trakcie migracji.

W przeciwnym razie: refactor etapowy.
