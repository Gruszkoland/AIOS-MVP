# Capability Model — AIOS MVP

The capability model is the security foundation of AIOS MVP. It enforces fine-grained access control between the kernel and advisory agents.

---

## Overview

Every agent can perform only actions it has been explicitly granted via a **capability bitmask**. This prevents:

- Privilege escalation (agent accessing kernel internals)
- Data exfiltration (agent reading sensitive I/O)
- Denial of service (agent consuming unlimited resources)
- Side-channel attacks (timing covert channels)

---

## Capability Types

Capabilities are grouped into 4 categories:

### 1. Data Access (bits 0-7)

```
CAP_READ_JOB_METADATA       (0x01)  — read job type, id, priority
CAP_READ_RESOURCE_METRICS   (0x02)  — read CPU, RAM, disk utilization
CAP_READ_AUDIT_LOG          (0x04)  — read historical decisions
CAP_READ_SYSTEM_STATE       (0x08)  — read scheduler state, EBDI values
```

### 2. Decision Making (bits 8-15)

```
CAP_RECOMMEND_APPROVE       (0x0100) — agent can suggest APPROVE
CAP_RECOMMEND_DENY          (0x0200) — agent can suggest DENY
CAP_RECOMMEND_FLAG          (0x0400) — agent can suggest FLAG_FOR_REVIEW
CAP_OVERRIDE_PREVIOUS       (0x0800) — agent can revoke past decisions
```

### 3. I/O Operations (bits 16-23)

```
CAP_WRITE_LOG               (0x010000) — append to audit trail
CAP_SEND_NOTIFICATION       (0x020000) — send alerts to ops
CAP_EXPORT_DATA             (0x040000) — export decisions to external systems
```

### 4. System Control (bits 24-31)

```
CAP_MODIFY_POLICY           (0x01000000) — change Guardian Laws enforcement
CAP_RESTART_SCHEDULER       (0x02000000) — trigger kernel restart
CAP_MANAGE_OTHER_AGENTS     (0x04000000) — create/destroy other agents
```

---

## Default Capability Sets

### SecurityGuardian (most restricted)

```rust
CAP_READ_JOB_METADATA
| CAP_READ_RESOURCE_METRICS
| CAP_RECOMMEND_DENY          // can reject unsafe decisions
| CAP_WRITE_LOG               // log its own decisions
```

**Why:** Only needs to see what it's deciding on; can reject but not approve (conservative bias).

### EthicsGuardian

```rust
CAP_READ_JOB_METADATA
| CAP_READ_RESOURCE_METRICS
| CAP_READ_SYSTEM_STATE
| CAP_RECOMMEND_APPROVE
| CAP_RECOMMEND_DENY
| CAP_WRITE_LOG
```

**Why:** Full view into decision context; can recommend approve/deny/flag.

### PerformanceGuardian

```rust
CAP_READ_RESOURCE_METRICS    // only resource data
| CAP_RECOMMEND_APPROVE
| CAP_RECOMMEND_DENY
| CAP_WRITE_LOG
```

**Why:** Specialized to resource constraints; doesn't need business logic context.

---

## Enforcement Mechanism

### At IPC Boundary

Every message from agent to kernel includes:

```rust
pub struct IpcMessage {
    from_agent_id: u32,
    required_capabilities: u32,         // bitmask of capabilities needed
    payload: [u8; 48],                  // agent data
}
```

**Kernel validates before processing:**

```pseudocode
if (agent_capabilities & required_capabilities) != required_capabilities:
    return Error::CapabilityDenied
else:
    process_message(payload)
```

### At Decision Execution

Before executing agent recommendation:

```pseudocode
if agent_can_recommend(verdict):      // e.g., CAP_RECOMMEND_DENY
    if recommendation_passes_guardian_laws():
        execute_recommendation()
    else:
        deny_recommendation()
else:
    return Error::CapabilityDenied
```

---

## Granting Capabilities

Capabilities are granted at agent initialization via `agents/config.toml`:

```toml
[[agents]]
name = "SecurityGuardian"
capabilities = [
    "CAP_READ_JOB_METADATA",
    "CAP_READ_RESOURCE_METRICS",
    "CAP_RECOMMEND_DENY",
    "CAP_WRITE_LOG",
]

[[agents]]
name = "EthicsGuardian"
capabilities = [
    "CAP_READ_*",                    # wildcard expansion
    "CAP_RECOMMEND_*",
    "CAP_WRITE_LOG",
]
```

**Rules:**
- Capabilities are immutable after agent creation
- No runtime capability grants (fail-safe)
- Capability changes require kernel restart + audit log entry

---

## Guardian Laws Alignment (G7, G8)

### G7: Privacy (CRITICAL)

Capability model protects privacy by:
- `CAP_READ_*` restricted to necessary data only
- `CAP_EXPORT_DATA` requires explicit grant
- Audit trail captures all agent access
- No agent has unrestricted access to all data

**Verification:**
```bash
# Audit: which agents have CAP_EXPORT_DATA?
grep -r "CAP_EXPORT_DATA" agents/config.toml

# Should be: none (unless explicitly needed)
```

### G8: Nonmaleficence (CRITICAL)

Capability model prevents harm by:
- `CAP_MODIFY_POLICY` restricted to ops team only (human approval)
- `CAP_RESTART_SCHEDULER` restricted (prevents DoS)
- `CAP_MANAGE_OTHER_AGENTS` restricted (prevents cascade failures)
- Dangerous capabilities default to `denied`

**Verification:**
```bash
# Audit: which agents can modify policy?
grep -r "CAP_MODIFY_POLICY" agents/config.toml

# Should be: none (kernel enforces, no agents modify laws)
```

---

## Testing

### Unit Tests

```rust
#[test]
fn test_capability_check_blocks_unauthorized_read() {
    let agent_caps = CAP_READ_JOB_METADATA;
    let required = CAP_READ_AUDIT_LOG;

    assert!(!has_capability(agent_caps, required));
}

#[test]
fn test_capability_check_allows_authorized_read() {
    let agent_caps = CAP_READ_JOB_METADATA | CAP_READ_AUDIT_LOG;
    let required = CAP_READ_AUDIT_LOG;

    assert!(has_capability(agent_caps, required));
}
```

### Integration Tests

```rust
#[tokio::test]
async fn test_security_guardian_denied_cap_recommend_approve() {
    let guardian = SecurityGuardian::new();
    let recommendation = guardian.recommend_approve();

    // Should fail — SecurityGuardian lacks CAP_RECOMMEND_APPROVE
    assert_eq!(recommendation, Err(CapabilityDenied));
}
```

### Fuzzing

Fuzz capability bitmask combinations to find unexpected state.

---

## References

- [ARCHITECTURE.md](./ARCHITECTURE.md) — IPC message format
- [CONTRIBUTING.md](../CONTRIBUTING.md) — unsafe code review (capability checks)
- `docs/GUARDIAN_LAWS_CANONICAL.json` — G7, G8 definitions
