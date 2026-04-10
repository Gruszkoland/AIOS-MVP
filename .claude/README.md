#!/bin/bash

# .claude/README.md - Quick reference for installed agents and skills

## 🤖 AGENTS — Multi-Agent Coordination

### Meta & Orchestration

- **agent-organizer.md** — Multi-agent workflow design, task decomposition
  - Use: `@agent-organizer break down Trinity-Hexagon-Guardians into async tasks`

- **context-manager.md** — Context window optimization across agents
  - Use: `@context-manager optimize conversation for 6 parallel agents`

- **error-coordinator.md** — Graceful error recovery in multi-agent systems
  - Use: `@error-coordinator design fallback strategy for Trinity failure`

### Backend Development

- **api-designer.md** — REST/GraphQL API architecture
  - Use: `@api-designer design POST /trinity-analysis endpoint schema`

- **backend-developer.md** — Server-side implementation patterns
  - Use: `@backend-developer implement Guardian Laws validation service`

- **python-pro.md** — Python optimization & patterns
  - Use: `@python-pro optimize arbitrage/guardian.py performance`

### Quality & Security

- **performance-engineer.md** — Performance tuning & benchmarking
  - Use: `@performance-engineer profile Vortex 174Hz response times`

---

## 💡 SKILLS — Patterns & Best Practices

### Infrastructure & Databases

- **llm-integration/** — Claude + Ollama integration patterns
  - Examples: streaming, function calling, cost optimization

- **postgres-optimization/** — PostgreSQL tuning for genesis_record
  - Examples: indexes, query plans, JSONB, partitioning

- **redis-patterns/** — AI-Binder IPC patterns (zero-copy)
  - Examples: pub/sub, streams, atomic operations

- **monitoring-observability/** — Prometheus + OpenTelemetry setup
  - Examples: custom metrics, dashboards, alerting

### Languages & Frameworks

- **golang-idioms/** — Go best practices for Vortex/internal/
  - Examples: error wrapping, interfaces, concurrency

- **python-best-practices/** — Python patterns for arbitrage/
  - Examples: type hints, testing, optimization

- **docker-best-practices/** — Container orchestration
  - Examples: multi-service setup, resource limits, health checks

### DevOps & Testing

- **devops-automation/** — Infrastructure automation
  - Examples: deployment scripts, service health checks

- **ci-cd-pipelines/** — GitHub Actions workflows
  - Examples: coverage gates (90%+), security scanning

- **microservices-design/** — Service architecture patterns
  - Examples: communication, resilience, monitoring

- **tdd-mastery/** — Test-driven development patterns
  - Examples: red-green TDD, mutation testing, coverage

---

## 🚀 QUICK COMMANDS

```bash
# View all agents
ls -la agents/*/

# View all skills
ls -la skills/

# Read a skill (e.g., LLM integration)
cat skills/llm-integration/SKILL.md | less

# Invoke agent in Claude Code
@agent-organizer <prompt>

# Search skills
grep -r "streaming" skills/
```

---

## 📍 INTEGRATION CHECKPOINTS

- [x] Agents installed: 6 subagents in `.claude/agents/`
- [x] Skills installed: 11 curated skills in `.claude/skills/`
- [ ] Trinity-Hexagon-Guardians multi-agent flow (use: `@agent-organizer`)
- [ ] PostgreSQL indexes for genesis_record (use: `@postgres-optimization`)
- [ ] LLM streaming for Ollama (use: `@llm-integration`)
- [ ] Prometheus metrics for Vortex 174Hz (use: `@monitoring-observability`)
- [ ] CI/CD gate to 90% coverage (use: `@ci-cd-pipelines`)

---

**Created:** 2026-04-10
**Project:** ADRION 369 v1.0
**Status:** ✅ Ready for development
