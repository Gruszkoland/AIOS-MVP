Analiza metod Jake'a Van Cliefa ujawnia, że jego sukces nie wynika z używania „lepszych” modeli, ale z rygorystycznej **inżynierii kontekstu poprzez strukturę folderów**. Jake twierdzi, że "folder jest Twoją architekturą myślenia", a chaos w plikach to najszybsza droga do spalenia limitów tokenów i halucynacji AI.  
Oto dogłębny podział jego metodologii:

## **1\. Fundament: System "Librarian" (Bibliotekarz)**

Zamiast budować skomplikowane "agenty", Jake buduje systemy oparte na **strukturze plików**. Kluczem jest to, aby Claude nie musiał "szukać" informacji, bo każde wyszukiwanie zużywa tzw. *context jar* (słoik kontekstu).

* **Zasada 30 minut:** Jeśli uporządkowanie folderów zajmuje 30 minut, oszczędza to godziny błędów AI w przyszłości.  
* **Hierarchia Kontekstu:** Każdy plik w określonym folderze to decyzja o tym, co AI ma "widzieć" w danym momencie. Dzięki temu model nie przetwarza niepotrzebnych danych.

### **Strategia plików kontrolnych (CLAUDE.md)**

To najważniejszy element jego systemu. Plik CLAUDE.md działa jak "mapa drogowa" dla modelu:

* **Root CLAUDE.md:** Zawiera globalne preferencje, Twoją tożsamość i uniwersalne zasady pracy.  
* **Project CLAUDE.md:** Specyficzne instrukcje dla konkretnego zadania, lista dostępnych narzędzi i opis struktury danego projektu.  
* **Efekt:** Claude ładuje ten plik na samym początku rozmowy (w najsilniejszej części okna kontekstowego), co eliminuje zgadywanie.

## **2\. Automatyzacja "Infrastructure-as-Context"**

Jake wykorzystuje narzędzia takie jak **Claude Code** do budowania systemów, które same się utrzymują.

* **Session-Init Hooks:** Skrypty, które uruchamiają się automatycznie przy starcie sesji. Regenerują indeksy umiejętności i czyszczą pliki tymczasowe starsze niż 7 dni.  
* **Modularne biblioteki procesów:** Zamiast pisać kod od zera, Jake posiada foldery z "procesami" (np. do animacji w Remotion czy skryptów Python). Prosi Claude'a: "Użyj procesu z folderu X, aby przetworzyć plik Y".  
* **Komenda /finish:** Na koniec sesji model analizuje, co zostało zrobione, i sugeruje, jakie kroki podjąć jutro, co pozwala na płynną kontynuację pracy bez "przypominania" AI o co chodziło.

## **3\. Strategia "Zero-Inference" (Zero domysłów)**

Największym błędem jest proszenie AI: "Zrób mi aplikację". Jake stosuje podejście **deklaratywne**:

1. **Definicja w naturalnym języku:** Opisuje proces w dokumencie tekstowym umieszczonym w folderze.  
2. **Biblioteki pomocnicze:** Dostarcza Claude'owi gotowe moduły, z których ten ma korzystać.  
3. **Orkiestracja:** AI pełni rolę "montażysty", który łączy klocki, a nie "architekta", który musi wszystko wymyślić.

### **Podsumowanie możliwości kontynuacji:**

* **Claude Code & Codex:** Zbadaj, jak te narzędzia integrują się bezpośrednio z Twoim systemem plików (to tam Jake osiąga największą wydajność).  
* **Remotion:** Jeśli interesują Cię animacje, Jake używa tej biblioteki React do generowania wideo za pomocą skryptów pisanych przez AI.  
* **Systemy Skill Indexing:** Dowiedz się, jak tworzyć pliki .md, które służą jako "pamięć długotrwała" Twoich projektów.

[Jak naprawić strukturę folderów dla Claude](https://www.youtube.com/watch?v=MkN-ss2Nl10)  
Ten film szczegółowo wyjaśnia, dlaczego Twoja struktura folderów jest ważniejsza niż wybór modelu i jak zaprojektować "plan piętra", po którym AI będzie mogło poruszać się bez marnowania tokenów.  
Który element tego systemu – automatyczne skrypty startowe czy tworzenie mapy projektu w CLAUDE.md – chciałbyś wdrożyć jako pierwszy?