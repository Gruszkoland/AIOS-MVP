# Security Policy — ADRION 369

## Supported Versions

| Version | Supported |
| ------- | --------- |
| v4.x    | Yes       |
| < v4.0  | No        |

## Reporting a Vulnerability

### Non-critical issues (LOW / MEDIUM / HIGH)

Open a [Security Vulnerability issue](../../issues/new?template=security_vulnerability.yml) using the provided template.

### CRITICAL issues (G7 Privacy, G8 Nonmaleficence)

**Do NOT open a public issue.** Instead:

1. Use [GitHub Security Advisories](../../security/advisories/new) to report privately.
2. Include: description, affected component, steps to reproduce, and suggested fix.
3. You will receive acknowledgement within **48 hours**.
4. A fix will be developed privately and released as a patch within **7 days** for CRITICAL severity.

### What qualifies as CRITICAL?

Per the [Guardian Laws](docs/GUARDIAN_LAWS_CANONICAL.json):

- **G7 Privacy violation** — unauthorized data exposure, PII leaks, authentication bypass
- **G8 Nonmaleficence violation** — remote code execution, SQL injection, data destruction

### Scope

The following components are in scope:

- `arbitrage/` — Flask application and all blueprints
- `uap/backend/` — UAP orchestrator
- `cmd/`, `internal/` — Go Vortex server
- `kubernetes/` — deployment manifests
- `docker-compose*.yml` — container configurations
- `.github/workflows/` — CI/CD pipelines

### Out of scope

- Third-party dependencies (report upstream)
- `Genesis Record/` — documentation only
- Development tooling (`.aider/`, scripts)

## Security Measures

- Parameterized SQL only (no string interpolation)
- Guardian Laws engine with CRITICAL=instant DENY
- Rate limiting on all POST endpoints
- Circuit breakers on external services
- Weekly automated scans: bandit (SAST), safety (dependencies), Trivy (containers)
- Dependabot monitoring: pip, docker, gomod, github-actions
