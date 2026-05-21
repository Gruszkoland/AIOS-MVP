# 📦 Struktura Repozytorium: adrion-369

**Źródło:** <https://github.com/Gruszkoland/adrion-369>  
**Branch:** main  
**Ostatnia aktualizacja:** 2024-2025

---

## 🌳 Tree View

```
adrion-369/
│
├── 📋 Pliki konfiguracyjne (Root Level)
│   ├── .env.example                    # Szablon zmiennych środowiskowych
│   ├── .gitignore                      # Pliki ignorowane przez Git
│   ├── .gitattributes                  # Atrybuty Git
│   ├── .pre-commit-config.yaml         # Konfiguracja pre-commit hooks
│   ├── .roo.json / .roo.ignore / .roorc # Konfiguracja Roo IDE
│   ├── .roomodes / .secrets.baseline   # Zaawansowane konfiguracje
│   ├── .coveragerc                     # Konfiguracja code coverage
│   ├── .dockerignore                   # Pliki ignorowane w Dockerze
│   ├── VERSION                         # Wersja projektu
│   ├── Makefile                        # Automatyzacja taskow
│   ├── pyproject.toml                  # Python project metadata
│   ├── pytest.ini                      # Konfiguracja pytest
│   ├── conftest.py                     # Konfiguracja testów
│   ├── go.mod / go.sum                 # Go project files
│   ├── wsgi.py                         # WSGI entry point
│   └── requirements-*.txt              # Zależności Pythona
│
├── 🐳 Dockerfiles (Multi-image)
│   ├── Dockerfile                      # Main application image
│   ├── Dockerfile.multi-stage          # Multi-stage build
│   ├── Dockerfile.genesis-mcp          # Genesis MCP service
│   ├── Dockerfile.guardian-mcp         # Guardian MCP service
│   ├── Dockerfile.healer-mcp           # Healer MCP service
│   ├── Dockerfile.oracle-mcp           # Oracle MCP service
│   ├── Dockerfile.vortex-mcp           # Vortex MCP service
│   ├── Dockerfile.mcp-router           # MCP Router
│   ├── Dockerfile.mcp-tier             # MCP Tier layer
│   ├── Dockerfile.healer               # Healer service
│   ├── Dockerfile.alert-handler        # Alert Handler
│   ├── Dockerfile.vortex               # Vortex service
│   └── Dockerfile.backup               # Backup service
│
├── 🔧 Docker Compose Configurations
│   ├── docker-compose.yml              # Main configuration
│   ├── docker-compose.prod.yml         # Production environment
│   ├── docker-compose.local.yml        # Local development
│   ├── docker-compose.cloud.yml        # Cloud deployment
│   ├── docker-compose.mcp-tier.yml     # MCP tier orchestration
│   ├── docker-compose.n8n-adrion.yml   # n8n integration
│   ├── docker-compose.k8s-integration.yml # Kubernetes integration
│   ├── docker-compose.oracle.yml       # Oracle database
│   ├── docker-compose.lmstudio.yml     # LM Studio integration
│   └── docker-compose-orchestration.yml # Advanced orchestration
│
├── 📖 Dokumentacja (Root Level)
│   ├── README.md                       # Project overview
│   ├── CHANGELOG.md                    # Version history
│   ├── CLAUDE.md                       # Claude AI instructions (34KB)
│   ├── DOCKER.md                       # Docker setup guide
│   ├── DOCKER_BUILD_PLAN.md            # Docker build strategy
│   ├── INTEGRACJA_STRATEGIA.md         # Integration strategy
│   ├── MANIFEST.md                     # Project manifest
│   ├── PHASE5_CONTINUATION_PLAN.md     # Phase 5 continuation
│   ├── PROJECT_COMPLETION_SUMMARY.md   # Project summary
│   ├── TEST_REPORT.md                  # Test results
│   ├── SECURITY.md                     # Security guidelines
│   └── UPSTREAM_REPOS_REFERENCE.md     # Upstream repos
│
├── 🔍 Configuration Directories
│   ├── .claude/                        # Claude configuration
│   ├── .github/                        # GitHub workflows & CI/CD
│   ├── .githooks/                      # Git hooks
│   ├── .vscode/                        # VS Code settings
│   ├── .zap/                           # OWASP ZAP config
│   └── .roo/                           # Roo IDE config
│
├── 🏗️ Core Architecture
│   ├── adrion-swarm/                   # Swarm orchestration
│   ├── core/                           # Core application logic
│   ├── internal/                       # Internal packages
│   ├── cmd/                            # Command line tools
│   ├── config/                         # Configuration files
│   └── arbitrage/                      # Arbitrage logic
│
├── 🎯 Service Modules
│   ├── mcp_servers/                    # MCP server implementations
│   │   ├── genesis-mcp/
│   │   ├── guardian-mcp/
│   │   ├── healer-mcp/
│   │   ├── oracle-mcp/
│   │   ├── vortex-mcp/
│   │   └── mcp-router/
│   ├── arbitrage/                      # Arbitrage processing
│   ├── dashboard/                      # Dashboard frontend
│   ├── frontend/                       # Web frontend
│   └── ecosystem/                      # Ecosystem components
│
├── 🛠️ Infrastructure & DevOps
│   ├── kubernetes/                     # K8s manifests
│   ├── terraform/                      # IaC configurations
│   ├── scripts/                        # Automation scripts
│   ├── monitoring/                     # Monitoring setup
│   ├── prometheus/                     # Prometheus config
│   ├── logging/                        # Logging configuration
│   └── db/                             # Database setup
│
├── 🔄 Data & Workflow
│   ├── data/                           # Data files
│   ├── n8n-workflows/                  # n8n workflow definitions
│   ├── tasks/                          # Task definitions
│   ├── healing_proposals/              # Healing proposals
│   └── arbitrage_server.py             # Arbitrage server entry
│
├── 📝 Testing & Validation
│   ├── tests/                          # Test suites
│   ├── test_phase3_middleware.py       # Middleware tests
│   └── validation-report.json          # Validation results
│
├── 📚 Documentation & Records
│   ├── docs/                           # Extended documentation
│   ├── Genesis Record/                 # Genesis records
│   ├── micro-saas/                     # Micro-SaaS components
│   ├── tools/                          # Development tools
│   └── uap/                            # UAP components
│
└── 📊 Logs & Reports
    └── logs/                           # Application logs

```

---

## 📊 Statystyki Repozytorium

| Aspekt | Wartość |
|--------|---------|
| **Główne katalogi** | 30+ |
| **Dockerfiles** | 12 |
| **Docker Compose configs** | 9 |
| **Pliki konfiguracyjne** | 15+ |
| **Dokumentacja** | 12 plików MD |
| **Języki** | Python, Go, YAML, JSON |
| **Orchestration** | Docker Compose + Kubernetes |

---

## 🎯 Kluczowe Komponenty

### 1. **MCP Servers Tier**

Modularny system serwerów MCP (Model Context Protocol):

- `genesis-mcp` - Genesis service
- `guardian-mcp` - Guardian/protection service
- `healer-mcp` - Healing/recovery service
- `oracle-mcp` - Oracle/prediction service
- `vortex-mcp` - Vortex/data processing service
- `mcp-router` - Routing layer

### 2. **Orchestration**

- Docker Compose dla local/dev
- Kubernetes manifests dla production
- n8n workflow integration
- Database layer (Oracle, PostgreSQL)

### 3. **Pipeline**

- Arbitrage processing engine
- Task automation (n8n)
- Data healing & proposals
- Monitoring & alerts

### 4. **Frontend**

- Dashboard (`/dashboard`)
- Web application (`/frontend`)
- Micro-SaaS components

---

## 🔗 Główne Definicje

### Dokumenty Projektowe

```
CLAUDE.md                      → Instrukcje AI/Claude (34KB)
INTEGRACJA_STRATEGIA.md        → Strategia integracji (23KB)
MANIFEST.md                    → Manifest projektu (21KB)
PHASE5_CONTINUATION_PLAN.md    → Plan kontynuacji fazy 5 (17KB)
PROJECT_COMPLETION_SUMMARY.md  → Podsumowanie projektu (17KB)
```

### Pliki Skonfiguracyjne

```
.env.example                   → 6.8KB - Zmienne środowiska
.roo.json                      → 10KB - Konfiguracja Roo
.roorc                         → 10KB - Roo runtime config
.secrets.baseline              → 95KB - Security baseline
```

---

## 🚀 Quick Start Paths

```
# Development
docker-compose -f docker-compose.local.yml up

# Production
docker-compose -f docker-compose.prod.yml up

# MCP Tier
docker-compose -f docker-compose.mcp-tier.yml up

# n8n Integration
docker-compose -f docker-compose.n8n-adrion.yml up

# Kubernetes
kubectl apply -f kubernetes/

# Tests
pytest
make test
```

---

## 📌 Ważne Pliki

| Plik | Rozmiar | Opis |
|------|---------|------|
| `.secrets.baseline` | 95KB | Bezpieczeństwo, sekrety |
| `.roomodes` | 39KB | Zaawansowane konfiguracje |
| `CLAUDE.md` | 34KB | Instrukcje AI |
| `docker-compose-orchestration.yml` | 23KB | Orkestracja |
| `INTEGRACJA_STRATEGIA.md` | 23KB | Strategia |
| `MANIFEST.md` | 21KB | Manifest projektu |

---

## 🔐 Security & DevOps

```
├── Security
│   ├── .secrets.baseline      # Baseline dla detectsecrets
│   ├── SECURITY.md            # Security guidelines
│   └── .pre-commit-config.yaml # Pre-commit hooks
│
├── Monitoring
│   ├── prometheus/            # Prometheus config
│   ├── monitoring/            # Monitoring setup
│   └── logs/                  # Log storage
│
└── Infrastructure
    ├── kubernetes/            # K8s manifests
    ├── terraform/             # IaC (jeśli istnieje)
    └── scripts/               # Automation scripts
```

---

## 📦 Zależności

### Python

```
pyproject.toml          # Primary dependencies
requirements-mcp.txt    # MCP specific
requirements-arbitrage.txt # Arbitrage specific
```

### Go

```
go.mod                  # Go module definition
go.sum                  # Go dependencies lock
```

### Docker

```
Multiple Dockerfiles   # 12 specialized images
docker-compose files   # 9 configurations
```

---

## 🎯 Projekt: ADRION-369

**Ekosystem:** Zaawansowany system orchestracji oparty na architekturze 3-6-9  
**Komponenty:** MCP Servers + n8n + Arbitrage + Healing + Monitoring  
**Deployment:** Docker Compose + Kubernetes  
**Status:** Active Development (Phase 5+)

---

*Wygenerowano: 13.05.2026*
