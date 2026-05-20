# 🎯 PLAN ULEPSZEŃ — ADRION 369 v5.7+

**Dokument opracowany:** 2026-05-20  
**Zagrożenia:** BRAK REGRESJI  
**Filozofia:** Evoluuj, nie cofaj się.

---

## 📌 Strategie Wdrażania

### 1. NO-REGRESSION PRINCIPLE

```
Każda nowa funkcja = UPG tylko, ZERO deletions
Każdy deprecated endpoint = stary kod ← nowy alias
Każdy test = green lub skip, nigdy nie tłukł się
```

### 2. A/B TESTING (Feature Flags)

```python
# Trinity v6 (nowy) vs v5 (stary) — A/B test
if TRINITY_V6_ENABLED:
    score = trinity_v6.calculate_score(...)  # Nowy
else:
    score = trinity_v5.calculate_score(...)  # Stary (fallback)
```

### 3. BLUE/GREEN DEPLOYMENT

```bash
# Blue (v5.6 stable)
git branch blue && git checkout blue

# Green (v5.7 development)
git branch green && git checkout green
# ... wdrażaj nowe feature'y ...

# Swap (gdy testy OK)
git branch -m blue blue-old && git branch -m green blue
git branch green && git checkout green
```

---

## 🔧 FAZA 2A (Tygodnie 1-2)

### Priority 1: Dependency Management

```
Problem: 11 otwartych Dependabot PRs, openai SDK v2 BREAKING
Rozwiązanie:
1. Review każdy PR (git diff)
2. Dla non-breaking (pydantic, golang) → merge natychmiast
3. Dla openai SDK (BREAKING) → feature branch + thorough test
```

**Konkretne akcje:**

```bash
# Opcja A: Manual merge (safe)
git checkout dependabot/pip/openai-2-34-0
git pull origin dependabot/pip/openai-2-34-0
# Review changes...
git merge --no-ff -m "feat(deps): openai SDK v2.34.0 upgrade"

# Opcja B: Automated (GitHub Actions) — configure .github/workflows/dependabot.yml
```

**Commits to write:**

- `fix: Update openai SDK to v2.34.0 — async client adapter`
- `fix: Update python-docx to 1.2.0 — docx properties compatibility`
- `chore: Update pytest-asyncio to 1.3.0 — asyncio_mode='auto'`

### Priority 2: Docker Consolidation

```
Problem: 9 Dockerfiles, każdy na innej wersji Pythona
Cel: 1 multi-stage + parametryzacja

Struktura:
Dockerfile (nowy)
├── Stage 1: base (Python 3.13, common deps)
├── Stage 2: build (dev deps, compile)
├── Stage 3: prod (runtime, lean)
└── .env.docker (ARG PYTHON_VERSION=3.13, VORTEX_ENABLED=true)
```

**Skrypt migracji:**

```bash
for f in Dockerfile.* ; do
  cat "$f" | grep -E "^FROM|^RUN|^COPY" > "$f.rules"
done
# → wygeneruj unified ruleset
```

### Priority 3: Redis Integration (CVC Multi-instance)

```python
# core/cvc_redis.py
import redis

class CumulativeViolationCounterRedis:
    def __init__(self, redis_url="redis://localhost:6379/0", ttl=86400):
        self.redis = redis.from_url(redis_url)
        self.ttl = ttl
    
    def record_violation(self, session_id, violation_type):
        key = f"cvc:{session_id}:{violation_type}"
        self.redis.incr(key)
        self.redis.expire(key, self.ttl)
    
    def get_count(self, session_id, violation_type):
        key = f"cvc:{session_id}:{violation_type}"
        return int(self.redis.get(key) or 0)
    
    # load-balancer safe: routers A, B, C all read/write same Redis
```

**Wymagane zmiany:**

- `tests/test_cvc_redis.py` — integration test + failover scenario
- `docker-compose.yml` — add Redis service
- `docs/REDIS_INTEGRATION.md` — deployment guide

---

## 🔧 FAZA 2B (Tydzień 3)

### Priority 1: Genesis Record Failover

```
Problem: Brak dostępu do Genesis Record = silent failure
Rozwiązanie: 3-level failover

Level 1 (primary): PostgreSQL (full Genesis)
        ↓ (timeout 100ms)
Level 2 (replica): PostgreSQL replica / WAL log
        ↓ (timeout 100ms)
Level 3 (fallback): Local JSON file (last known state)
```

**Implementacja:**

```python
# core/genesis_failover.py
class GenesisRecord:
    def __init__(self, pg_primary, pg_replica, fallback_path):
        self.pg_primary = pg_primary
        self.pg_replica = pg_replica
        self.fallback_path = fallback_path  # /var/lib/genesis/latest.json
    
    def get_decision_audit(self, decision_id):
        try:
            return self.pg_primary.query(f"SELECT * FROM audit WHERE id={decision_id}")
        except TimeoutError:
            try:
                return self.pg_replica.query(...)
            except TimeoutError:
                return self._load_fallback(decision_id)
    
    def _load_fallback(self, decision_id):
        with open(self.fallback_path) as f:
            data = json.load(f)
        return data.get(decision_id, {"status": "UNKNOWN"})
```

### Priority 2: NLP Paraphrase Detector (G5)

```
Problem: "Czy audyt to dobry pomysł?" omija "Przeprowadź audyt"
Rozwiązanie: spaCy + paraphrase embeddings

Model: sentence-transformers/paraphrase-multilingual-mpnet-base-v2
```

**Implementacja:**

```python
# core/g5_paraphrase_detector.py
from sentence_transformers import SentenceTransformer

class G5ParaphraseGuard:
    def __init__(self, model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"):
        self.model = SentenceTransformer(model_name)
        self.audit_patterns = [
            "Perform an audit",
            "Run compliance check",
            "Execute system review",
            # ... 40+ PL/EN semantyczne warianty
        ]
        self.audit_embeddings = self.model.encode(self.audit_patterns)
    
    def is_audit_request(self, text):
        text_embedding = self.model.encode(text)
        # Cosine similarity
        similarities = util.pytorch_cos_sim(text_embedding, self.audit_embeddings)
        return max(similarities) > 0.7  # threshold
```

**Testy:**

- `"Czy warto audytować?"` → True
- `"Raport powinien być przejrzysty"` → False

---

## 🎯 FAZA 3 (1 miesiąc)

### Trinity + Hexagon Integration

```
Celem: Pełna konwergencja 3-6-9 matrycy

Cyklus Hexagonu (max 3 cykle):
  Cykl 1 → Trinity Score (material perspective)
  Cykl 2 → Guardians eval (9 laws)
  Cykl 3 → Hexagon sync + EBDI emotional state
```

### Per-IP Rate Limiting

```python
# core/rate_limit_per_ip.py
class PerIPRateLimiter:
    def __init__(self, redis_client, rate_per_min=60):
        self.redis = redis_client
        self.rate_per_min = rate_per_min
    
    def is_allowed(self, client_ip):
        key = f"ratelimit:{client_ip}"
        current = self.redis.incr(key)
        if current == 1:
            self.redis.expire(key, 60)
        return current <= self.rate_per_min
```

### Threat Model Document

```markdown
# ADRION 369 Threat Model

## Adversary Profiles
1. Insider — full code access
2. External attacker — API access only
3. Malicious agent — compromised AI agent in swarm

## Assets to Protect
1. Decision integrity (Trinity Score)
2. Guardian Laws enforcement
3. Audit trail (Genesis Record)
4. Inter-agent communication

## Attack Vectors (TOP 5)
1. Object mutation (Python internals) — MITIGATED v5.6
2. Serialization exploit — MITIGATED v5.6
3. Race conditions (multi-instance) — MITIGATED v5.7 (Redis)
4. Paraphrase evasion (G5) — MITIGATED v5.8 (NLP)
5. Replay attack (signatures) — ROADMAP v5.9

## Mitigation Status
| Vector | v5.0 | v5.6 | v5.7 | v5.8 | v5.9 |
|--------|------|------|------|------|------|
| Object mutation | ❌ | ✅ | ✅ | ✅ | ✅ |
| Serialization | ❌ | ✅ | ✅ | ✅ | ✅ |
| Race condition | ❌ | ❌ | ✅ | ✅ | ✅ |
| Paraphrase evasion | ❌ | ❌ | ❌ | ✅ | ✅ |
| Replay attack | ❌ | ❌ | ❌ | ❌ | ✅ |
```

---

## 🚀 FAZA 4 (Infrastruktura, 2+ miesiące)

### mTLS Inter-Agent (Produkcja)

```
Wymagane: Certificate Authority + agent certificates
Tool: certutil (Windows) or openssl (Linux)
```

### Go Vortex JWT + Rate Limit

```go
// cmd/vortex-server/auth.go
import "github.com/golang-jwt/jwt/v5"

type VortexAuth struct {
    jwtSecret string
    tokenTTL  = 5 * time.Minute
}

func (v *VortexAuth) IssueToken(agentID string) (string, error) {
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
        "agent_id": agentID,
        "exp":      time.Now().Add(v.tokenTTL).Unix(),
    })
    return token.SignedString([]byte(v.jwtSecret))
}
```

### Sygnatura 369 Replay Protection

```python
# Add nonce + timestamp
class Signature369:
    def __init__(self, decision_id, timestamp, nonce):
        self.decision_id = decision_id
        self.timestamp = timestamp
        self.nonce = nonce  # uuid4
        self.digital_root = self._compute_root()
        self.signature = self._sign()
    
    def validate(self, signature_obj):
        # Block if: timestamp > 5 min old OR nonce reused
        age = datetime.now() - signature_obj.timestamp
        if age > timedelta(minutes=5):
            return False
        if self.redis.exists(f"nonce:{signature_obj.nonce}"):
            return False
        self.redis.setex(f"nonce:{signature_obj.nonce}", 3600, "used")
        return signature_obj.signature == self.signature
```

---

## ✅ Checklist Implementacji Faza 2+

### Przed każdą release

- [ ] Wszystkie testy zielone (`pytest -v`)
- [ ] Coverage >= 80%
- [ ] Brak `TODO` / `FIXME` w core/ modules
- [ ] Changelog zaktualizowany
- [ ] Git tag v5.X.0 created
- [ ] GitHub Release stworzona (notes + docs link)

### Przed produkcją

- [ ] Load test (1000 req/sec przez min 1h)
- [ ] Security audit (external firm, jeśli >= v6.0)
- [ ] Backup strategy (Genesis Record + CVC)
- [ ] Runbook napisany (incidents, failover)

---

## 🎓 Nauka z Przeszłości

**Co działało:**

- Frozen dataclasses + MappingProxyType = silna obrana
- Penetration testing (64 scenariusze) = znalazło rzeczywiste luki
- Multi-warstwowy defense (Python + business logic + distributed)

**Co nie działało:**

- Pojedynczą patcha nie wystarczył (v5.1 vs v5.6 = 6 iteracji)
- Class attributes bez immutability = zawsze exploit-able
- Dokumentacja behind code (docu powinno być first)

**Przyszłość:**

- Security jest procesem, nie check-box'em
- Każde release bez testów penetracyjnych = regression risk
- Multi-instance bez Redis = silent failure

---

## 📞 Questions?

Wszystkie szczegóły w `docs/security/` folder.  
Kod w `push_staging/` — gotowy do merge.

**Rekomendacja:** Push v5.6 natychmiast, zaplanuj v5.7 (Redis) na tydzień 1-2.
