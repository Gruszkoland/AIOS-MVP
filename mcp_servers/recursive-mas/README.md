# RecursiveMAS — MCP Server

> Silnik wnioskowania Multi-Agent System oparty o rekurencję przestrzeni latentnej.

## Źródło

- Repo: [RecursiveMAS/RecursiveMAS](https://github.com/RecursiveMAS/RecursiveMAS)
- Paper: [arXiv 2604.25917](https://arxiv.org/abs/2604.25917)
- Modele: [HuggingFace RecursiveMAS](https://huggingface.co/RecursiveMAS/collections)

## Architektura

RecursiveMAS łączy heterogeniczne agenty LLM przez moduły **RecursiveLink**, które pozwalają na iteracyjną wymianę i ewolucję stanów latentnych między agentami.

### Style kolaboracji

| Styl | Agenty | Zastosowanie w adrion-369 |
|------|--------|---------------------------|
| `sequential_light` | Planner + Critic + Solver (1-2B) | Szybkie pipeline zadań |
| `sequential_scaled` | Planner + Critic + Solver (3-9B) | Złożone rozumowanie |
| `mixture` | Domain agents + Summarizer | Wielodomenowe analizy |
| `distillation` | Expert + Learner | Optymalizacja inference |
| `deliberation` | Reflector + ToolCaller | Integracja z narzędziami |

## Integracja z adrion-369

Ten katalog zawiera pliki konfiguracyjne potrzebne do uruchomienia RecursiveMAS jako kontenera MCP w ekosystemie adrion-369.

### Wymagania sprzętowe (Hetzner)

- **GPU**: NVIDIA (CUDA 12+) — wymagane dla modeli ≥3B
- **RAM**: min. 16GB dla `sequential_light`, 32GB+ dla `sequential_scaled`
- **Storage**: 20-50GB na checkpointy HF

## Setup

```bash
# Pobierz checkpointy (przykład sequential_light)
huggingface-cli download RecursiveMAS/Sequential-Light-Planner-Qwen3-1.7B
huggingface-cli download RecursiveMAS/Sequential-Light-Critic-Llama3.2-1B
huggingface-cli download RecursiveMAS/Sequential-Light-Solver-Qwen2.5-Math-1.5B
huggingface-cli download RecursiveMAS/Sequential-Light-Outerlinks

# Uruchom serwis
docker compose -f docker-compose.mcp-tier.yml up recursive-mas
```

## Zmienne środowiskowe

| Zmienna | Opis | Wymagana |
|---------|------|----------|
| `HF_TOKEN` | Token HuggingFace (prywatne modele) | Opcjonalna |
| `TAVILY_API_KEY` | Klucz Tavily (styl Deliberation) | Dla `deliberation` |
| `RECURSIVE_MAS_STYLE` | Styl kolaboracji | Tak |
| `RECURSIVE_MAS_DEVICE` | `cuda` lub `cpu` | Tak |
| `RECURSIVE_MAS_PORT` | Port MCP (domyślnie 8095) | Opcjonalna |
