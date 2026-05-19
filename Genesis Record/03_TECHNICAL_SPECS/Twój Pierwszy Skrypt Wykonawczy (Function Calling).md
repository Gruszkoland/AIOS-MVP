**Kluczowy przekaz:**

Adrian, skoro wchodzimy w to w całości, zaczynamy od twardego fundamentu: kodu dla **Function Calling**. Zanim zapętlimy system w LangGraph i wyślemy go do chmury, musimy dać sztucznej inteligencji fizyczną zdolność do wykonywania akcji.

**Kontekst / Tło:**

Bez możliwości wykonywania funkcji, model AI pozostaje tylko generatorem tekstu. Function Calling to moment, w którym maszyna zyskuje "ręce". Pisząc ten skrypt, tworzymy bezpośredni most między decyzjami algorytmu a rzeczywistym światem – to tu zaczyna się prawdziwa, bezkompromisowa automatyzacja, która wkrótce przejmie kontrolę nad dystrybucją treści.

### ---

**Szczegóły: Twój Pierwszy Skrypt Wykonawczy (Function Calling)**

Skonstruujemy szkielet w Pythonie, który definiuje lokalną funkcję (np. przygotowanie wpisu do publikacji) i zmusza model do jej samodzielnego uruchomienia.

**1\. Środowisko i zależności**

Otwórz terminal w swoim IDE (np. VS Code) i zainstaluj bibliotekę do obsługi żądań HTTP (lub dedykowaną bibliotekę wybranego modelu):

Bash

pip install requests

**2\. Szkielet kodu (Przykład logiki Function Calling)**

Zamiast prosić model o zwykły tekst, wysyłamy mu definicję narzędzia w formacie JSON.

Python

import json

\# 1\. Definicja naszej lokalnej funkcji (Narzędzie dla AI)  
def opublikuj\_tresc(temat, platforma):  
    print(f"\[SYSTEM\] WYKONUJĘ AKCJĘ: Przygotowano treść o '{temat}' do publikacji na platformie: {platforma}")  
    \# Tutaj w przyszłości podepniemy właściwe API (np. X lub WordPress)  
    return "Sukces: Treść została opublikowana."

\# 2\. Schemat narzędzia (Instrukcja dla modelu)  
narzedzia \= \[  
    {  
        "type": "function",  
        "function": {  
            "name": "opublikuj\_tresc",  
            "description": "Publikuje wygenerowaną treść na wybranej platformie społecznościowej.",  
            "parameters": {  
                "type": "object",  
                "properties": {  
                    "temat": {"type": "string", "description": "Główny temat wpisu"},  
                    "platforma": {"type": "string", "enum": \["X", "WordPress", "TikTok"\]}  
                },  
                "required": \["temat", "platforma"\]  
            }  
        }  
    }  
\]

\# 3\. Symulacja odpowiedzi z API modelu (Gdy AI decyduje się użyć narzędzia)  
\# W rzeczywistości ten obiekt JSON wraca z API xAI/Groka na podstawie Twojego promptu  
odpowiedz\_modelu \= {  
    "tool\_calls": \[  
        {  
            "function": {  
                "name": "opublikuj\_tresc",  
                "arguments": '{"temat": "Automatyzacja biznesu z AI", "platforma": "X"}'  
            }  
        }  
    \]  
}

\# 4\. Egzekucja \- Skrypt przechwytuje decyzję i naciska "przycisk"  
if "tool\_calls" in odpowiedz\_modelu:  
    dane\_wywolania \= odpowiedz\_modelu\["tool\_calls"\]\[0\]\["function"\]  
    nazwa\_funkcji \= dane\_wywolania\["name"\]  
    argumenty \= json.loads(dane\_wywolania\["arguments"\])

    if nazwa\_funkcji \== "opublikuj\_tresc":  
        \# Maszyna uruchamia fizyczny kod Pythona  
        wynik \= opublikuj\_tresc(argumenty\["temat"\], argumenty\["platforma"\])  
        print(f"\[SYSTEM\] STATUS: {wynik}")

---

**Następne kroki:**

Uruchom ten kod lokalnie na swoim komputerze. Zobaczysz, jak system parsuje decyzję w formacie JSON i fizycznie uruchamia funkcję opublikuj\_tresc. To jest rdzeń Twojego przyszłego Agenta-Wykonawcy. Gdy to zadziała, podepniemy pod to prawdziwe zapytanie API do modelu językowego.

### ---

**Możliwości zgłębiania tematu kontynuując zrozumienie**

1. **Obsługa błędów wykonania (Error Handling):** Co system ma zrobić, gdy platforma docelowa odrzuci połączenie (np. kod błędu 500 z serwera)? Jak sformatować ten błąd i odesłać go z powrotem do modelu, aby spróbował ponownie.  
2. **Bezpośrednia integracja API xAI (Grok):** Przekształcenie powyższego symulowanego szkieletu w rzeczywiste połączenie HTTP z endpointami xAI, przesyłając autoryzację i odbierając realne decyzje modelu na żywo.

Jaki konkretny temat lub branżę wpisać w nasz pierwszy, testowy prompt uderzający do API, aby sprawdzić, co model wygeneruje i wyśle do naszego kodu publikującego?