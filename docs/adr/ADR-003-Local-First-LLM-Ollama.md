# ADR-003: Local-first LLM — Ollama zamiast cloud API

**Status:** ZAAKCEPTOWANY
**Data:** 2025-Q4
**Autor:** ADRION Core Team

---

## Kontekst

ADRION 369 przetwarza wrażliwe dane:

- Dane finansowe leads (kwoty kontraktów, dane firm)
- Dane arbitrażu (strategie, marże, dostawcy)
- Dane użytkowników (freelancer profiles)

Opcje backendu LLM:
| Opcja | Jakość | Prywatność | Koszt | Offline |
|-------|--------|------------|-------|---------|
| OpenAI GPT-4 | Najlepsza | ❌ dane w US | $$$  | ❌ |
| Anthropic Claude | Bardzo dobra | ❌ dane w US | $$$ | ❌ |
| Google Gemini | Dobra | ❌ dane w EU | $$ | ❌ |
| **Ollama (local)** | Dobra | ✅ localhost | $0 | ✅ |
| LM Studio | Dobra | ✅ localhost | $0 | ✅ |

## Decyzja

**`LLM_BACKEND=ollama`** jako domyślny i jedyny tryb produkcyjny.
Model: DeepSeek-Coder-V2 na localhost:11434

```python
# config.py
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
```

Cloud LLM dopuszczony TYLKO jako opt-in w środowisku deweloperskim,
po explicite ustawieniu `LLM_BACKEND=openai` w `.env`.

## Konsekwencje

### Plusy

- Zero PII wysłanych poza localhost — pełna RODO compliance
- Brak kosztów per-token w produkcji
- Działa całkowicie offline (`.env.offline`)
- Guardian Law #7 (Privacy) automatycznie spełniony
- Brak vendor lock-in

### Minusy / Ryzyka

- Gorsze rozumowanie niż frontier models (GPT-4, Claude Opus)
- Cold start 10-60s przy reload modelu po idle
- Wymaga GPU ≥8GB VRAM dla sensownej prędkości
- Ograniczony context window (8k vs 200k w Claude)

## Mitygacja ryzyk

- Ollama preload w startup script (eliminacja cold start)
- GPU monitoring via `pynvml` (VRAM threshold alerting)
- Fallback: `LLM_BACKEND=mock` dla CI/CD bez GPU

## Powiązane ADR

- ADR-001: Trinity-EBDI (Ollama jest motorem Intellectual perspective)
