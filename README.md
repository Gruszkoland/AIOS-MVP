# AIOS-MVP

MVP-first repository dla projektu **AIOS** — eksperymentalnego systemu operacyjnego opartego na agentach AI.

## Założenia MVP

- AI działa wyłącznie jako **asynchroniczny advisory plane**.
- Kernel pozostaje **deterministyczny** i nie czeka na LLM.
- Najpierw walidujemy PoC na Linuxie, dopiero potem inwestujemy w kernel.
- Startujemy od wariantu **headless / TUI-first**.

## Struktura workspace

```
AIOS-MVP/
├── Cargo.toml
├── README.md
├── LICENSE
├── kernel/
├── agents/
├── ipc/
├── poc/
├── docs/
├── scripts/
├── .github/
└── .devcontainer/
```

## Sprint 1

1. Setup monorepo i struktury katalogów
2. Konfiguracja narzędzi developerskich
3. RFC #1: `CognitiveAgent`
4. CI/CD GitHub Actions
5. Spike: model size + runtime feasibility
6. PoC: scheduler manager w user-space
7. Definicja kryteriów GO/NO-GO

## Zasady architektoniczne

- **AI advisory only** — żadnego LLM w hard real-time path
- **Shared memory / ring buffer** zamiast RPC na ścieżce krytycznej
- **MVP-first** — bez GUI jako wymagania startowego
- **Safety first** — capability model, review dla `unsafe`, benchmarki i fuzzing jako część DoD

## Definition of Done

Każdy ticket uznajemy za zamknięty gdy:
- przechodzi build i testy
- ma aktualną dokumentację
- ma review (dla `unsafe`: obowiązkowo 2-osobowe)
- nie wprowadza regresji benchmarków
- spełnia acceptance criteria

## Licencja

MPL-2.0
