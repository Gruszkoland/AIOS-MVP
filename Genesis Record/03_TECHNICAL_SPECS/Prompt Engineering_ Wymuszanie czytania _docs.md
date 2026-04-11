Aby AI skutecznie korzystało z zewnętrznej pamięci, musisz przestać traktować ją jako "wyszukiwarkę", a zacząć jako **system operacyjny**, który ma swoje procedury startowe i końcowe.  
Oto konkretne techniki implementacji metodologii Jake'a Van Cliefa w Twoim workflow.

## **1\. Prompt Engineering: Wymuszanie czytania /docs**

Kluczem jest umieszczenie instrukcji w tzw. **System Prompcie** lub w pliku konfiguracyjnym projektu (np. .clauderc lub CLAUDE.md), który model czyta jako pierwszy.

### **Skuteczny System Prompt (Template):**

"Działaj jako inżynier oprogramowania. Twój proces myślowy musi być zawsze poprzedzony sprawdzeniem zasobów lokalnych.  
**Procedura obowiązkowa:**

1. Zanim odpowiesz na jakiekolwiek pytanie techniczne, przeskanuj folder /docs.  
2. Jeśli w /docs istnieje plik SKILLS.md lub ARCHITECTURE.md, wykorzystaj zawarte tam wzorce zamiast proponować nowe.  
3. Jeśli instrukcja użytkownika jest sprzeczna z zasadami w CLAUDE.md, priorytetyzuj plik CLAUDE.md.  
4. Jeśli w /docs brakuje informacji o bieżącym zadaniu, zapytaj o nie, zamiast zgadywać (Zero-Inference)."

**Dlaczego to działa?** Zdejmujesz z modelu ciężar podejmowania decyzji "jak pisać kod". On ma tylko naśladować wzorce, które mu tam zostawiłeś.

## **2\. Automatyzacja /finish: Szablon PROGRESS.md**

Komenda /finish to sygnał dla AI, aby dokonało zrzutu pamięci operacyjnej do pliku trwałego. Zapobiega to tzw. "rozmyciu kontekstu" przy następnym logowaniu.

### **Szablon podsumowania (do wklejenia do instrukcji Claude):**

Poproś Claude, aby przy komendzie /finish generował wpis w poniższym formacie Markdown i dopisywał go na górze pliku PROGRESS.md:  
`## [DATA: YYYY-MM-DD] - Podsumowanie Sesji`  
`**Status:** [Zakończone / W toku / Zablokowane]`

`### ✅ Wykonane zadania:`  
`* [Zadanie 1]: Krótki opis co zostało zaimplementowane.`  
`* [Zadanie 2]: Zmiany w strukturze plików.`

`### 🧠 Kluczowe wnioski (Nowe umiejętności):`  
`* [Ważna informacja]: Np. "Problem z API rozwiązany przez zmianę timeoutu na 30s".`

`### 🚀 Następne kroki:`  
`1. [Krok 1]: Co trzeba zrobić jutro rano jako pierwsze?`  
`2. [Krok 2]: Na co uważać przy kolejnej implementacji?`

`---`

### **Przykład użycia w rozmowie:**

**Ty:** "Dobra, na dziś koniec. Uruchom procedurę /finish i zaktualizuj PROGRESS.md."  
**Claude:** "Oczywiście. Przeanalizowałem nasze dzisiejsze postępy w module płatności. Właśnie dopisałem podsumowanie do PROGRESS.md. Jutro zaczniemy od testów integracyjnych, o czym wspomniałem w sekcji 'Następne kroki'."

## **Porównanie: Jak to oszczędza Twoje zasoby?**

| Metoda | Bez systemu plików | Z systemem /docs i /finish |
| :---- | :---- | :---- |
| **Start sesji** | Tłumaczysz wszystko od nowa (500-1000 tokenów). | Mówisz: "Przeczytaj PROGRESS.md" (50 tokenów). |
| **Błędy** | AI powtarza te same błędy co wczoraj. | AI czyta ostrzeżenie w SKILLS.md i unika błędu. |
| **Spójność** | Kod z czasem staje się chaotyczny. | Kod trzyma się rygorystycznie Twoich wzorców. |

## **Możliwości do zgłębiania tematu**

* **Auto-indeksowanie:** Dowiedz się, jak napisać skrypt Bash, który co wieczór przeszukuje Twój kod i automatycznie generuje streszczenie nowych funkcji do SKILLS.md.  
* **RAG (Retrieval-Augmented Generation) lokalny:** Zbadaj narzędzia takie jak *Continue.dev* (wtyczka do VS Code), która automatycznie indeksuje Twój folder /docs i podsuwa go Claude'owi w tle.

**Czy chciałbyś, abym przygotował dla Ciebie pierwszy, gotowy plik CLAUDE.md, który możesz wrzucić do swojego projektu, aby przetestować to w praktyce?**