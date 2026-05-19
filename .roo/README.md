# Roo Code Configuration for ADRION 369

## Overview

Complete Roo Code configuration for the ADRION 369 Multi-Agent Swarm Orchestrator project with 162D decision space.

## Configuration Files

### Main Configuration Files

1. **`.roo.json`** - Primary Roo Code configuration
   - Project metadata (name, version, description)
   - File patterns (include/exclude)
   - Code analysis settings (linters, type checking, security)
   - Testing framework configuration
   - Architecture layers definition
   - Deployment environments
   - Workspace folder structure
   - Performance optimization settings

2. **`.roorc`** - Runtime configuration (INI format)
   - Core settings (profile, logging, verbosity)
   - Analysis engine parameters
   - Code analysis controls
   - Linters and formatters configuration
   - Testing settings
   - Security scanning options
   - Performance tuning
   - Reporting configuration
   - Integration settings
   - Language-specific configurations

3. **`.roo.ignore`** - Ignore patterns (gitignore syntax)
   - Virtual environments and dependencies
   - Python cache and compiled files
   - Testing and coverage artifacts
   - IDE and editor files
   - Git and system files
   - Temporary files and backups
   - Project-specific exclusions

4. **`roo.profiles.json`** - Analysis profiles
   - **production**: Strict analysis with high security/documentation
   - **development**: Relaxed analysis for active development
   - **ci-pipeline**: Automated CI/CD checks
   - **security-audit**: Deep security analysis
   - **performance-tuning**: Performance optimization focus
   - **documentation**: Documentation completeness checks

5. **`roo.rules.json`** - Custom analysis rules
   - Security rules (hardcoded secrets, SQL injection, etc.)
   - Performance rules (N+1 queries, inefficient patterns)
   - Code quality rules
   - Architecture patterns

6. **`mcp.json`** - Model Context Protocol server configuration
   - File system access server
   - Git integration server
   - Python code analysis server
   - Docker integration server
   - PostgreSQL integration (optional)
   - Additional tool integrations

## VS Code Integration

The following settings are configured in `.vscode/settings.json`:

### Roo Code Settings

```json
{
  "roo.analysis.enabled": true,
  "roo.analysis.complexity": true,
  "roo.analysis.security": true,
  "roo.analysis.performance": true,
  "roo.testing.framework": "pytest",
  "roo.codeNavigation.enableSymbolIndexing": true
}
```

### File Patterns

- **Include**: `**/*.py`, `**/*.go`, `**/*.ps1`, `**/*.ts`, Dockerfiles, scripts, MCP servers
- **Exclude**: `.venv`, `__pycache__`, `.git`, `node_modules`, build artifacts

### Linters

- Python: Ruff, Pylint, Mypy
- Go: golangci-lint, go vet
- PowerShell: PSScriptAnalyzer
- Docker: hadolint

## Project Structure Recognition

Roo Code is configured to recognize:

- **Orchestration Layer**: `adrion-swarm/`, `persona-agents/`
- **MCP Services**: `mcp_servers/`, MCP implementations
- **Core Services**: `scripts/`, `arbitrage/` business logic
- **Infrastructure**: `kubernetes/`, Docker compose files, Dockerfiles
- **API Layer**: `cmd/`, `internal/`, server implementations
- **Database**: `scripts/db/` schemas and migrations
- **Documentation**: `docs/`, API documentation

## Analysis Profiles

### Development Profile (Default)

- Security: High level
- Complexity: Max cyclomatic 12
- Coverage: Min 70%
- Documentation: Optional
- Typing: Not strict

### Production Profile

- Security: Critical level
- Complexity: Max cyclomatic 8
- Coverage: Min 85%
- Documentation: Required
- Typing: Strict

### CI Pipeline Profile

- Security: Critical with deep scanning
- Complexity: Max cyclomatic 10
- Coverage: Min 80% (fails if under)
- Documentation: API docs required
- Linting: Warnings not treated as errors

## Security Configuration

Security features enabled:

- Hardcoded secrets detection
- SQL injection vulnerability scanning
- Unvalidated user input detection
- Weak cryptography detection
- HTTPS enforcement
- Insecure deserialization detection
- Missing authentication detection
- Static code analysis (SAST)
- Dependency vulnerability scanning

## Runtime Settings

### Performance Tuning

- Analysis timeout: 30 seconds
- Max file size: 5 MB
- Parallel analysis: Enabled
- Cache: Enabled with 24-hour TTL
- Incremental analysis: Enabled

### Reporting

- Auto-generate reports on save
- Report formats: JSON, HTML
- Report location: `reports/`
- Metrics tracked: Complexity, Coverage, Security, Performance

## Integration Points

### Git Integration

- Branch info display
- Commit history
- 3-line diff context

### Docker Integration

- Container analysis
- Image validation
- Dockerfile linting

### Kubernetes Integration

- Manifest validation
- Schema validation
- Deployment analysis

## AI Features

- Mode: Hybrid (local + remote)
- Local LLM endpoint: `http://localhost:11434`
- Refactoring suggestions: Enabled
- Performance optimizations: Enabled
- Security advisories: Enabled
- Architecture analysis: Enabled

## Guardrails

Enforcement policies:

- Naming conventions (PEP 8 for Python, Go conventions for Go)
- Security policies (no hardcoded secrets, secure patterns)
- Documentation requirements
- Type hints when applicable

## Security & OAuth Configuration

Complete OAuth 2.0 security framework for ADRION 369 MCP Servers:

### 📚 OAuth Documentation (Start Here!)

1. **[mcp-security.md](mcp-security.md)** ⭐ Main Guide
   - Complete OAuth 2.0 implementation for all 6 MCP servers
   - Token management, scope validation, encryption
   - Guardian Laws mapping (G1-G9)
   - Roo Code security rules (SEC-008-012) integration
   - Pre-deployment checklist

2. **[oauth-faq.md](oauth-faq.md)** 🤔 Quick Reference
   - 10 most common OAuth questions
   - How tokens work, token rotation, audit logging
   - Troubleshooting common issues
   - Step-by-step configuration verification

3. **[google-oauth-mapping.md](google-oauth-mapping.md)** 🗺️ Architecture Guide
   - Maps "Bezpieczny dostęp do danych Google" to ADRION 369
   - OAuth 2.0 protocol → MCP servers translation
   - API Scopes → Roo Code security rules patterns
   - Hidden data folders management
   - Practical implementation scenarios

### 🔧 Configuration Files

- **[oauth_config.ini](oauth_config.ini)** - Server-specific scope & token settings
  - All 6 MCP servers (Genesis, Guardian, Healer, Vortex, Oracle, Router)
  - Token expiration & rotation margin
  - Encryption algorithms & storage backends
  - Audit logging configuration
  - Compliance checklist status

- **[mcp.json](mcp.json)** - MCP server endpoint configurations
  - Server command & argument mappings
  - Environment variable templates
  - Tool configuration (ruff, mypy, pytest, docker)
  - Path mappings for workspace integration

### 🛡️ Security Rules (SEC-008 through SEC-012)

Automated by Roo Code security checks in `roo.rules.json`:

| Rule | Purpose | Guardian Law |
|------|---------|-------------|
| **SEC-008** | OAuth Scope Validation | G7 (Privacy), G8 (Nonmaleficence) |
| **SEC-009** | Missing Token Rotation | G3 (Rhythm), G9 (Sustainability) |
| **SEC-010** | Unencrypted Token Storage | G7 (Privacy) |
| **SEC-011** | Missing Scope Audit Logging | G4 (Causality), G5 (Transparency) |
| **SEC-012** | Application Data Folder Leakage | G5 (Transparency), G7 (Privacy) |

### 📊 OAuth Architecture Summary

- **MCP Servers**: 6 (Genesis, Guardian, Healer, Vortex, Oracle, Router)
- **Scopes per Server**: 1-3 granular, least-privilege only
- **Token Expiry**: 24 hours (12h for sensitive operations)
- **Audit Retention**: 30 days, stored in Genesis Record
- **Encryption**: AES-256-GCM at rest, TLS in transit
- **Guardian Laws**: All 9 enforced (G1-G9)
- **Automated Checks**: Roo Code security-audit profile

## Custom Rules

Enable additional custom analysis rules from:

- `roo.rules.json` - Main rules file
- `config/roo-rules/` - Additional rule files

## Usage

### Running Roo Code Analysis

1. **Full Analysis**: All enabled checks

   ```
   Profile: development (default)
   ```

2. **Production Mode**: Strict analysis

   ```
   Profile: production
   ```

3. **Security Audit**: Deep security scanning
   ```
   Profile: security-audit
   ```

### Configuration Selection

- **Default Profile**: `development` (relaxed, suitable for active development)
- **CI/CD Profile**: `ci-pipeline` (strict, for automated testing)
- **Pre-deployment**: `production` (strict, for release candidates)

## Monitoring and Reporting

- Real-time analysis as you code
- Status in VS Code status bar
- Reports generated in `reports/` directory
- Problem matcher integration for IDE
- Git diff integration
- Terminal output formatting

## Performance Considerations

- Large files (>5MB) are skipped by default
- Analysis cache reduces repeated work
- Parallel analysis for faster checks
- Background analysis prevents UI blocking

## Security & OAuth Configuration

See [mcp-security.md](mcp-security.md) for complete OAuth 2.0 implementation guide:

- **Token Management**: Secure storage, rotation, encryption (SEC-010, SEC-009)
- **Scope Validation**: Granular permissions per MCP server (SEC-008)
- **Audit Logging**: Comprehensive trail of OAuth events (SEC-011)
- **Guardian Laws**: Compliance with 9 fundamental laws (G1-G9)
- **Roo Code Integration**: Automated security checks included
- **Compliance Checklist**: Pre-deployment verification steps

Key related files:

- [`oauth_config.ini`](oauth_config.ini) - Server scope & token config
- [`roo.rules.json`](../roo.rules.json) - Security rules SEC-008-012
- [`mcp.json`](mcp.json) - MCP server configurations

## Next Steps

1. **Review OAuth security guide** in [mcp-security.md](mcp-security.md)
2. **Verify token configuration** in `oauth_config.ini`
3. **Review profiles** in `roo.profiles.json` for your needs
4. **Customize rules** in `roo.rules.json` for project standards
5. **Adjust thresholds** in `.roorc` based on team preferences
6. **Test integration** with your IDE and CI/CD pipeline
7. **Run security analysis**: `roo analyze --profile security-audit`
8. **Monitor reports** in `reports/` directory

## Support

For security or OAuth issues:

1. Check MCP security guide: [mcp-security.md](mcp-security.md)
2. Review OAuth configuration: [`oauth_config.ini`](oauth_config.ini)
3. Check `.roorc` runtime configuration
4. Review analysis profiles in `roo.profiles.json`
5. Verify file patterns in `.roo.json`
6. Check custom security rules in `roo.rules.json` (SEC-008-012)

For general issues:

1. Check `.roorc` configuration
2. Review analysis profiles in `roo.profiles.json`
3. Verify file patterns in `.roo.json`
4. Check custom rules in `roo.rules.json`

---

**Configuration Version**: 1.0
**Created**: 2026-04-08
**Maintainer**: ADRION-369 Master Orchestrator
