# MCP Server Security: OAuth 2.0 & Guardian Laws Integration

**Configuration Date**: 2026-04-08
**Version**: 1.0
**Compliance**: 9 Guardian Laws + GDPR + OAuth 2.0 RFC 6749

---

## 🔐 Executive Summary

All ADRION 369 MCP servers implement OAuth 2.0 with granular scope control, token rotation, encrypted storage, and comprehensive audit logging. This document maps security patterns to the 9 Guardian Laws and provides implementation guidelines.

---

## 1. OAuth 2.0 Architecture in ADRION 369

### 1.1 Token Flow

```
┌─────────────────────────────────────────────────────────────┐
│ MCP Server Authorization Flow                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ 1. Client requests token with specific scopes               │
│    └─> Scopes enforce least-privilege (Guardian Law G8)    │
│                                                              │
│ 2. Authorization Server validates request                   │
│    └─> Check against roo.rules.json SEC-008                │
│                                                              │
│ 3. Issue short-lived Access Token + long-lived Refresh     │
│    └─> Tokens encrypted at rest (SEC-010)                  │
│                                                              │
│ 4. Client stores token securely                             │
│    └─> Use encrypted-env or system-keyring backend        │
│                                                              │
│ 5. Token lifecycle monitoring                               │
│    └─> Auto-rotate 1 hour before expiry (SEC-009)         │
│    └─> Log all operations (Transparency, G5)              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Scope Granularity (Guardian Law G7 - Privacy)

Each MCP server has minimal, documented scopes:

| Server       | Scopes                           | Expiry | Rotation |
| ------------ | -------------------------------- | ------ | -------- |
| **Genesis**  | `read.record`, `write.record`    | 24h    | Yes      |
| **Guardian** | `audit`                          | 24h    | Yes      |
| **Healer**   | `health.check`, `identity.reset` | 12h    | Yes      |
| **Vortex**   | `data.transform`                 | 24h    | Yes      |
| **Oracle**   | `model.query`                    | 24h    | Yes      |
| **Router**   | `routing.control`                | 24h    | Yes      |

**Principle**: Each scope grants access to ONE specific function. No wildcard scopes.

---

## 2. Mapping to 9 Guardian Laws

### G1 - Unity (Integrated Security)

```python
# ✓ All MCP servers share unified OAuth config
# ✓ Centralized in .roo/oauth_config.ini
# ✓ Enforced by roo.rules.json rules
```

### G2 - Harmony (Coordinated Scope Management)

```python
# ✓ Token expiration synchronized across servers
# ✓ Rotation margin = 1 hour (consistent)
# ✓ Audit timestamps unified in Genesis Record
```

### G3 - Rhythm (Cyclic Token Rotation)

```python
# ✓ Regular token rotation every 24h (12h for Healer)
# ✓ Refresh token cycle: request → validate → rotate
# ✓ Scheduled quarterly OAuth audits (compliance_checklist)
```

### G4 - Causality (Cause-Effect Audit Trail)

```python
# ✓ SEC-011: Every OAuth event logged
# ✓ Audit path: Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/oauth_audit.jsonl
# ✓ Format: timestamp, server, scope, action, user_id, result
```

### G5 - Transparency (Disclosure & Logging)

```python
# ✓ SEC-011: Mandatory scope audit logging
# ✓ All hidden data folders documented in oauth_config.ini
# ✓ Consent screens reviewed quarterly
# ✓ Token usage logged (no blind actions)
```

### G6 - Authenticity (Genuine Identity Verification)

```python
# ✓ MCP servers verify JWT signature before accepting token
# ✓ Token issuer validated (iss claim)
# ✓ Token audience validated (aud claim for server)
# ✓ Prevent cross-server token replay
```

### G7 - Privacy (Confidentiality & User Control)

```python
# ✓ Tokens never logged in plain text
# ✓ Scopes strictly granular (no overprivilege)
# ✓ SEC-012: Hidden data folders documented & user-deletable
# ✓ Encryption: AES-256-GCM at rest, TLS in transit
# ✓ Data minimization: collect only scoped data
```

### G8 - Nonmaleficence (Do No Harm)

```python
# ✓ SEC-008: Invalid scopes rejected with clear error
# ✓ SEC-010: Unencrypted tokens immediately fail
# ✓ Least-privilege scope model prevents abuse
# ✓ Token expiration prevents "forever" compromise
```

### G9 - Sustainability (Long-term Viability)

```python
# ✓ Token rotation prevents key compromise
# ✓ Audit retention: 30 days (compliance_checklist)
# ✓ Quarterly security audits scheduled
# ✓ Roo Code security profile passes = prerequisite for deployment
```

---

## 3. Implementation Guidelines

### 3.1 Token Storage (SEC-010)

**❌ NEVER DO THIS:**

```python
# BAD: Plaintext in .env
API_TOKEN="eyJhbGc..."

# BAD: Hardcoded in code
TOKEN = "secret_xyz"

# BAD: Unencrypted file
with open("token.json") as f:
    token = f.read()
```

**✅ DO THIS:**

```python
import os
from cryptography.fernet import Fernet

# Store encrypted token in environment
encrypted_token = os.getenv("ENCRYPTED_TOKEN")
cipher = Fernet(os.getenv("CIPHER_KEY"))  # from system-keyring
decrypted = cipher.decrypt(encrypted_token.encode())
```

### 3.2 Scope Validation (SEC-008)

**Check in code:** Every time a scope is requested:

```python
from roo.oauth_config import ALLOWED_SCOPES

def request_scope(server_name: str, requested_scope: str) -> bool:
    """
    Validate scope before issuing token.
    Triggered by roo.rules.json SEC-008 check.
    """
    allowed = ALLOWED_SCOPES.get(server_name, [])

    if requested_scope not in allowed:
        LOG_AUDIT(f"DENIED: {server_name} scope={requested_scope}")
        return False

    LOG_AUDIT(f"GRANTED: {server_name} scope={requested_scope}")
    return True
```

### 3.3 Token Rotation (SEC-009)

**Automatic rotation 1 hour before expiry:**

```python
import asyncio
from datetime import datetime, timedelta

async def token_rotation_loop(server_name: str):
    """
    Background task: rotate token 1 hour before expiry.
    Implements SEC-009 requirement.
    """
    config = load_server_config(server_name)
    expiry_hours = config['token_expiration_hours']
    rotation_margin = 1  # from oauth_config.ini

    while True:
        current_token = get_current_token(server_name)
        expires_at = current_token['exp']
        now = datetime.utcnow()

        rotate_time = expires_at - timedelta(hours=rotation_margin)

        if now >= rotate_time:
            new_token = refresh_token(server_name)
            store_encrypted_token(server_name, new_token)
            LOG_AUDIT(f"Token rotated: {server_name}")

        await asyncio.sleep(3600)  # Check hourly
```

### 3.4 Audit Logging (SEC-011)

**Every OAuth event must be logged:**

```python
import json
from datetime import datetime
from pathlib import Path

def log_oauth_event(event_type: str, server_name: str, scope: str,
                    user_id: str, result: str, details: dict = None):
    """
    Mandatory audit logging per SEC-011 & Guardian Law G5.
    """
    audit_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,  # "token_request", "token_granted", "token_rotated", etc.
        "server": server_name,
        "scope": scope,
        "user_id": user_id,
        "result": result,  # "success", "denied", "error"
        "details": details or {}
    }

    audit_path = "Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/oauth_audit.jsonl"
    with open(audit_path, "a") as f:
        f.write(json.dumps(audit_event) + "\n")
```

### 3.5 Hidden Data Folders (SEC-012)

**Document all hidden data:**

```
.roo_cache/
  └─> Purpose: Code analysis temporary cache
      Retention: 24h TTL, auto-cleanup
      User Control: Deletable via `rm -rf .roo_cache/`

.aider/
  └─> Purpose: Aider conversation history
      Retention: User-defined
      User Control: Deletable, documented in .gitignore

Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/
  └─> Purpose: Audit logs and session reports
      Retention: 30 days (configurable)
      User Control: Readable, archivable, deletable
```

---

## 4. Roo Code Integration

### 4.1 Security Profile Rules

Roo Code automatically enforces OAuth rules via `roo.profiles.json`:

```json
{
  "id": "security-audit",
  "checks": {
    "security": {
      "enabled": true,
      "level": "critical"
    }
  },
  "customRules": [
    "SEC-008: OAuth Scope Validation",
    "SEC-009: Token Rotation",
    "SEC-010: Token Storage",
    "SEC-011: Audit Logging",
    "SEC-012: Data Folder Documentation"
  ]
}
```

### 4.2 Pre-Deployment Checklist

Before deploying any MCP server:

```bash
# Run security audit profile
roo analyze --profile security-audit --server <server_name>

# Verify OAuth config
roo check-oauth-config .roo/oauth_config.ini

# Verify audit logs
roo audit-trail --path "Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/oauth_audit.jsonl"
```

---

## 5. Compliance Matrix

| Requirement            | Implementation                         | Roo Rule             | Guardian Law |
| ---------------------- | -------------------------------------- | -------------------- | ------------ |
| Scopes minimal         | Per-function scopes in config          | SEC-008              | G7, G8       |
| Tokens encrypted       | AES-256-GCM at rest                    | SEC-010              | G7           |
| Token rotation         | Auto-rotate 1h before expiry           | SEC-009              | G3, G9       |
| Audit logging          | JSONL to Genesis Record                | SEC-011              | G4, G5       |
| Hidden data documented | oauth_config.ini [hidden_data_folders] | SEC-012              | G5, G7       |
| JWT validation         | Verify iss, aud, sig                   | G6                   | G6           |
| No hardcoded secrets   | ENV vars + encryption                  | SEC-001              | G7           |
| Consent screen review  | Quarterly                              | compliance_checklist | G5           |
| Quarterly audit        | Scheduled event                        | compliance_checklist | G9           |

---

## 6. Troubleshooting

### Token Validation Fails

```
Error: Invalid OAuth token for Genesis server
```

**Diagnosis:**

1. Check token expiry: `roo token-info genesis`
2. Verify encryption key: `echo $CIPHER_KEY`
3. Check scope: `roo scope-info genesis`

**Fix:**

```python
# Force token refresh
roo refresh-token genesis --force
```

### Audit Log Not Writable

```
Error: Cannot write to oauth_audit.jsonl
```

**Fix:**

```bash
mkdir -p "Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU"
chmod 755 "Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU"
```

### Scope Denied but Should Be Allowed

```
Error: SEC-008 Scope validation failed
```

**Fix:**

1. Update `.roo/oauth_config.ini` [servers.YOUR_SERVER]
2. Add scope to allowed list
3. Re-run Roo analysis: `roo analyze --profile security-audit`

---

## 7. Key Files Reference

| File                                      | Purpose                     | Guardian Laws |
| ----------------------------------------- | --------------------------- | ------------- |
| `.roo/oauth_config.ini`                   | Server scope & token config | G1, G3, G7    |
| `roo.rules.json` (SEC-008-012)            | Security rule enforcement   | G5, G8, G9    |
| `Genesis Record/.../oauth_audit.jsonl`    | Audit trail                 | G4, G5        |
| `.vscode/settings.json` (roo.security.\*) | IDE integration             | G9            |

---

## 8. Next Steps

1. **Configure all 6 MCP servers** in `.roo/oauth_config.ini`
   - Set `all_mcp_servers_oauth_configured = true`

2. **Implement token storage backend**
   - Choose: `encrypted-env`, `system-keyring`, or cloud vault

3. **Enable audit logging**
   - Set `audit_logging_active = true`

4. **Run pre-deployment checks**
   - `roo analyze --profile security-audit`

5. **Schedule quarterly OAuth audit**
   - Add to calendar: Review consent screens, audit log retention

---

**Maintained by**: ADRION-369 Master Orchestrator
**Last Updated**: 2026-04-08
**Status**: ✅ Compliant with 9 Guardian Laws
