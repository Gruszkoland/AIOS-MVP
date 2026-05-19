---
title: "Quick Start dla Zewnetrznych Integratorow"
version: "1.0"
created: "2026-05-19"
author: "ADRION 369 Core Team"
audience: "B2B External Integrators"
---

# Quick Start — Integracja z ADRION 369

> Przewodnik dla deweloperow chcacych zintegrowac zewnetrzny system z ADRION 369.
> Czas do pierwszego dzialajacego call: **~15 minut**.

---

## Wymagania wstepne

- Python 3.11+ lub Go 1.22+
- Klucz API (uzyskaj od administratora ADRION 369)
- Dostep sieciowy do endpointu API

---

## Krok 1: Konfiguracja srodowiska

```bash
# Sklonuj repo (opcjonalnie, jesli chcesz uruchomic lokalnie)
git clone https://github.com/Gruszkoland/adrion-369.git
cd adrion-369

# Zainstaluj zaleznosci Python
pip install -r requirements.txt

# Skopiuj .env i uzupelnij klucze
cp config/.env.example .env
```

Uzupelnij `.env`:
```env
ADRION_API_KEY=twoj_klucz_api
ADRION_BASE_URL=https://api.adrion369.example.com
ADRION_AGENT_ID=AGT-EXT-001
```

---

## Krok 2: Autentykacja

ADRION 369 uzywa JWT z SHA-256 session hash.

```python
import httpx
import os

API_KEY = os.getenv("ADRION_API_KEY")
BASE_URL = os.getenv("ADRION_BASE_URL")

# Pobierz token sesji
response = httpx.post(
    f"{BASE_URL}/auth/token",
    json={"api_key": API_KEY}
)

token = response.json()["access_token"]
print(f"Token: {token[:20]}...")
```

---

## Krok 3: Pierwszy Call — Zapytanie do agenta

```python
import httpx

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Wyslij zapytanie do agenta Orchestrator (AGT-003)
response = httpx.post(
    f"{BASE_URL}/agents/AGT-003/query",
    headers=headers,
    json={
        "query": "Jaki jest obecny stan systemu?",
        "perspective": "Material",      # Material | Intellectual | Essential
        "mode": "Inventory",             # tryb Hexagon
        "criticality": "MEDIUM"          # LOW | MEDIUM | HIGH | CRITICAL
    }
)

result = response.json()
print(f"Decision: {result['decision']}")
print(f"Reasoning: {result['reasoning']}")
```

Oczekiwana odpowiedz:
```json
{
  "decision": "ALLOW",
  "reasoning": "System w stanie normalnym. Zasoby dostepne.",
  "agent_id": "AGT-003",
  "guardian_laws_checked": ["G3", "G6", "G8"],
  "veto_triggered": false,
  "session_hash": "a3f9b2c1d4e5"
}
```

---

## Krok 4: Akcja z VETO check

Akcje o wysokim ryzyku wymagaja quorum 2 agentow:

```python
# Przyklad: akcja HIGH — wymaga zgody 2 agentow
response = httpx.post(
    f"{BASE_URL}/actions/execute",
    headers=headers,
    json={
        "action_type": "PROCESS_PAYMENT",
        "criticality": "HIGH",
        "payload": {"amount": 500.00, "currency": "PLN"},
        "requesting_agent": "AGT-EXT-001"
    }
)

result = response.json()
if result["decision"] == "PENDING":
    print("Oczekiwanie na quorum (min. 2 agenty)")
elif result["decision"] == "DENY":
    print(f"VETO! Powod: {result['veto_reason']}")
else:
    print("Akcja zatwierdzona!")
```

**Akcje CRITICAL sa zawsze blokowane przez VETO:**
```python
# To zwroci Decision.DENY
response = httpx.post(
    f"{BASE_URL}/actions/execute",
    headers=headers,
    json={
        "action_type": "PURGE",          # CRITICAL action
        "criticality": "CRITICAL"
    }
)
# result["decision"] == "DENY" zawsze
```

---

## Krok 5: Subskrypcja zdarzen (WebSocket)

```python
import asyncio
import websockets
import json

async def listen_to_events():
    uri = f"wss://api.adrion369.example.com/ws/events"
    async with websockets.connect(
        uri,
        extra_headers={"Authorization": f"Bearer {token}"}
    ) as ws:
        async for message in ws:
            event = json.loads(message)
            print(f"[{event['type']}] {event['data']}")

asyncio.run(listen_to_events())
```

---

## Kody odpowiedzi HTTP

| Kod | Znaczenie |
|-----|-----------|
| `200` | OK — decyzja ALLOW |
| `202` | Accepted — decyzja PENDING (oczekiwanie na quorum) |
| `403` | Forbidden — VETO (akcja CRITICAL lub naruszenie Guardian Laws) |
| `401` | Unauthorized — nieprawidlowy/wygasly token |
| `422` | Unprocessable — nieprawidlowe pola zapytania |
| `429` | Too Many Requests — rate limit przekroczony |

---

## Limity i Rate Limiting

- **Free tier:** 100 zapytan / dzien na agent_id
- **Business tier:** 10 000 zapytan / dzien
- Naglowek `X-RateLimit-Remaining` informuje o pozostalym limicie
- Reset o 00:00 UTC

---

## Dalsze kroki

- [VETO-RULE.md](../VETO-RULE.md) — szczegoly reguly VETO
- [PERSONA-MAPPING.md](../PERSONA-MAPPING.md) — lista agentow i trybow
- [162D-DECISION-SPACE.md](../162D-DECISION-SPACE.md) — architektura przestrzeni decyzyjnej
- [security/](../security/) — dokumentacja bezpieczenstwa v5.6

---

## Wsparcie

Problemy? Otworz Issue na GitHub lub skontaktuj sie z zespolem ADRION 369.
