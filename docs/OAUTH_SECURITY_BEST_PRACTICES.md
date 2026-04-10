# OAuth 2.0 & Security Best Practices for MCP Servers

## ADRION 369 Multi-Agent Swarm Orchestrator

**Document Version**: 1.0
**Created**: 2026-04-08
**Scope**: OAuth, token management, and secret handling for Model Context Protocol services

---

## 1. OAuth 2.0 Architecture Overview

### 1.1 Core Principles (Guardian Law G7 - Privacy)

All MCP servers MUST operate under OAuth 2.0 protocol with the following guarantees:

- **No Password Sharing**: Applications receive temporary tokens, never user credentials
- **Least Privilege**: Each token has explicitly defined scopes (granular permissions)
- **Token Isolation**: Tokens can be revoked without changing passwords
- **Audit Trail**: All OAuth operations logged for transparency (G5-Transparency)

### 1.2 Token Flow Diagram

```
User → Authorization Server → Grant Code → Access Token (24h) + Refresh Token
        ↓
    Verification
        ↓
   MCP Server (with scopes)
```

---

## 2. Scopes Definition & Configuration

### 2.1 Available MCP Server Scopes

| Server   | Scope URI                             | Permissions               | Guardian Law        |
| -------- | ------------------------------------- | ------------------------- | ------------------- |
| Genesis  | `mcp://genesis.adrion/read.record`    | Read Genesis Record logs  | G7 (Privacy)        |
| Genesis  | `mcp://genesis.adrion/write.record`   | Write session reports     | G5 (Transparency)   |
| Guardian | `mcp://guardian.adrion/audit`         | Perform security audits   | G8 (Nonmaleficence) |
| Healer   | `mcp://healer.adrion/health.check`    | Health monitoring         | G2 (Harmony)        |
| Healer   | `mcp://healer.adrion/identity.reset`  | Identity reset on failure | G6 (Authenticity)   |
| Vortex   | `mcp://vortex.adrion/data.transform`  | Data transformation tasks | G3 (Rhythm)         |
| Oracle   | `mcp://oracle.adrion/model.query`     | LLM model inference       | G4 (Causality)      |
| Router   | `mcp://router.adrion/routing.control` | Agent routing decisions   | G1 (Unity)          |

### 2.2 Scope Granularity Rules

❌ **ANTI-PATTERN** (Too Broad):

```json
{
  "scope": "mcp://*/all" // All permissions - violates G7
}
```

✅ **CORRECT PATTERN** (Minimal Privilege):

```json
{
  "scope": "mcp://genesis.adrion/read.record" // Only read Genesis logs
}
```

### 2.3 Configuring Scopes in MCP Servers

**File**: `.roo/mcp.json`

```json
{
  "mcpServers": {
    "genesis": {
      "command": "python",
      "args": ["mcp_genesis_app.py"],
      "env": {
        "MCP_OAUTH_SCOPES": "mcp://genesis.adrion/read.record,mcp://genesis.adrion/write.record",
        "MCP_TOKEN_EXPIRATION": "86400",
        "MCP_SCOPE_AUDIT_LOG": "Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/oauth_audit.log"
      }
    }
  }
}
```

---

## 3. Token Management & Rotation

### 3.1 Access Token Lifecycle

| Phase        | Duration       | Action                         | Logging                            |
| ------------ | -------------- | ------------------------------ | ---------------------------------- |
| **Issued**   | T=0            | OAuth server grants token      | Log: token_id, scopes, created_at  |
| **Active**   | T=0 to T=86400 | Token used for API calls       | Log: each API call with scope used |
| **Expiring** | T=82800 (23h)  | Refresh token requested        | Log: refresh_token_request         |
| **Expired**  | T>86400        | Token revoked, new flow starts | Log: token_revoked, reason=expiry  |
| **Revoked**  | Manual         | User/admin revokes token       | Log: revocation_reason, revoked_by |

### 3.2 Token Rotation Strategy

Implement automatic token rotation (REQUIRED for compliance):

```python
# mcp_servers/base_oauth_handler.py
class OAuthTokenHandler:
    def __init__(self, token_expiration_hours=24):
        self.token_expiration_hours = token_expiration_hours
        self.rotation_margin_hours = 1  # Refresh 1h before expiry

    async def ensure_valid_token(self):
        """Automatically rotate token if expiring soon."""
        if self.token_expires_in_hours() < self.rotation_margin_hours:
            await self.rotate_token()
        return self.access_token

    async def rotate_token(self):
        """Refresh access token using refresh_token."""
        new_token = await self.oauth_provider.refresh_token(
            refresh_token=self.refresh_token,
            scopes=self.authorized_scopes
        )
        await self.audit_log(f"token_rotated", {
            "old_token_id": self.access_token[:8],  # Last 8 chars of token
            "new_token_id": new_token["access_token"][:8],
            "scopes": self.authorized_scopes,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.access_token = new_token["access_token"]
        self.refresh_token = new_token.get("refresh_token", self.refresh_token)
```

### 3.3 Token Storage (CRITICAL - G7 Privacy)

❌ **FORBIDDEN**:

```python
# NEVER do this:
TOKEN = "oauth2_abc123xyz789..."  # Hardcoded in source code
os.environ["TOKEN"] = "oauth2_abc123xyz789..."  # Plain text in environment
```

✅ **REQUIRED - Encrypted Storage**:

```python
# Use system keyring or encrypted secrets backend
import keyring
import cryptography.fernet

# Encrypt token with master key
cipher = cryptography.fernet.Fernet(master_key)
encrypted_token = cipher.encrypt(oauth_token.encode())

# Store in secure location
keyring.set_password("adrion-mcp", "genesis_oauth_token", encrypted_token)

# Retrieve and decrypt
retrieved_encrypted = keyring.get_password("adrion-mcp", "genesis_oauth_token")
token = cipher.decrypt(retrieved_encrypted).decode()
```

**Environment Protection**:

```bash
# .env.template (Never commit actual tokens)
OAUTH_TOKEN_ENCRYPTED=true
OAUTH_ENCRYPTION_KEY=<use-aws-kms-or-vault>
OAUTH_KEYRING_BACKEND=system  # or: aws-secretsmanager, hashicorp-vault
```

---

## 4. Audit Logging & Compliance (G5 - Transparency)

### 4.1 Required Audit Events

Every OAuth operation MUST be logged:

```json
{
  "event_type": "oauth_scope_granted",
  "timestamp": "2026-04-08T14:32:15Z",
  "server": "genesis",
  "user_id": "adiha@adrion369",
  "scopes_granted": [
    "mcp://genesis.adrion/read.record",
    "mcp://genesis.adrion/write.record"
  ],
  "decision": "approved",
  "decision_reason": "user_explicit_consent",
  "token_id_hash": "sha256:abc123...",
  "ip_address": "10.0.1.5",
  "user_agent": "ADRION-369/4.0.1"
}
```

### 4.2 Audit Log Storage

**Location**: `Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/oauth_audit.jsonl`

```python
# mcp_servers/audit_logger.py
async def audit_oauth_event(event_type, details):
    """Log OAuth event to Genesis Record."""
    audit_entry = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        **details
    }

    # Log to file (append-only)
    audit_log_path = "Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/oauth_audit.jsonl"
    async with aiofiles.open(audit_log_path, "a") as f:
        await f.write(json.dumps(audit_entry) + "\n")

    # Also log to Roo Code analysis (for visibility)
    logger.info(f"OAuth Event: {event_type}", extra=audit_entry)
```

---

## 5. Application Data Folder (Hidden Data) Compliance

### 5.1 Visible vs Hidden Data

| Data Type     | Location             | User Visibility              | Deletion                     |
| ------------- | -------------------- | ---------------------------- | ---------------------------- |
| **Visible**   | Genesis Record/      | Full visibility              | User can delete anytime      |
| **Hidden**    | .roo_cache/, .aider/ | Not visible in file explorer | User can manage via settings |
| **Encrypted** | secrets backend      | Not visible, encrypted       | User can revoke access       |

### 5.2 Disclosure Requirements (G7 - Privacy)

Every MCP server using hidden data MUST document:

```markdown
## Data Storage Policy

**Hidden Folders Used**:

- `.roo_cache/` - Code analysis cache (auto-expiring, 24h TTL)
- `.aider/` - Conversation history (user-deletable)

**User Control**:

- Delete cache: Settings → Roo Code → Clear Cache
- Delete history: Settings → Aider → Clear History
- Revoke API access: Settings → OAuth Connections → Disconnect Genesis

**Data Retention**:

- Cache: 24 hours (auto-cleaned)
- History: Until user deletion
- Logs: 30 days (archived)
```

---

## 6. Security Rules in Roo Code (roo.rules.json)

### 6.1 Built-in OAuth Security Checks

| Rule ID | Check                       | Severity | Guardian Law      |
| ------- | --------------------------- | -------- | ----------------- |
| SEC-008 | OAuth Scope Validation      | Warning  | G7 (Privacy)      |
| SEC-009 | Missing Token Rotation      | Warning  | G7 (Privacy)      |
| SEC-010 | Unencrypted Token Storage   | Error    | G7 (Privacy)      |
| SEC-011 | Missing Scope Audit Logging | Warning  | G5 (Transparency) |
| SEC-012 | App Data Folder Leakage     | Warning  | G7 (Privacy)      |

### 6.2 Running Security Analysis

```bash
# Analyze OAuth compliance
roo analyze --profile security-audit --rule SEC-008,SEC-010

# Check for hardcoded secrets
roo analyze --rule SEC-001 --languages python

# Full security audit with Guardian Laws
roo analyze --profile security-audit
```

---

## 7. Practical Implementation: Genesis MCP Server

### 7.1 OAuth Initialization

```python
# mcp_genesis_app.py
from mcp_servers.base_oauth_handler import OAuthTokenHandler
from mcp_servers.audit_logger import audit_oauth_event

class GenesisMCPServer:
    def __init__(self):
        self.oauth = OAuthTokenHandler(
            token_expiration_hours=24,
            scopes=[
                "mcp://genesis.adrion/read.record",
                "mcp://genesis.adrion/write.record"
            ]
        )

    async def initialize(self):
        """Initialize with OAuth, log to Genesis Record."""
        token = await self.oauth.ensure_valid_token()

        await audit_oauth_event("mcp_server_start", {
            "server": "genesis",
            "status": "initialized",
            "scopes": self.oauth.authorized_scopes,
            "token_valid_hours": 24
        })

    async def handle_request(self, request):
        """Check token before processing request."""
        # Ensure token is still valid
        await self.oauth.ensure_valid_token()

        # Process request
        result = await self._process(request)

        # Audit the operation
        await audit_oauth_event("api_call", {
            "server": "genesis",
            "operation": request.operation,
            "scopes_used": self.oauth.get_required_scopes(request.operation)
        })

        return result
```

---

## 8. Compliance Checklist

### Before Deployment

- [ ] All MCP servers have OAuth configured
- [ ] Scopes are documented in `.roo/mcp.json`
- [ ] Token expiration is set (24 hours recommended)
- [ ] Token rotation is implemented
- [ ] Tokens stored encrypted, never plain text
- [ ] Audit logging to Genesis Record active
- [ ] Hidden data folders documented in server README
- [ ] Roo Code security rules pass (no SEC-008/010/011/012 violations)
- [ ] Security profile analysis passes
- [ ] OAuth consent screen reviewed and approved

### Quarterly Audits

- [ ] Review OAuth audit logs for anomalies
- [ ] Verify token rotation working correctly
- [ ] Check for orphaned/revoked tokens
- [ ] Audit unused scopes (remove if not needed)
- [ ] Update Guardian Laws alignment documentation

---

## 9. Reference: Guardian Laws Mapping

| Law                   | OAuth Aspect                   | Implementation                       |
| --------------------- | ------------------------------ | ------------------------------------ |
| **G1-Unity**          | Consistent auth across servers | Use common OAuthTokenHandler         |
| **G2-Harmony**        | Seamless token refresh         | Auto-rotate before expiry            |
| **G3-Rhythm**         | Regular audit cycles           | Quarterly compliance checks          |
| **G4-Causality**      | Token→Scope→Action chain       | Log all three in audit trail         |
| **G5-Transparency**   | OAuth disclosure               | Audit log all decisions              |
| **G6-Authenticity**   | Real user grants               | Require explicit consent UI          |
| **G7-Privacy**        | Minimal scopes, encryption     | Least privilege + at-rest encryption |
| **G8-Nonmaleficence** | No token abuse                 | Revocation + monitoring              |
| **G9-Sustainability** | Token lifecycle mgmt           | Automatic rotation & cleanup         |

---

## 10. Support & Questions

For OAuth configuration issues:

1. Check `.roo/mcp.json` scopes definition
2. Review audit logs: `Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/oauth_audit.jsonl`
3. Run security analysis: `roo analyze --profile security-audit`
4. Check token: `keyring get adrion-mcp <server>_oauth_token`

---

**Maintained by**: ADRION-369 Master Orchestrator
**Last Updated**: 2026-04-08
**Compliance Standard**: OAuth 2.0 RFC 6749 + Guardian Laws Framework
