<!-- ADNOTACJA DLA GŁÓWNEJ STRONY INFORMACYJNEJ -->
<!-- Dodaj poniższy fragment do głównej strony docs/ lub README systemowego -->

## 🔗 Rozszerzenia systemu

### RecursiveMAS — Multi-Agent LLM Inference

> **[📄 Pełna dokumentacja →](./recursive-mas.html)**

System adrion-369 został rozszerzony o silnik **RecursiveMAS** — framework multi-agentowy oparty o rekurencję przestrzeni latentnej ([arXiv 2604.25917](https://arxiv.org/abs/2604.25917)).

RecursiveMAS działa jako niezależny **serwis MCP** (port `8095`) i udostępnia:
- `POST /tools/recursive_mas_infer` — uruchomienie wnioskowania wieloagentowego
- `GET /tools/recursive_mas_styles` — lista dostępnych stylów kolaboracji
- `GET /tools/recursive_mas_status` — stan załadowanych modeli

**Style kolaboracji:** `sequential_light` · `sequential_scaled` · `mixture` · `distillation` · `deliberation`

**Wymagania:** Docker + NVIDIA GPU (CUDA 12+) dla modeli ≥3B; CPU dla `sequential_light`.

```bash
# Uruchomienie
docker compose -f docker-compose.mcp-tier.yml up recursive-mas

# Weryfikacja
curl http://localhost:8095/health
```

> ⚠️ **Uwaga:** Styl `deliberation` wymaga dodatkowo `TAVILY_API_KEY` w `.env`.
