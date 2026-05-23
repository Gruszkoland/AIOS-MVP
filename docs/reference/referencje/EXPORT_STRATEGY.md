# 📤 Export Analysis & Repository Strategy

**Generated**: 2026-05-14  
**GitHub Org**: Gruszkoland  
**Primary Repo**: <https://github.com/Gruszkoland/adrion-369>

---

## 📊 Projects Inventory

| Project | Location | Type | Status | Recommendation |
|---------|----------|------|--------|-----------------|
| **162 demencje w schemacie 369** | `.1_Projekty/PROJEKTY/162 demencje w schemacie 369/` | Monolith + MCP ecosystem | ✅ Synced (GitHub) | **PUSH to adrion-369** |
| **adrion-369-architecture** | `.1_Projekty/PROJEKTY/adrion-369-architecture/` | Documentation + Design | ⚠️ Local only | **New Repo: `adrion-architecture`** |
| **adrion-deploy** | `.1_Projekty/PROJEKTY/adrion-deploy/` | Kubernetes + Docker configs | ⚠️ Local only | **New Repo: `adrion-deploy`** |
| **Consultacja-Wielomodelowa-AI** | `.1_Projekty/PROJEKTY/Consultacja-Wielomodelowa-AI/` | Multi-model LLM service | ⚠️ Local only | **New Repo: `consultacao-ai`** |
| **embedding-ab-test-framework** | `.1_Projekty/PROJEKTY/embedding-ab-test-framework/` | ML testing framework | ⚠️ Local only | **New Repo: `embedding-ab-test`** |
| **leadgen-comet-pipeline** | `.1_Projekty/PROJEKTY/leadgen-comet-pipeline/` | Lead generation pipeline | ⚠️ Local only | **New Repo: `leadgen-comet`** |
| **Punkt odniesienia** | `.1_Projekty/PROJEKTY/Punkt odniesienia/` | Benchmark/reference project | ⚠️ Local only | **New Repo: `punkt-odniesienia`** |
| **n8n-produkcja** | `.1_Projekty/PROJEKTY/n8n-produkcja/` | n8n workflows + infra | ⚠️ Local only | **New Repo: `n8n-workflows-prod`** |
| **kyc-provider-integration-guide** | `.1_Projekty/PROJEKTY/kyc-provider-integration-guide/` | KYC integration docs | ⚠️ Local only | **New Repo: `kyc-provider-guide`** |
| **Models Offline** | `.1_Projekty/Models Offline/` | Local LLM models (large) | 🟡 Data only | **Skip (local mirrors)** |
| **WSZYSTKIE DOKUMENTY ADRIANA** | `.1_Projekty/WSZYSTKIE DOKUMENTY ADRIANA/` | Archive/docs | 🟡 Archive | **Skip (archived)** |

---

## 🎯 Export Action Plan

### Phase 1: Existing Project (adrion-369)

**Current Status**: ✅ Already synced to GitHub  
**Action**: Git push latest from `PROJEKTY/162 demencje w schemacie 369/`

```bash
cd "C:\Users\adiha\.1_Projekty\PROJEKTY\162 demencje w schemacie 369"
git status
git add -A
git commit -m "feat: consolidate docker, ci-cd automation, agent validation"
git push origin master
```

---

### Phase 2: New GitHub Repositories (8 Repos)

#### 2.1 adrion-architecture

- **Path**: `PROJEKTY/adrion-369-architecture/`
- **Description**: ADRION system architecture, Guardian Laws, decision space (162D)
- **Key Files**: `GUARDIAN_LAWS_CANONICAL.json`, `README.md`, `docs/`
- **Action**: `git init` → GitHub → push
- **Suggested Owner**: Gruszkoland/adrion-architecture

#### 2.2 adrion-deploy

- **Path**: `PROJEKTY/adrion-deploy/`
- **Description**: Kubernetes, Docker Compose, Prometheus/Grafana, Caddy configs
- **Key Files**: `docker-compose.yml`, `Caddyfile`, `prometheus.yml`, `kubernetes/`
- **Action**: `git init` → GitHub → push
- **Suggested Owner**: Gruszkoland/adrion-deploy

#### 2.3 consultacao-ai

- **Path**: `PROJEKTY/Consultacja-Wielomodelowa-AI/`
- **Description**: Multi-model LLM consultation system (Claude, GPT, local Ollama)
- **Key Files**: `src/`, `Dockerfile`, `requirements.txt`, `README.md`
- **Action**: `git init` → GitHub → push
- **Suggested Owner**: Gruszkoland/consultacao-ai

#### 2.4 embedding-ab-test

- **Path**: `PROJEKTY/embedding-ab-test-framework/`
- **Description**: AB testing framework for embeddings (used by claim_type_classifier)
- **Key Files**: `src/`, `tests/`, `pyproject.toml`, `README.md`
- **Action**: `git init` → GitHub → push
- **Suggested Owner**: Gruszkoland/embedding-ab-test

#### 2.5 leadgen-comet

- **Path**: `PROJEKTY/leadgen-comet-pipeline/`
- **Description**: Lead generation pipeline with async agents & webhooks
- **Key Files**: `agents/`, `engine/`, `config/`, `n8n_workflows/`
- **Action**: `git init` → GitHub → push
- **Suggested Owner**: Gruszkoland/leadgen-comet

#### 2.6 punkt-odniesienia

- **Path**: `PROJEKTY/Punkt odniesienia/`
- **Description**: Benchmark/reference implementation for core ADRION patterns
- **Key Files**: `src/`, `tests/`, `README.md`
- **Action**: `git init` → GitHub → push
- **Suggested Owner**: Gruszkoland/punkt-odniesienia

#### 2.7 n8n-workflows-prod

- **Path**: `PROJEKTY/n8n-produkcja/`
- **Description**: Production n8n workflows, automation, orchestration
- **Key Files**: `workflows/`, `docker-compose.yml`, `config/`
- **Action**: `git init` → GitHub → push
- **Suggested Owner**: Gruszkoland/n8n-workflows-prod

#### 2.8 kyc-provider-guide

- **Path**: `PROJEKTY/kyc-provider-integration-guide/`
- **Description**: KYC provider integration guide (Sumsub, IDnow, etc.)
- **Key Files**: `docs/`, `examples/`, `README.md`
- **Action**: `git init` → GitHub → push
- **Suggested Owner**: Gruszkoland/kyc-provider-guide

---

## 🚀 Execution Order

```
1. ✅ Push adrion-369 (existing) — 5 min
   └─ git add -A && git commit && git push origin master

2. 🏗️ Create 8 new repos on GitHub (via web or CLI)
   └─ For each: gh repo create Gruszkoland/[repo-name] --public

3. 📦 Initialize & push Phase 2 repos (batch)
   └─ For each in Phase 2:
      cd /path/to/project
      git init
      git add -A
      git commit -m "Initial commit: [description]"
      git remote add origin https://github.com/Gruszkoland/[repo-name].git
      git branch -M master
      git push -u origin master

4. 📌 Update cross-project references
   └─ Update imports, documentation, submodule references
   └─ Create monorepo index in adrion-369 README
```

---

## 📝 GitHub Repository Template (for each new repo)

```markdown
# [Project Name]

> [One-line description]

## Overview
[2-3 paragraph overview]

## Quick Start
\`\`\`bash
pip install -r requirements.txt
python -m pytest
\`\`\`

## Related Projects
- [adrion-369](https://github.com/Gruszkoland/adrion-369) — Main ecosystem
- [adrion-architecture](https://github.com/Gruszkoland/adrion-architecture) — System design
- [adrion-deploy](https://github.com/Gruszkoland/adrion-deploy) — Deployment configs

## License
MIT

## Author
[@Gruszkoland](https://github.com/Gruszkoland)
```

---

## 🔗 Cross-Project Dependencies

| From | To | Type |
|------|----|----|
| adrion-369 | adrion-deploy | Imports (Dockerfile, k8s manifests) |
| adrion-369 | adrion-architecture | References (GUARDIAN_LAWS) |
| embedding-ab-test | adrion-369 | Submodule or import |
| leadgen-comet | adrion-369 | Imports + workflows |
| consultacao-ai | adrion-369 | Imports + models |
| n8n-workflows-prod | adrion-deploy | References (docker-compose) |
| kyc-provider-guide | adrion-369 | Documentation link |
| punkt-odniesienia | adrion-369 | Reference implementation |

**Action**: After pushing all repos, update **README.md** in adrion-369 to include links to all related projects.

---

## 📊 Estimated Export Timeline

| Phase | Task | Time | Priority |
|-------|------|------|----------|
| 1 | Push adrion-369 (existing) | 5 min | 🔴 IMMEDIATE |
| 2 | Create 8 GitHub repos | 10 min | 🟠 URGENT |
| 3 | Init + push 8 repos | 20 min | 🟠 URGENT |
| 4 | Update cross-references | 15 min | 🟡 HIGH |
| 5 | Test imports & docs | 10 min | 🟡 HIGH |
| **TOTAL** | | **~60 min** | |

---

## ✅ Pre-Export Checklist

- [ ] All projects have `.gitignore` (copy from adrion-369 if missing)
- [ ] Sensitive data (API keys, tokens) removed or in `.env.example`
- [ ] README.md present in each project root
- [ ] LICENSE file present (recommend MIT for all)
- [ ] requirements.txt or pyproject.toml present
- [ ] GitHub token active (for pushing)
- [ ] No merge conflicts in working trees

---

## 🎯 Success Criteria

✅ All 9 projects pushed to GitHub  
✅ All repos public and browsable  
✅ Cross-project links work  
✅ CI/CD workflows trigger on first push  
✅ Documentation accessible  

---

**Next Action**: Approve plan → Execute Phase 1 & 2 → Report results
