Narzędzia te stanowią brakujące ogniwo między czatem AI a Twoim lokalnym komputerem. Pozwalają one Claude'owi nie tylko "pisać o kodzie", ale bezpośrednio operować na Twojej strukturze plików, co jest fundamentem metody Jake’a Van Cliefa.

## **1\. Claude Code & Codex: AI w systemie plików**

W przeciwieństwie do webowego interfejsu Claude.ai, **Claude Code** to narzędzie CLI (wiersza poleceń), które działa bezpośrednio w Twoim terminalu.

### **Jak wygląda integracja?**

* **Bezpośredni dostęp do plików (Read/Write):** Claude może samodzielnie przeszukiwać Twój projekt, czytać pliki i – co najważniejsze – zapisywać w nich zmiany. Nie musisz już kopiować kodu z czatu.  
* **Wykonywanie komend terminala:** Claude Code może uruchamiać testy (np. pytest lub npm test), sprawdzać błędy w terminalu i na ich podstawie poprawiać kod, aż przejdzie on weryfikację.  
* **Integracja z Git:** Narzędzie to potrafi samodzielnie tworzyć commity z opisem wykonanych zmian, co idealnie wpisuje się w bezpieczne eksperymentowanie.

## **2\. Systemy Skill Indexing: Twoja "Pamięć Długotrwała"**

Problem z AI polega na tym, że "zapomina" ona o ustaleniach z poprzednich dni. **Skill Indexing** rozwiązuje to poprzez tworzenie plików .md, które służą jako zewnętrzna pamięć Twojego projektu.

### **Jak tworzyć pliki .md do indeksowania umiejętności?**

Zamiast trzymać wszystko w głowie modelu, tworzysz folder /docs lub /skills, w którym przechowujesz:

1. **CLAUDE.md (Instrukcje operacyjne):**  
   * **Styl kodu:** "Używaj Type Hinting w Pythonie".  
   * **Komendy:** "Buduj projekt komendą make build".  
   * **Kontekst projektu:** "To jest mikroserwis odpowiedzialny za płatności Stripe".  
2. **SKILLS.md (Biblioteka rozwiązań):** Jeśli raz rozwiążesz z AI trudny problem (np. specyficzne formatowanie danych w Remotion), poproś AI o zapisanie tego rozwiązania w SKILLS.md.  
   * *Struktura wpisu:* Cel \-\> Fragment kodu \-\> Jak go użyć.  
   * *Przy następnej sesji:* Mówisz: "Sprawdź w SKILLS.md, jak ostatnio rozwiązywaliśmy problem X i użyj tej samej metody".  
3. **PROGRESS.md (Dziennik postępu):** Plik, który Claude aktualizuje na koniec każdej sesji komendą /finish. Dzięki temu przy następnym logowaniu AI dokładnie wie, na czym skończyło i jakie są następne kroki.

## **Zalety podejścia "Infrastructure-as-Context"**

| Cecha | Standardowy Czat | Claude Code \+ Skill Indexing |
| :---- | :---- | :---- |
| **Pamięć** | Ograniczona do jednej rozmowy. | Trwała, zapisana w plikach projektu. |
| **Tokeny** | Marnowane na wklejanie kodu. | Oszczędzane przez czytanie tylko mapy plików. |
| **Błędy** | Częste "halucynacje" kodu. | Minimalne, dzięki weryfikacji w terminalu. |
| **Skala** | Pojedyncze pliki. | Zarządzanie całymi repozytoriami. |

### **Możliwości do zgłębiania tematu:**

* **Instalacja Claude Code:** Sprawdź oficjalną dokumentację Anthropic dotyczącą narzędzi CLI (obecnie w fazie beta/early access).  
* **Prompt Engineering dla plików Markdown:** Naucz się, jak pisać instrukcje, które nakazują AI *zawsze* sprawdzać folder /docs przed udzieleniem odpowiedzi.  
* **Automatyzacja /finish:** Spróbuj stworzyć własny szablon podsumowania sesji, który AI będzie dopisywać do PROGRESS.md.

Który z tych elementów chciałbyś teraz "rozbić na atomy" i spróbować wdrożyć w swoim projekcie?