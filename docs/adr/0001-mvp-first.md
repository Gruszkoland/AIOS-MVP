# ADR-0001: MVP-first zamiast full-scope od startu

## Status
Accepted

## Kontekst
Pełny scope AIOS (kernel + AI runtime + 9 agentów + FS + sieć + security) oceniony przez audyt na ~40 miesięcy dla 10-13 inżynierów.

## Decyzja
Projekt zaczyna od PoC user-space i minimalnego repo, nie od pełnej implementacji.

## Uzasadnienie
- redukcja ryzyka
- szybszy feedback (walidacja assumptions schedulera/AI na Linuksie)
- uniknięcie AI w ścieżce krytycznej (P0-05 z audytu)
- niższy próg wejścia dla nowych kontrybutorów

## Konsekwencje
- Faza -1: PoC + sprint 1 na Linuksie
- Kernel development zaczyna się dopiero po GO z PoC
- GUI/desktop pominięte w MVP scope
