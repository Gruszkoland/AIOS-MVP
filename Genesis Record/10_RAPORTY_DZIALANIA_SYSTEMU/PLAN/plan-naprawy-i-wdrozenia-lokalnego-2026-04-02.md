# Plan naprawy i wdrozenia lokalnego

Data: 2026-04-02
Status: in-progress

## Cel
Przywrocic pelna lokalna gotowosc uruchomieniowa systemu (Python, Go, Next.js) oraz zamknac blokery P0/P1 z audytu.

## Kroki wykonawcze

1. Przywrocenie kompatybilnosci kontraktow Oracle/Quantum
- Cel kroku: usunac ImportError i przywrocic zgodnosc API z testami oraz warstwa `api.py`.
- Kryterium ukonczenia: `tests/test_oracle.py` i `tests/test_quantum.py` przechodza.
- Zaleznosci: dostep do stabilnej implementacji z `legacy`.
- Priorytet: P0
- Status: done

2. Naprawa skladni backendu API
- Cel kroku: usunac bledny naglowek/docstring powodujacy SyntaxError.
- Kryterium ukonczenia: `python -m compileall arbitrage` bez bledow.
- Zaleznosci: brak.
- Priorytet: P0
- Status: done

3. Naprawa builda Next.js (param typing)
- Cel kroku: dostosowac `PageProps` i `params` do kontraktu Next 15.
- Kryterium ukonczenia: `npm run build` w `micro-saas` przechodzi.
- Zaleznosci: sprawna instalacja npm.
- Priorytet: P1
- Status: done

4. Ustabilizowanie modulu Go
- Cel kroku: wygenerowac `go.sum` i potwierdzic kompilacje/testy.
- Kryterium ukonczenia: `go mod tidy` + `go test ./...` bez fail.
- Zaleznosci: dostep do internetu dla dependency resolution.
- Priorytet: P0
- Status: done

5. Walidacja calosci lokalnie
- Cel kroku: potwierdzic, ze naprawy nie wprowadzily regresji.
- Kryterium ukonczenia: `pytest -q` oraz build Next i testy Go przechodza.
- Zaleznosci: kroki 1-4.
- Priorytet: P0
- Status: done

6. Domkniecie dokumentacji i przekazanie wdrozenia
- Cel kroku: zapisac przebieg i wynik w PLAN/PROGRESS/REPORTS.
- Kryterium ukonczenia: komplet 3 dokumentow i rekomendacje dalszych krokow.
- Zaleznosci: kroki 1-5.
- Priorytet: P1
- Status: in-progress
