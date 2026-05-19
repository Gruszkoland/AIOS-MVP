# ADRION 369 — Docker Compose Reference

Każdy plik `docker-compose*.yml` odpowiada innemu trybowi uruchomienia. Poniżej mapa — wybierz jeden odpowiedni do kontekstu.

---

## Mapa plików

| Plik | Cel | Kiedy używać |
|------|-----|--------------|
| `docker-compose.yml` | **Dev baseline** — Postgres + backend Flask + pgAdmin | Lokalne środowisko, pierwsza instalacja |
| `docker-compose.local.yml` | **Dev rozszerzony** — + Prometheus + Grafana + Redis | Lokalne testowanie monitoringu |
| `docker-compose.prod.yml` | **Produkcja (cloud minimal)** — API + dashboard + Loki + Grafana | Serwer VPS bez Kubernetes |
| `docker-compose.cloud.yml` | **Produkcja (cloud pełna)** — jak prod + alert-handler + promtail | Pełny cloud deployment |
| `docker-compose.oracle.yml` | **Oracle stack** — API + UAP + Prometheus + Grafana + Loki | Wdrożenie z Vortex Oracle |
| `docker-compose.mcp-tier.yml` | **MCP mikroserwisy** — 6 portów 9000–9005 | Uruchomienie warstwy Guardian/MCP |
| `docker-compose.lmstudio.yml` | **LM Studio** — lokalne LLM zamiast OpenAI | Testowanie z lokalnym modelem |
| `docker-compose.k8s-integration.yml` | **K8s bridge** — usługi nieobj ęte K8s (Postgres, Prometheus) | Kubernetes + local hybrid |
| `docker-compose-orchestration.yml` | **Full orchestration** — Postgres + Loki + Promtail + Ollama + alert-handler | Pełny stack z Ollama |

---

## Szybki start

### Dev (minimum)
```bash
docker compose up -d
```

### Dev z monitoringiem
```bash
docker compose -f docker-compose.local.yml up -d
```

### Produkcja
```bash
docker compose -f docker-compose.prod.yml up -d
```

### MCP tier (Guardian, Oracle, Healer, Vortex, Router, Genesis)
```bash
docker compose -f docker-compose.mcp-tier.yml up -d
```
Porty MCP: Router=9000, Vortex=9001, Guardian=9002, Oracle=9003, Genesis=9004, Healer=9005

### Z lokalnym LLM (LM Studio)
```bash
docker compose -f docker-compose.lmstudio.yml up -d
```

---

## Zmienne środowiskowe

Skopiuj `.env.example` → `.env` przed pierwszym uruchomieniem:
```bash
cp .env.example .env
```

Wymagane (bez nich `sys.exit(1)` przy starcie):

| Zmienna | Opis | Środowisko |
|---------|------|-----------|
| `UAP_API_KEY` | Klucz API warstwy UAP | prod/staging |
| `JWT_SECRET` | Sekret JWT (min. 32 znaki) | prod/staging |
| `ENVIRONMENT` | `development` \| `production` | wszystkie |

Opcjonalne:

| Zmienna | Domyślna | Opis |
|---------|---------|------|
| `OPENAI_API_KEY` | — | OpenAI / OpenRouter |
| `POSTGRES_URL` | `localhost:5432` | Baza danych |
| `REDIS_URL` | `redis://localhost:6379` | Cache/CVC |
| `CORS_ALLOWED_ORIGIN` | `http://localhost:8003` | Frontend origin |

---

## Porty serwisów

| Serwis | Port | Compose |
|--------|------|---------|
| Arbitrage API (Flask) | 8001 | wszystkie |
| UAP Backend | 8002 | oracle, cloud |
| Frontend / Dashboard | 8003 | dev, prod |
| Vortex Engine (Go) | 1740 | orchestration |
| Prometheus | 9090 | local, k8s, oracle |
| Grafana | 3000 | local, cloud, oracle |
| Loki | 3100 | cloud, oracle |
| pgAdmin | 5050 | dev |
| MCP Router | 9000 | mcp-tier |
| MCP Vortex | 9001 | mcp-tier |
| MCP Guardian | 9002 | mcp-tier |
| MCP Oracle | 9003 | mcp-tier |
| MCP Genesis | 9004 | mcp-tier |
| MCP Healer | 9005 | mcp-tier |

---

## Nowe obrazy MCP

Stare Dockerfiles (`Dockerfile.genesis-mcp`, `Dockerfile.guardian-mcp`, etc.) są zdeprecjonowane.
Użyj `Dockerfile.mcp-tier` z `--build-arg`:

```bash
docker build -f Dockerfile.mcp-tier \
  --build-arg APP=mcp_guardian_app.py \
  --build-arg PORT=9002 \
  -t adrion-guardian-mcp .
```
