# ADRION 369 v2.0 - Final Deployment Checklist

## ??? Pre-Flight Security & Identity
- [ ] Genesis Record verified (local logs directory writable).
- [ ] `.env.adrion` is correctly configured with local secrets.
- [ ] `config/personas.yml` and `config/trinity-weights.yml` represent current system values.
- [ ] Master Protocol ADRION 369 is active in VS Code settings.

## ?? Infrastructure (Docker Stack)
1. **Prepare Workspace:**
   - [ ] Ensure `adrion-swarm/` directory is clean.
   - [ ] Build custom images: `docker-compose -f adrion-swarm/docker-compose.yml build`.
2. **Launch Services:**
   - [ ] Start database and orchestration: `docker-compose -f adrion-swarm/docker-compose.yml up -d postgres n8n`.
   - [ ] Start monitoring stack: `docker-compose -f adrion-swarm/docker-compose.yml up -d loki promtail grafana`.
   - [ ] Launch Vortex Core: `docker-compose -f adrion-swarm/docker-compose.yml up -d vortex-engine`.
3. **Connectivity:**
   - [ ] `vortex-engine` accessible at `http://localhost:1740`.
   - [ ] `n8n` dashboard accessible at `http://localhost:5678`.
   - [ ] `loki` receiving logs from `vortex-engine`.

## ?? AI Engine (Ollama + Aider)
- [ ] Ollama service running on Windows: `ollama serve`.
- [ ] DeepSeek models loaded: `deepseek-coder-v2:16b` (Production) or `deepseek-coder-v2:lite` (Performance).
- [ ] Aider connected to local Ollama via port 11434.
- [ ] Persona agents (`/persona-agents/*.agent.md`) validated for compliance with 9 Guardian Laws.

## ?? Operational Validation (Trinity Check)
- [ ] **Material (ROI):** Stream ingestion (UGC/Resale) returns high-confidence arbitrage signals.
- [ ] **Intellectual (Logic):** Vortex Oracle (Go) latency < 50ms for telemetry ingestion.
- [ ] **Essential (Ethics):** Sentinel/Auditor actively flagging violations in Genesis Record.

## ?? Execution Commands
- Start production stack: `docker-compose -f adrion-swarm/docker-compose.yml up -d`
- Check logs: `docker-compose -f adrion-swarm/docker-compose.yml logs -f`
- Run system health audit: `python scripts/security/audit_system.py`

---
*Status: Production-Ready (Version 2.0.FINAL)*
