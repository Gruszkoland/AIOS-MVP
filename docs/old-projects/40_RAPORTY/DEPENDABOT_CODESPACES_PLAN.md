# 🔧 DEPENDABOT + CODESPACES Setup — Plan Wdrożenia

## Status

✅ **GitHub Topics** — Wszystkie 9 repos mają topics  
✅ **Organization README** — Utworzony (300+ linii z diagramami)  
⏳ **Dependabot + Codespaces** — Przygotowanie do wdrożenia

---

## 📋 Plan Wdrożenia Dependabot

### Krok 1: Dla każdego repo

```bash
# Clone repo
git clone https://github.com/Gruszkoland/{repo}.git
cd {repo}

# Konfiguracja git
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Utwórz .github/dependabot.yml
mkdir -p .github
cat > .github/dependabot.yml << 'EOF'
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "daily"
      time: "02:00"
      timezone: "Europe/Warsaw"
    auto-merge:
      enabled: true
      method: "squash"
      strategy: "auto"
      
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "03:00"
      timezone: "Europe/Warsaw"
      
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "wednesday"
      time: "03:30"
      timezone: "Europe/Warsaw"
EOF

# Commit & push
git add .github/dependabot.yml
git commit -m "⚙️  chore: setup Dependabot for dependency updates"
git push
```

### Repos do konfiguracji (9 total)

- [ ] adrion-369
- [ ] adrion-architecture
- [ ] adrion-deploy
- [ ] consultacao-ai
- [ ] embedding-ab-test
- [ ] leadgen-comet
- [ ] punkt-odniesienia
- [ ] n8n-workflows-prod
- [ ] kyc-provider-guide

---

## 🚀 Plan Wdrożenia Codespaces

### Krok 1: Dla każdego repo

```bash
# W repo
mkdir -p .devcontainer
cat > .devcontainer/devcontainer.json << 'EOF'
{
  "name": "ADRION Development Environment",
  "image": "mcr.microsoft.com/devcontainers/python:1-3.11-bullseye",
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/github-cli:1": {},
    "ghcr.io/devcontainers/features/node:1": {}
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-docker.docker",
        "eamodio.gitlens"
      ]
    }
  },
  "forwardPorts": [8000, 8001, 5000, 3000, 9090],
  "postCreateCommand": "pip install --upgrade pip && pip install -r requirements.txt 2>/dev/null || true"
}
EOF

# Commit & push
git add .devcontainer/devcontainer.json
git commit -m "⚙️  chore: setup GitHub Codespaces devcontainer"
git push
```

### Expected Result

- GitHub Actions: "Create a codespace on {branch}" button appears
- `gh codespace create` command works
- Unified development environment for all 9 repos

---

## 📊 Automated Script (Bash)

```bash
#!/bin/bash

REPOS=(
  "adrion-369"
  "adrion-architecture"
  "adrion-deploy"
  "consultacao-ai"
  "embedding-ab-test"
  "leadgen-comet"
  "punkt-odniesienia"
  "n8n-workflows-prod"
  "kyc-provider-guide"
)

ORG="Gruszkoland"

for repo in "${REPOS[@]}"; do
  echo "📌 Processing $repo..."
  
  TEMP_DIR=$(mktemp -d)
  git clone "https://github.com/$ORG/$repo.git" "$TEMP_DIR/$repo"
  cd "$TEMP_DIR/$repo"
  
  # Setup git
  git config user.name "ADRION Bot"
  git config user.email "bot@adrion.local"
  
  # Dependabot
  mkdir -p .github
  cat > .github/dependabot.yml << 'DEPENDABOT'
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "daily"
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
DEPENDABOT
  
  # Codespaces
  mkdir -p .devcontainer
  cat > .devcontainer/devcontainer.json << 'DEVCONTAINER'
{
  "name": "ADRION Dev",
  "image": "mcr.microsoft.com/devcontainers/python:1-3.11-bullseye",
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/github-cli:1": {}
  }
}
DEVCONTAINER
  
  # Commit & push
  git add .
  git commit -m "⚙️  chore: setup Dependabot and Codespaces"
  git push
  
  cd -
  rm -rf "$TEMP_DIR"
  
  sleep 2  # Rate limiting
done

echo "✅ Done!"
```

---

## 🎯 Next Steps (After Dependabot/Codespaces)

### Phase 2: GitHub Actions Automation

- [ ] Cross-repo sync workflow (adrion-369 → satellite repos)
- [ ] Unified Dependabot dashboard
- [ ] Scheduled health checks

### Phase 3: Docker + Kubernetes

- [ ] Multi-stage Docker builds (7 services)
- [ ] Push to ghcr.io
- [ ] Helm charts (umbrella pattern)
- [ ] K8s manifests

---

## 📌 Validation Checklist

### Dependabot

- [ ] `.github/dependabot.yml` present in all repos
- [ ] GitHub shows "Dependabot" tab in Security section
- [ ] Configured to auto-merge PRs
- [ ] Scheduled correctly (02:00 Warsaw time)

### Codespaces

- [ ] `.devcontainer/devcontainer.json` present in all repos
- [ ] "Create a codespace on main" button available
- [ ] Port forwarding configured (8000, 8001, 5000, 3000, 9090)
- [ ] Python extensions installed in devcontainer

---

## 🚀 Deployment Status

- **Dependabot Setup**: Manual per-repo (9 repos)
- **Codespaces Setup**: Manual per-repo (9 repos)
- **Total Time Estimate**: ~2-3 hours for complete setup
- **Scripting**: Bash/PowerShell script ready for automation

---

**Created**: 2026-05-14  
**Target Environment**: github.com/Gruszkoland  
**Priority**: High (Foundation for Phase 2 & 3)
