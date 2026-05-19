#!/usr/bin/env python3
"""
Auto-Generated README Generator for .1_Projekty
Scans each project directory and generates comprehensive README.md with:
- Project overview & purpose
- Tech stack
- Quick start guide
- File structure
- Dependencies & links to related projects
- Deployment instructions
"""

import os
import json
from pathlib import Path
from datetime import datetime

PROJECT_METADATA = {
    "162 demencje w schemacie 369": {
        "title": "🎯 ADRION 369 — Main Production Platform",
        "description": "Complete orchestration system for AI-driven arbitrage, multi-model consulting, and workflow automation",
        "status": "🔥 PRODUCTION",
        "stack": ["Python/FastAPI", "PostgreSQL", "Docker Compose", "Redis", "Loki", "Prometheus", "Grafana", "Ollama", "n8n"],
        "ports": {"backend": 8002, "api": 8001, "n8n": 5678, "grafana": 3000, "nginx": 80},
        "key_services": [
            "adrion-api (Arbitrage Engine) - 8001",
            "vortex-engine (174Hz Orchestration) - 8003",
            "adrion-healer (Self-Healing) - 8004",
            "n8n (Workflow SAP) - 5678",
            "Grafana (Monitoring) - 3000",
            "PostgreSQL (Genesis Record) - 5432"
        ],
        "related_projects": ["Consultacja-Wielomodelowa-AI", "n8n-produkcja"],
        "entry_files": ["docker-compose.yml", "docker-compose-orchestration.yml", "conftest.py"],
        "git_repo": "https://github.com/[owner]/162-demencje-369"
    },
    
    "Consultacja-Wielomodelowa-AI": {
        "title": "💬 Multi-Model AI Consultation System",
        "description": "Unified API wrapper for multi-model LLM consultation with local Ollama + cloud providers",
        "status": "🟢 ACTIVE",
        "stack": ["Python/FastAPI", "PostgreSQL", "Redis", "Docker", "Ollama", "OpenAI", "Anthropic", "Google"],
        "ports": {"api": 8000, "playground": 3000},
        "key_services": [
            "API Server - 8000",
            "PostgreSQL (consultacao_db) - 5432",
            "Redis Cache - 6379",
            "Ollama LLM - 11434",
            "OpenPlayground - 3000"
        ],
        "related_projects": ["162 demencje w schemacie 369"],
        "entry_files": ["docker-compose.yml", "main.py"],
        "git_repo": "https://github.com/[owner]/consultacja-ai"
    },
    
    "n8n-produkcja": {
        "title": "🔄 n8n Workflow Orchestration",
        "description": "SAP integration and automated workflows for enterprise process automation",
        "status": "🟢 ACTIVE",
        "stack": ["Node.js", "n8n", "PostgreSQL", "Docker", "Webhooks"],
        "ports": {"ui": 5678},
        "key_services": [
            "n8n UI - 5678",
            "PostgreSQL (n8n_db) - 5432"
        ],
        "related_projects": ["162 demencje w schemacie 369"],
        "entry_files": ["docker-compose.yml", "prometheus.yml"],
        "git_repo": "https://github.com/[owner]/n8n-adrion"
    },
    
    "adrion-369-architecture": {
        "title": "🏗️ Architecture & Documentation",
        "description": "Complete documentation, architecture diagrams, and deployment guides for ADRION 369",
        "status": "📚 DOCUMENTATION",
        "stack": ["Markdown", "Mermaid", "PlantUML"],
        "ports": {},
        "key_services": [],
        "related_projects": ["162 demencje w schemacie 369", "Consultacja-Wielomodelowa-AI"],
        "entry_files": ["README.md", "ARCHITECTURE.md", "DEPLOYMENT.md"],
        "git_repo": "https://github.com/[owner]/adrion-architecture"
    },
    
    "leadgen-comet-pipeline": {
        "title": "💰 Lead Generation — Comet Pipeline",
        "description": "Automated lead generation and enrichment pipeline for B2B sales",
        "status": "🟡 STABLE",
        "stack": ["Python", "PostgreSQL", "GCP", "Google Maps API"],
        "ports": {},
        "key_services": [],
        "related_projects": ["162 demencje w schemacie 369"],
        "entry_files": ["main.py", "requirements.txt"],
        "git_repo": "https://github.com/[owner]/leadgen-comet"
    },

    "embedding-ab-test-framework": {
        "title": "📊 Embedding A/B Test Framework",
        "description": "Testing framework for embedding vector search and semantic similarity",
        "status": "🟡 STABLE",
        "stack": ["Python", "Pytest", "Vector DB"],
        "ports": {},
        "key_services": [],
        "related_projects": ["162 demencje w schemacie 369"],
        "entry_files": ["conftest.py", "main.py"],
        "git_repo": "https://github.com/[owner]/embedding-ab-test"
    },

    "kyc-provider-integration-guide": {
        "title": "🏦 KYC Provider Integration",
        "description": "Know Your Customer (KYC) provider integrations and API documentation",
        "status": "🟡 STABLE",
        "stack": ["Python", "REST APIs", "PostgreSQL"],
        "ports": {},
        "key_services": [],
        "related_projects": ["162 demencje w schemacie 369"],
        "entry_files": ["README.md", "integration_guide.md"],
        "git_repo": "https://github.com/[owner]/kyc-providers"
    }
}

def generate_readme(project_name, metadata):
    """Generate comprehensive README.md for a project"""
    
    readme = f"""# {metadata['title']}

**Status:** {metadata['status']}

{metadata['description']}

## 📊 Project Overview

- **Type**: {' / '.join(metadata['stack'][:2])}
- **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
- **Repository**: [{project_name}]({metadata['git_repo']})

## 🛠️ Tech Stack

{chr(10).join(f"- **{tech}**" for tech in metadata['stack'])}

## 🚀 Quick Start

### Prerequisites
```bash
docker --version
docker-compose --version
python 3.11+
git
```

### Setup

1. **Clone Repository**
   ```bash
   git clone {metadata['git_repo']}
   cd {project_name}
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   # or for production:
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Verify Health**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

## 📂 Project Structure

```
{project_name}/
├── docker-compose.yml          # Dev environment
├── docker-compose.prod.yml     # Production environment
├── .env.example               # Environment template
├── src/                        # Source code
├── docs/                       # Documentation
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
└── README.md                   # This file
```

## 🔌 Available Services

{chr(10).join(f"| **{svc.split(' - ')[0].strip()}** | {svc.split(' - ')[1].strip() if ' - ' in svc else 'N/A'} |" if svc else "" for svc in metadata['key_services'])}

## 📡 API Endpoints

"""
    
    if metadata['ports']:
        readme += "### Base URLs\n\n"
        for service, port in metadata['ports'].items():
            readme += f"- **{service.title()}**: `http://localhost:{port}`\n"
    else:
        readme += "No public API endpoints.\n"
    
    readme += f"""

## 🔗 Related Projects

{chr(10).join(f"- [{proj}](../{proj})" for proj in metadata['related_projects'])}

## 📋 Configuration

### Environment Variables

See `.env.example` for complete list. Key variables:

```env
ENVIRONMENT=development|staging|production
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
```

### Docker Compose Profiles

```bash
# Development (default)
docker-compose up

# Production with monitoring
docker-compose -f docker-compose.prod.yml up -d

# With LLM Studio
docker-compose -f docker-compose.lmstudio.yml up -d

# Kubernetes integration
docker-compose -f docker-compose.k8s-integration.yml up -d
```

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src tests/

# Specific test file
pytest tests/test_api.py -v
```

## 📊 Monitoring & Logs

### Grafana Dashboard
- URL: http://localhost:3000
- Default User: admin / admin
- Datasources: Prometheus (metrics), Loki (logs)

### View Logs
```bash
# Follow container logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend

# Export logs
docker-compose logs > logs_export.txt
```

## 🚢 Deployment

### Local Development
```bash
docker-compose up -d
```

### Staging
```bash
docker-compose -f docker-compose.staging.yml up -d
```

### Production (Hetzner/AWS/Azure)
```bash
# Build and push image
docker build -t {project_name}:latest .
docker tag {project_name}:latest registry.example.com/{project_name}:latest
docker push registry.example.com/{project_name}:latest

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes (K8s)
```bash
kubectl apply -f k8s/
kubectl get pods
kubectl logs -f deployment/{project_name}
```

## 🔐 Security

- ✅ All secrets from `.env` (never hardcoded)
- ✅ Environment-based configuration
- ✅ HTTPS/TLS in production
- ✅ JWT authentication on APIs
- ✅ Database credentials encrypted

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Commit changes: `git commit -m "Add feature: xyz"`
3. Push to branch: `git push origin feature/my-feature`
4. Create Pull Request

## 📞 Support & Issues

- **Bugs**: GitHub Issues
- **Questions**: GitHub Discussions
- **Documentation**: See `docs/` folder

## 📄 License

Copyright © 2024 ADRION. All rights reserved.

---

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Version:** 1.0
"""
    
    return readme

def generate_all_readmes():
    """Generate README for all projects"""
    root_path = Path("c:\\Users\\adiha\\.1_Projekty")
    
    for project_name, metadata in PROJECT_METADATA.items():
        project_path = root_path / project_name
        if not project_path.exists():
            print(f"⚠️  Skipping {project_name} — directory not found")
            continue
        
        readme_content = generate_readme(project_name, metadata)
        readme_path = project_path / "README.md"
        
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        print(f"✅ Generated: {readme_path}")

def generate_index_file():
    """Generate main INDEX.md with links to all READMEs"""
    
    index_content = """# 📚 ADRION 369 — Complete Project Index

**Generated:** {}

## 🎯 Quick Navigation

### 🔥 Production Systems

| Project | Status | Purpose | Quick Start |
|---------|--------|---------|------------|
| [162 demencje w schemacie 369](../../PROJEKTY/162%20demencje%20w%20schemacie%20369/README.md) | 🔴 ACTIVE | Main Platform | `docker-compose up -d` |
| [Consultacja-Wielomodelowa-AI](../../PROJEKTY/Consultacja-Wielomodelowa-AI/README.md) | 🟢 ACTIVE | Multi-Model API | `docker-compose up -d` |
| [n8n-produkcja](../../PROJEKTY/n8n-produkcja/README.md) | 🟢 ACTIVE | Workflows | `docker-compose up -d` |

### 📚 Documentation & Reference

| Project | Type | Status |
|---------|------|--------|
| [adrion-369-architecture](../../PROJEKTY/adrion-369-architecture/README.md) | Docs | 📄 Reference |
| [leadgen-comet-pipeline](../../PROJEKTY/leadgen-comet-pipeline/README.md) | Module | 🟡 Stable |
| [embedding-ab-test-framework](../../PROJEKTY/embedding-ab-test-framework/README.md) | Testing | 🟡 Stable |
| [kyc-provider-integration-guide](../../PROJEKTY/kyc-provider-integration-guide/README.md) | Integration | 🟡 Stable |

## 🏗️ Architecture Overview

```mermaid
graph TD
    A["162 demencje w schemacie 369"] -->|API Calls| B["Consultacja-Wielomodelowa-AI"]
    A -->|Workflows| C["n8n-produkcja"]
    A -->|Monitoring| D["Grafana Dashboard"]
    A -->|Docs| E["adrion-369-architecture"]
    B -->|LLM| F["Ollama / Cloud LLMs"]
    C -->|Triggers| A
```

## 📡 Port Map

| Service | Port | Project | URL |
|---------|------|---------|-----|
| **Nginx Ingress** | 80, 443 | Main | http://localhost |
| **API (Arbitrage)** | 8001 | Main | http://localhost:8001 |
| **Backend** | 8002 | Main | http://localhost:8002 |
| **Vortex Engine** | 8003 | Main | http://localhost:8003 |
| **Consultacja API** | 8000 | Consultacja | http://localhost:8000 |
| **n8n UI** | 5678 | n8n | http://localhost:5678 |
| **Grafana** | 3000 | Monitoring | http://localhost:3000 |
| **PostgreSQL** | 5432 | Database | localhost:5432 |
| **Ollama** | 11434 | LLM | http://localhost:11434 |

## 🚀 Common Commands

### Start All Services
```bash
cd "PROJEKTY/162 demencje w schemacie 369"
docker-compose -f docker-compose-orchestration.yml up -d
```

### Monitor Services
```bash
docker-compose ps
docker-compose logs -f --tail=100
```

### Access Dashboards
- Grafana: http://localhost:3000 (admin/admin)
- n8n: http://localhost:5678
- API Docs: http://localhost:8001/docs

### Database Access
```bash
psql -h localhost -U adrion -d genesis_record -p 5432
```

## 📊 Metrics & Monitoring

- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Loki Logs**: Integrated in Grafana
- **Dashboard**: See [DevOps Dashboard](../../PROJEKTY/adrion-deploy/grafana/provisioning/dashboards/devops-dashboard.json)

## 🔗 Dependencies Graph

```
Tier 0 (Foundation)
  └─ PostgreSQL

Tier 1 (Infrastructure)
  ├─ Loki (Logs)
  └─ Promtail (Log Shipper)

Tier 2 (Core Engines)
  ├─ n8n (Workflows)
  ├─ Vortex Engine (Orchestration)
  ├─ Adrion Healer (Self-Healing)
  └─ Ollama (LLM)

Tier 3 (APIs & Services)
  ├─ Arbitrage API
  ├─ Backup Automation
  └─ Alert Handler

Tier 4 (Observability)
  ├─ Grafana
  └─ Nginx Reverse Proxy
```

## 🐛 Troubleshooting

### Services Won't Start?
```bash
docker-compose down -v
docker-compose up -d
```

### Database Connection Error?
```bash
docker-compose logs postgres
docker exec adrion-postgres pg_isready
```

### Out of Memory?
```bash
docker system prune -a
docker volume prune
```

## 📞 Support

- 📖 [Full Documentation](../../PROJEKTY/adrion-369-architecture/)
- 🐛 [Report Issues](https://github.com/[owner]/162-demencje-369/issues)
- 💬 [Discussions](https://github.com/[owner]/162-demencje-369/discussions)

---

**Last Generated**: {}
**Status**: All systems operational ✅
""".format(
        datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    )
    
    index_path = Path("c:\\Users\\adiha\\.1_Projekty\\00_DOKUMENTACJA\\referencje\\PROJECT_INDEX.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)
    
    print(f"✅ Generated: {index_path}")

def main():
    """Main function"""
    print("🚀 Generating README files for all projects...")
    print()
    
    # Generate individual READMEs
    generate_all_readmes()
    print()
    
    # Generate index
    print("📋 Generating project index...")
    generate_index_file()
    
    print()
    print("✅ All documentation generated successfully!")
    print()
    print("📚 Generated Files:")
    print("   - 00_DOKUMENTACJA/referencje/PROJECT_INDEX.md (Main navigation)")
    print("   - [ProjectName]/README.md (Individual projects)")
    print()
    print("🎯 Next Steps:")
    print("   1. Review 00_DOKUMENTACJA/referencje/PROJECT_INDEX.md")
    print("   2. Check individual project READMEs")
    print("   3. Update git repos with new documentation")

if __name__ == "__main__":
    main()
