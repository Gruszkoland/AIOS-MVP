# 05 — Security & Compliance: ADRION 369

**Dla kogo:** CISO, compliance oficer, inwestorzy z wymogami regulacyjnymi
**Data:** 2026-04-05 | **Wersja:** v1.0.0

---

## Podsumowanie bezpieczeństwa

```
╔══════════════════════════════════════════════════════╗
║  ADRION 369 Security Posture — Snapshot 2026-04-05   ║
╠══════════════════════════════════════════════════════╣
║  Threat Model:           ✅ Udokumentowany           ║
║  Security CI/CD:         ✅ bandit + safety (hard)   ║
║  Secrets management:     ✅ .env + manage-secrets.ps1║
║  Transport security:     ✅ HMAC webhooks (Stripe)   ║
║  Rate limiting:          ✅ Per-endpoint (9 limiters)║
║  Circuit breakers:       ✅ 4 breakers (llm/stripe..)║
║  Immutable audit log:    ✅ Genesis Record design     ║
║  Cloud data exposure:    ✅ ZERO (local-first)        ║
║  RODO compliance:        ✅ By design (local LLM)     ║
║  Penetration testing:    ⚠️ Planowany Q2 2026         ║
╚══════════════════════════════════════════════════════╝
```

---

## 1. Warstwa etyczna — 9 Guardian Laws

Unikalny w branży system etycznej walidacji każdej decyzji AI:

| # | Prawo | Co chroni | Implementacja |
|---|-------|-----------|---------------|
| 1 | Unity | Spójność systemu | Cel score check |
| 2 | Truth | Zakaz dezinformacji | Fact validation |
| 3 | Rhythm | Przewidywalność | Rate check |
| 4 | Causality | Przejrzystość przyczyn | Chain logging |
| 5 | Transparency | Uzasadnienie każdej decyzji | Required justification |
| 6 | **Nonmaleficence** | **Zakaz wyrządzania szkody** | **Najwyższy priorytet** |
| 7 | Autonomy | Szanowanie decyzji użytkownika | Consent check |
| 8 | Justice | Brak bias, sprawiedliwy dostęp | Fairness audit |
| 9 | Sustainability | Długoterminowy wpływ | Resource check |

**Mechanizm:** ≥2 naruszeń = MANDATORY DENY. Wynik Trinity ignorowany.
**Roadmap:** Ważone prawa — Nonmaleficence = instant DENY (ADR-002b)

---

## 2. Bezpieczeństwo aplikacji

### Zarządzanie sekretami

```bash
# Żadnych hardcoded secrets — egzekwowane przez CI
.env                    # lokalne sekrety (gitignored)
.env.example            # bezpieczny template dla repozytorium
manage-secrets.ps1      # rotacja i walidacja kluczy
.github/workflows/security-ci.yml  # skan sekretów w każdym PR
```

**Narzędzia CI:**
- `bandit` — skanowanie podatności w Python (blokuje PR)
- `safety` — skan zależności pod kątem CVE (blokuje PR)
- `truffleHog` / `gitleaks` — skanowanie git history (pre-commit)

### Rate limiting (ochrona przed DoS)

```python
# SlidingWindowRateLimiter — per endpoint, per IP
Rate limits:
  /api/quantum/*    30/min    — decision engine
  /api/scout        10/min    — expensive Apify calls
  /api/cycle        5/min     — full pipeline
  /api/oracle/*     20/min    — ML inference
  /api/mass-gen     3/min     — bulk operations
```

### Circuit breakers (ochrona przed kaskadowymi awariami)

```python
# arbitrage/circuit_breaker.py
llm_breaker    — Ollama (threshold: 5 errors/60s)
stripe_breaker — Płatności (threshold: 3 errors/60s)
apify_breaker  — Lead discovery (threshold: 5 errors/120s)
xrp_breaker    — Crypto feed (threshold: 10 errors/60s)
```

### Weryfikacja płatności (Stripe)

```python
# arbitrage/payments.py
def verify_webhook_signature(payload, sig_header, secret):
    # HMAC-SHA256 — identyczny z metodologią Stripe
    signed_payload = f"{timestamp}.{payload}"
    expected = hmac.new(secret.encode(), signed_payload.encode(), sha256).hexdigest()
    return hmac.compare_digest(expected, received_sig)
```

---

## 3. Prywatność i RODO

### Local-first architecture

```
DANE UŻYTKOWNIKA
      │
      ▼
  Ollama (localhost:11434)
      │
      ▼ (nigdy nie opuszcza systemu)
  Genesis Record (local PostgreSQL)
      │
      ▼
  Prometheus metrics (localhost, no PII)
```

**Gwarancje prywatności:**
- ✅ **Zero PII** wysyłanych do cloud LLM
- ✅ Genesis Record przechowywany lokalnie
- ✅ Logi nie zawierają wrażliwych danych (zweryfikowane w code review)
- ✅ Stripe webhooks: minimum danych (tylko event type + amount)

### Compliance status

| Standard | Status | Uwagi |
|----------|--------|-------|
| RODO (EU) | ✅ By design | Local-first = brak transferu do USA |
| SOC2 | 🔜 Planowany | Wymaga audit Q3 2026 |
| ISO 27001 | 🔜 Planowany | Po SOC2 |
| PCI DSS | ⚠️ Delegowany | Stripe obsługuje PCI compliance |

---

## 4. Infrostuktura bezpieczeństwa

### Network security

```yaml
# docker-compose — network isolation
networks:
  adrion-internal:   # tylko internal services
  adrion-external:   # tylko publiczne endpointy

# CORS
CORS_ALLOWED_ORIGIN: $CORS_ALLOWED_ORIGIN  # nie "*"
```

### Database security

```sql
-- PostgreSQL app user — minimal permissions
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO adrion_app;
-- Celowo brak: UPDATE, DELETE, TRUNCATE
-- Immutable audit log enforcement
```

### Pre-commit security hooks

```bash
# .githooks/pre-commit
- ruff check (linting)
- bandit (security scan)
- gitleaks (secret detection)
- coverage check (min 65%)
```

---

## 5. Incydenty i odpowiedź

### Procedury Disaster Recovery

- Backup PostgreSQL: daily (`scripts/backup/backup-postgres.sh`)
- Restore procedure: udokumentowana w `docs/DISASTER_RECOVERY.md`
- RTO (Recovery Time Objective): <30 min
- RPO (Recovery Point Objective): <24h

### Incident Response Plan

| Zdarzenie | Odpowiedź | Czas |
|-----------|-----------|------|
| Agent crash | Watchdog auto-restart | <5s |
| DB connection exhaustion | Pool monitoring + alert | real-time |
| Circuit breaker open | Log + fallback mode | instant |
| Security CVE w dependency | safety CI blokuje PR | per PR |

---

*ADRION 369 v1.0.0 — Genesis Record 2026-04-05*
*Pełny threat model: [docs/THREAT-MODEL.md](../../docs/THREAT-MODEL.md)*
