# MemoryOS Local: Demontaż, zależności i wdrożenie do ADRION 369

## 1. Co realnie jest przydatne do wdrożenia lokalnie

Poniższe elementy są najbardziej wartościowe i zgodne z lokalnym modelem ADRION:

1. Warstwa pamięci dwupoziomowej (short-term i long-term) z automatycznym wygaszaniem.
2. Pętla OODA dla uczenia na interakcjach (Observe, Orient, Decide, Act).
3. Złote odpowiedzi (golden answers) jako benchmark jakości i źródło augmentacji.
4. Sędzia dryfu modelu (Judge) blokujący spadek jakości.
5. Lokalny audit trail z pełną historią decyzji i feedbacku.
6. Priorytetyzacja wspomnień: trafność semantyczna plus świeżość danych.
7. Kompaktowanie pamięci krótkiej przy przekroczeniu pojemności.
8. Twardy tryb privacy-first: brak eksportu danych poza hosta.

## 2. Rozmontowanie zasady działania na czynniki pierwsze

### 2.1 Warstwy i role

1. Ingestion: przyjęcie prompt i response.
2. Scoring: wyliczenie jakości VERA.
3. Guardrails: weryfikacja przez Judge.
4. Storage: zapis do short-term i ewentualna promocja do long-term.
5. Retrieval: pobranie kontekstu przy następnym zapytaniu.
6. Adaptacja: korekty użytkownika podnoszą jakość przyszłych odpowiedzi.

### 2.2 Cykl operacyjny

1. Observe:
- zapis interakcji i metadanych,
- wyliczenie VERA,
- zapis do short-term.

2. Orient:
- odbiór akceptacji lub korekty,
- aktualizacja feedback score,
- ewaluacja Judge.

3. Decide:
- analiza trendu jakości,
- wykrycie dryfu,
- rekomendacje doszlifowania modelu i promptyzacji.

4. Act:
- najpierw dopasowanie do golden answers,
- potem retrieval z pamięci wektorowej,
- zbudowanie kontekstu wzbogaconego do kolejnej odpowiedzi.

### 2.3 Mechanizm zależności

1. Behavior log zasila VERA.
2. VERA zasila Judge.
3. Judge wpływa na politykę blokowania i eskalacji.
4. Feedback użytkownika wpływa na promocję short-term do long-term.
5. Golden answers i long-term są preferowane nad short-term w retrieval.
6. Decay i compaction stabilizują koszt pamięci.

## 3. Mapa dopasowania do obecnej struktury ADRION

## 3.1 Co już jest gotowe

1. Local vector memory, dual collection i compaction: harmonia-dashboard/rag_memory.py
2. OODA, VERA, Judge, Golden answers: harmonia-dashboard/feedback_engine.py
3. Integracja API i endpointy pamięci: harmonia-dashboard/webhook_server.py
4. Zasady prywatności i lokalności: docs/LAWS.md
5. Architektura Genesis Record: docs/INTEGRATED-ADVANCED-ARCHITECTURE.md

## 3.2 Luki do domknięcia

1. Brak centralnej polityki retencji dla wszystkich logów i pamięci.
2. Brak wspólnego pliku konfiguracyjnego dla progów MemoryOS.
3. Brak jednolitego indeksu zdarzeń pamięci między modułami.
4. Brak formalnych SLO dla latencji retrieval i czasów promocji.

## 4. Kopiowanie usprawnień do rozwoju struktury systemu

Poniżej docelowe usprawnienia i gdzie je osadzić:

1. Unified Memory Policy:
- nowy plik: config/memoryos.local.yml
- cel: jeden punkt kontroli progów i retencji.

2. Memory Event Bus:
- integracja przez webhook_server jako warstwę publikacji eventów.
- eventy: interaction_logged, feedback_received, promoted_to_long_term, judge_blocked.

3. Governance Gates:
- przed zapisem danych wrażliwych: filtr danych i maskowanie.
- reguły: deny by default dla pól PII poza koniecznym minimum.

4. SLO i observability:
- metryki: retrieval_latency_ms, promotion_rate, judge_block_rate, memory_hit_rate.
- raportowanie: endpoint status plus eksport do istniejącego monitoringu.

5. Kontrakt jakości pamięci:
- minimalny próg jakości do promocji.
- polityka degradacji i usuwania starych, niskowartościowych wpisów.

## 5. Minimalna architektura produkcyjna local-first

1. Runtime:
- webhook_server przyjmuje interakcje i feedback,
- feedback_engine robi scoring i guardrails,
- rag_memory realizuje zapis i retrieval.

2. Storage:
- pliki JSON dla behavior i verdict,
- ChromaDB persistent dla pamięci semantycznej,
- Genesis Record dla audytu decyzji.

3. Security:
- wszystkie komponenty lokalne,
- zero cloud export,
- opcjonalne szyfrowanie backupu katalogów pamięci.

## 6. Kolejność wdrożenia

1. Etap A, konfiguracja:
- dodać i aktywować config/memoryos.local.yml,
- ujednolicić progi i limity.

2. Etap B, normalizacja eventów:
- dodać wspólne typy eventów pamięci,
- wpiąć je w pipeline logowania.

3. Etap C, governance:
- wdrożyć maskowanie danych wrażliwych,
- uruchomić checki zgodności przed zapisem.

4. Etap D, SLO i audyt:
- wdrożyć dashboard metryk pamięci,
- ustawić alarmy dla regresji jakości.

## 7. Kryteria akceptacji wdrożenia

1. 100 procent zdarzeń interakcyjnych ma ślad w behavior log.
2. Co najmniej 95 procent zapytań retrieval kończy się poniżej 2 sekund.
3. Judge block rate utrzymuje się poniżej 5 procent po stabilizacji.
4. Brak naruszeń G7 i brak eksportu danych poza hosta.
5. Widoczna poprawa VERA total w trendzie 14-dniowym.

## 8. Ryzyka i neutralizacja

1. Przerost pamięci:
- neutralizacja: limity, TTL, compaction, retencja.

2. Dryf jakości:
- neutralizacja: Judge, golden answers, analiza trendu.

3. Zanieczyszczenie danych:
- neutralizacja: walidacja wejścia, deduplikacja, scoring jakości.

4. Nadmiar danych wrażliwych:
- neutralizacja: maskowanie i minimalizacja zakresu zapisu.

## 9. Decyzja wdrożeniowa

Rekomendacja: wdrożyć lokalnie natychmiast w trybie etapowym.

Uzasadnienie:
1. Większość fundamentu MemoryOS jest już zaimplementowana.
2. Koszt domknięcia to głównie standaryzacja i governance.
3. Efekt biznesowy: szybsza adaptacja modelu, wyższa jakość odpowiedzi, pełna audytowalność.
