# Modele LLM do użytku offline

Status: Sukces

Wykonano:
- Analiza dostępnych modeli Open Source i ich przystosowania do działania offline
- Opracowanie listy środowisk uruchomieniowych

Następny krok:
- Wybór i instalacja preferowanego środowiska (np. LM Studio / Ollama) oraz pobranie wybranego modelu.

Logi systemowe:
- Utworzono dokument z listą modeli i narzędzi.

---

### Popularne modele LLM (Open Source), które można używać offline:

1. **Meta Llama 3 / Llama 3.1**
   - Wersje: 8B (idealna na laptopy), 70B (wymaga potężnego PC/Serwera).
   - Charakteryzuje się świetnym stosunkiem wydajności do wymagań.

2. **Mistral / Mixtral (Mistral AI)**
   - Mistral 7B: Bardzo wydajny model na słabsze maszyny.
   - Mixtral 8x7B (MoE): Model oparty na mieszance ekspertów, bardzo inteligentny.

3. **Microsoft Phi-3**
   - Mini / Small: Niezwykle wydajne modele dedykowane na urządzenia o małej ilości zasobów (telefony, słabe PC).

4. **Google Gemma 2**
   - Wersje: m.in. 9B, 27B. 
   - Bardzo wysoka skuteczność i jakość generowanego tekstu.

5. **Qwen 2 (Alibaba)**
   - Świetnie radzi sobie z wieloma językami oraz z programowaniem. Wersje od 0.5B do 72B.

6. **Cohere Command R / R+**
   - Znakomicie radzą sobie z RAG (Retrieval-Augmented Generation) i językami innymi niż angielski.

### Narzędzia do pobierania i uruchamiania modeli (Offline):

1. **LM Studio**
   - Gotowa aplikacja (Windows, Mac, Linux) z interfejsem przypominającym ChatGPT. Pozwala wyszukiwać modele (z HuggingFace), pobierać je jednym kliknięciem i od razu testować. Automatycznie dobiera optymalizacje sprzętowe.

2. **Ollama**
   - Narzędzie operujące z terminala (można podpiąć mnóstwo nakładek graficznych np. *AnythingLLM*, *Open WebUI*). Uruchamianie sprowadza się do wpisania komendy np. `ollama run llama3`.

3. **GPT4All**
   - Aplikacja pozwalająca uruchamiać modele LLM na zwykłym procesorze (CPU) – idealna jeśli nie posiadasz dedykowanej, mocnej karty graficznej. Zoptymalizowana do prywatności.

4. **Text-generation-webui (Oobabooga)**
   - "Swiss Army knife" w świecie LLM. Bardzo rozbudowany interfejs webowy, dla zaawansowanych użytkowników chcących pełnej kontroli parametrów i ładowania modeli w różnych kwantyzacjach.

**Rekomendacja na start:** 
Pobierz aplikację **LM Studio**, wyszukaj w niej "Llama 3 8B Instruct" w formacie **GGUF** (np. od twórcy *Bartowski* lub *TheBloke*) i kliknij pobierz. Następnie przejdź do zakładki Chat i możesz bezpiecznie, offline rozmawiać ze swoim modelem.
