# LESSONS LEARNED — 162 Demencje w Schemacie 369

> Plik wymagany przez `Master Agent Behavior.instructions.md` §3 (Pętla Lekcji).
> Agent czyta ten plik na początku każdej sesji i stosuje się do zapisanych lekcji.
> Nowe lekcje są dodawane automatycznie przez agenta lub ręcznie.

---

## Format wpisu

```markdown
### Lekcja [N]: [Krótki tytuł]
- **Kontekst:** [Kiedy to się zdarza]
- **Reguła:** [Co zawsze robić / czego unikać]
- **Przykład:** [Opcjonalny fragment kodu lub scenariusz]
- **Discovered:** [YYYY-MM-DD]
```

---

## Lekcje

### Lekcja 1: Virtualenv zawsze w `.venv`

- **Kontekst:** Projekt używa Pythona z venv w katalogu głównym projektu.
- **Reguła:** Zawsze aktywuj środowisko przez `c:\Users\adiha\.1_Projekty\162 demencje w schemacie 369\.venv\Scripts\Activate.ps1` przed uruchomieniem skryptów.
- **Przykład:** `(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& ".venv\Scripts\Activate.ps1")`
- **Discovered:** 2026-05-06

### Lekcja 2: Projekt jest monorepo multi-stack

- **Kontekst:** Workspace zawiera Go (`go.mod`), Python (`pyproject.toml`), Docker, Kubernetes i MCP servers.
- **Reguła:** Przed edycją pliku sprawdź jego stack — Python w `arbitrage/`, Go w `cmd/` i `internal/`, MCP w `mcp_servers/`.
- **Discovered:** 2026-05-06

### Lekcja 3: Docker Compose — mapa profili projektowych

- **Kontekst:** W projekcie jest ~10 różnych plików `docker-compose.*.yml`. Uruchomienie złego profilu może zdeployować na produkcję.
- **Reguła:** Zawsze mapuj kontekst zadania na właściwy plik według tabeli poniżej. Nigdy nie uruchamiaj `docker compose up` bez jawnego `-f`.
- **Mapa profili:**

  | Plik | Środowisko | Kiedy używać |
  |---|---|---|
  | `docker-compose.local.yml` | Dev (lokalnie) | Codzienny development, debugowanie |
  | `docker-compose.yml` | Dev (domyślny) | Fallback, testy integracyjne |
  | `docker-compose.prod.yml` | Produkcja | ⚠️ SAFETY GATE — wymaga potwierdzenia |
  | `docker-compose.cloud.yml` | Cloud (GCP/Azure) | Deploy na chmurę |
  | `docker-compose.k8s-integration.yml` | K8s bridge | Testowanie z Kubernetes |
  | `docker-compose.mcp-tier.yml` | MCP servers | Uruchamianie warstwy MCP |
  | `docker-compose.lmstudio.yml` | LM Studio | Lokalne modele LLM |
  | `docker-compose.oracle.yml` | Oracle DB | Bazy danych Oracle |
  | `docker-compose-orchestration.yml` | Orchestration | Pełny stack orkiestracji |

- **Przykład:** `docker compose -f docker-compose.local.yml up -d` → dev bez ryzyka
- **Discovered:** 2026-05-07

### Lekcja 4: Docker Compose — kolejność startowania serwisów

- **Kontekst:** Projekt ma serwisy zależne od siebie (bazy danych, MCP, monitoring).
- **Reguła:** Przy starcie zawsze sprawdź `depends_on` i healthchecks. Nie używaj `--no-deps` w produkcji. Kolejność: DB → MCP servers → aplikacja → monitoring.
- **Przykład:** Jeśli serwis `arbitrage` failuje, najpierw sprawdź czy postgres/redis są healthy: `docker compose ps`
- **Discovered:** 2026-05-07

### Lekcja 5: Docker — odbudowa obrazów po zmianie kodu

- **Kontekst:** Po zmianie plików Python/Go docker-compose nie odbudowuje obrazów automatycznie.
- **Reguła:** Po zmianie kodu zawsze uruchamiaj `docker compose -f <plik> up -d --build`. Samo `up -d` uruchomi stary obraz.
- **Discovered:** 2026-05-07

---

*Kolejne lekcje dodawane automatycznie przez agenta w trakcie pracy.*
