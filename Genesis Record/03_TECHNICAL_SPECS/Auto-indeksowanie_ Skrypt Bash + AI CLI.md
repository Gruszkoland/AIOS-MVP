Zarówno auto-indeksowanie, jak i lokalny RAG, to kroki milowe w kierunku budowy "cyfrowego mózgu" Twojego projektu. Zamiast ręcznie aktualizować dokumentację, tworzysz system, który samoczynnie uczy się na podstawie Twojego kodu.

## **1\. Auto-indeksowanie: Skrypt Bash \+ AI CLI**

Aby skrypt mógł "streszczać" funkcje, musi on nie tylko znaleźć pliki, ale też wysłać ich fragmenty do modelu językowego (np. przez anthropic-cli lub prosty curl do API).

### **Koncepcja skryptu index\_skills.sh:**

Skrypt ten znajduje pliki zmienione w ciągu ostatnich 24 godzin, wyciąga z nich nowe funkcje i prosi AI o przygotowanie krótkiego wpisu do SKILLS.md.  
`#!/bin/bash`

`# 1. Znajdź pliki zmienione w ciągu ostatnich 24h (wykluczając foldery typu node_modules)`  
`changed_files=$(find . -name "*.py" -mtime -1 -not -path "*/.*")`

`for file in $changed_files; do`  
    `echo "Analizowanie: $file"`  
      
    `# 2. Wyciągnij nową logikę (uproszczony przykład - bierze całą treść)`  
    `content=$(cat "$file")`  
      
    `# 3. Wyślij do Claude (używając np. narzędzia 'anthropic' w CLI)`  
    `# Prompt nakazuje stworzenie sformatowanego wpisu do SKILLS.md`  
    `summary=$(echo "Na podstawie tego kodu stwórz wpis do biblioteki umiejętności: $content" | anthropic api messages --model claude-3-5-sonnet)`  
      
    `# 4. Dopisz do SKILLS.md`  
    `echo -e "\n### Nowa umiejętność z $file\n$summary" >> docs/SKILLS.md`  
`done`

`echo "Indeksowanie zakończone."`

**Automatyzacja (Cron):** Aby skrypt uruchamiał się co wieczór (np. o 23:00), dodaj wpis do crontab \-e: 0 23 \* \* \* /sciezka/do/twojego/projektu/index\_skills.sh

## **2\. Lokalny RAG: Continue.dev (VS Code)**

**Continue** to potężne narzędzie typu open-source, które działa jako most między Twoim IDE a modelem Claude. To właśnie on realizuje wizję "podsuwania dokumentacji w tle".

### **Jak Continue.dev realizuje RAG:**

1. **Indeksowanie bazy kodu:** Continue tworzy lokalny indeks wektorowy (osadzony na Twoim dysku) dla całego projektu.  
2. **Symbol @docs:** Możesz wpisać w czacie @docs, a Continue automatycznie przeszuka Twój folder /docs i dołączy najbardziej trafne fragmenty do promptu.  
3. **Kontekst na żądanie:** Nie musisz wklejać kodu. Możesz zaznaczyć fragment i nacisknąć Cmd/Ctrl \+ L, a on trafi do Claude'a wraz z kontekstem innych powiązanych plików.

## **3\. Integracja: Jak te dwa systemy współpracują?**

Prawdziwa moc pojawia się, gdy połączysz te dwa podejścia w jeden obieg informacji:

| Proces | Narzędzie | Co się dzieje? |
| :---- | :---- | :---- |
| **Tworzenie** | Ty \+ Claude | Piszesz kod w VS Code. |
| **Ekstrakcja** | Skrypt Bash | Wieczorem skrypt wyciąga "esencję" Twojej pracy do SKILLS.md. |
| **Indeksowanie** | Continue.dev | Wtyczka zauważa nowy wpis w SKILLS.md i dodaje go do bazy wektorowej. |
| **Przywołanie** | RAG | Następnego dnia, gdy pytasz o podobny problem, Continue automatycznie wstrzykuje wpis z SKILLS.md do rozmowy. |

## **Możliwości do zgłębiania tematu**

* **Vector Databases (np. LanceDB):** Continue używa ich pod maską. Zrozumienie, jak działają "embeddings" (wektory), pomoże Ci lepiej strukturyzować pliki tekstowe.  
* **Pre-commit Hooks:** Zamiast skryptu co wieczór, możesz uruchamiać indeksowanie przy każdym git commit, co daje jeszcze świeższą dokumentację.  
* **Model Context Protocol (MCP):** Nowy standard od Anthropic, który pozwala Claude'owi na bezpieczne i ustrukturyzowane łączenie się z Twoimi lokalnymi bazami danych i plikami.

**Czy chciałbyś, abym pomógł Ci skonfigurować plik config.json dla Continue.dev, tak aby optymalnie korzystał z Twojego folderu /docs?**