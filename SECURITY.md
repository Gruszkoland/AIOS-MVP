# Security Policy — AIOS MVP

AIOS MVP takes security seriously. We appreciate responsible vulnerability disclosure and will work with you to resolve issues promptly.

## Supported Versions

| Version | Status | Security Updates |
|---------|--------|------------------|
| v0.2+ | Current | ✅ Active |
| v0.1-alpha | Beta | ✅ Active (3 months from v0.2 release) |
| v0.0.x | EOL | ❌ No |

## Reporting Vulnerabilities

### Preferred channels

- **Email:** [security@adrion369.dev](mailto:security@adrion369.dev)
- **GitHub Security Advisory:** [Report a vulnerability](https://github.com/Gruszkoland/AIOS-MVP/security/advisories/new)
- **GitHub Issues:** Only for LOW severity public issues

### What to include

- Type of vulnerability (SQL injection, XSS, memory safety, etc.)
- Affected component(s) and file path
- Steps to reproduce (PoC code appreciated)
- Impact assessment
- Suggested fix (if available)

### Response Timeline

| Severity | CVSS | Acknowledgement | Fix Target | Public Disclosure |
|----------|------|-----------------|------------|-------------------|
| **CRITICAL** | 9.0-10.0 | 24 hours | 3-7 days | After patch release |
| **HIGH** | 7.0-8.9 | 48 hours | 14 days | After patch release |
| **MEDIUM** | 4.0-6.9 | 7 days | 30 days | 30-60 days embargo |
| **LOW** | 0.1-3.9 | 14 days | Next minor release | 60+ days embargo |

### CRITICAL issues (G6 Nonmaleficence, G8 Justice)

**Do NOT open a public issue.** Instead:

1. Email [security@adrion369.dev](mailto:security@adrion369.dev) or use GitHub Security Advisories (private mode)
2. Include: description, affected component, steps to reproduce, and suggested fix
3. You will receive acknowledgement within **24 hours**
4. A fix will be developed privately and released within **3-7 days**

### What qualifies as CRITICAL?

Per the [Guardian Laws](docs/GUARDIAN_LAWS_CANONICAL.json):

- **G6 Nonmaleficence violation** — prevent harm: remote code execution, SQL injection, data destruction
- **G8 Justice violation** — fairness: unauthorized privilege escalation, discrimination, unfair treatment

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
