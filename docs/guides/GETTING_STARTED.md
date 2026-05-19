# ADRION 369 v4.0 — Getting Started Guide

Przewodnik do uruchomienia i zarządzania pełnym systemem ADRION 369 na Windows 10/11.

## 🎯 Quick Start (5 minut)

### Krok 1: One-Click Setup

```powershell
# Otwórz PowerShell w głównym katalogu projektu
powershell -ExecutionPolicy Bypass -File scripts/install/setup-ADRION.ps1
```

To uruchomi:
✅ Sprawdzenie systemowych wymagań
✅ Pobranie i setup Ollama (local LLM)
✅ Budowanie i uruchamianie Docker stack
✅ Inicjalizacja bazy danych
✅ Instalacja pre-commit hooks
✅ Validation całego systemu

**Czas:** ~2-5 minut (w zależności od szybkości Internetu)

### Krok 2: Otwórz Dashboard

Po zakończeniu setup automatycznie otworzy się dashboard:

```
http://localhost:8003
```

**Login:** API Key: `local-dev-key-123` (wbudowany w nagłówkach)

### Krok 3: Sprawdź Status

```powershell
.\admin.ps1 status
```

Powinieneś zobaczyć:
```
✓ PostgreSQL --- http://localhost:5432 (Database)
✓ n8n --- http://localhost:5678 (Workflows)
✓ Vortex --- http://localhost:1740 (Sentinel)
✓ Arbitrage API --- http://localhost:8001 (Logic)
✓ UAP Backend --- http://localhost:8002 (Admin API)
✓ UAP Dashboard --- http://localhost:8003 (Admin UI)
✓ Ollama --- http://localhost:11434 (LLM)

All services operational ✓
```

---

## 📊 Admin CLI - Wszystkie Komendy

Master CLI tool do zarządzania całym systemem:

```powershell
.\admin.ps1 [command] [subcommand] [options]
```

### Zarządzanie Serwisami

```powershell
# Pokaż status wszystkich serwisów
.\admin.ps1 status

# Uruchom wszystkie serwisy
.\admin.ps1 start

# Zatrzymaj wszystkie serwisy
.\admin.ps1 stop

# Restartuj konkretny serwis
.\admin.ps1 restart postgres        # PostgreSQL
.\admin.ps1 restart n8n             # n8n workflows
.\admin.ps1 restart vortex          # Vortex Sentinel
.\admin.ps1 restart ollama          # Ollama LLM
.\admin.ps1 restart uap             # UAP Admin Panel
```

### Logi i Diagnostyka

```powershell
# Pokaż ostatnie 50 linii logów
.\admin.ps1 logs

# Pokaż 100 linii logów określonego serwisu
.\admin.ps1 logs postgres 100
.\admin.ps1 logs n8n 200

# Monitoruj zdrowie systemu (continuous monitoring)
.\admin.ps1 health monitor          # Pokaż co 30 sekund
.\admin.ps1 health monitor 10       # Pokaż co 10 sekund

# Szybki health check
.\admin.ps1 health check
```

### Operacje na Bazie Danych

```powershell
# Utwórz backup
.\admin.ps1 db backup

# Przywróć z backupu
.\admin.ps1 db restore backup_file.sql.gz

# Uruchom migracje
.\admin.ps1 db migrate 002          # Migrate to version 002
.\admin.ps1 db migrate              # Show current status

# Optymalizuj bazę (VACUUM + ANALYZE + REINDEX)
.\admin.ps1 db optimize
```

### Panel Administracyjny

```powershell
# Otwórz UAP Dashboard w przeglądarce
.\admin.ps1 ui open

# Sprawdź status UAP
.\admin.ps1 ui status
```

### Development & Testing

```powershell
# Uruchom wszystkie testy
.\admin.ps1 dev test

# Uruchom linter
.\admin.ps1 dev lint

# Wyświetl dev logi
.\admin.ps1 dev logs

# ⚠️ FULL RESET (backup najpierw!)
.\admin.ps1 dev reset
```

### Tryb Offline

```powershell
# Włącz tryb offline (wyłącza wszystkie cloud APIs)
.\admin.ps1 offline enable

# Sprawdź status offline mode
.\admin.ps1 offline status
```

### Setup & Pomoc

```powershell
# Uruchom pełny setup (jak na początku)
.\admin.ps1 setup

# Pokaż help z wszystkimi komendami
.\admin.ps1 help
```

---

## 🌐 Web Dashboard (UAP) — 5 Tabs

Otwórz w przeglądarce: **http://localhost:8003**

### Tab 1: Control HQ 🎛️
- **Trinity Scores** - System scoring (Material, Intellectual, Essential)
- **Trust Scores Heatmap** - 9 AI agents with trust levels
- **Guardian Laws Status** - 9 praw zgodności
- **Real-time stats** - Active tasks, logs, agents, avg score

### Tab 2: Agent Delegator 🚀
- **Task Form** - Wpisz zadanie do wykonania
- **Agent Selector** - Choose target agent (AI autopilot)
- **Dry-run Mode** - Preview bez execution
- **Task Execution Log** - Historia submitted tasks

### Tab 3: Genesis Viewer 📚
- **Search & Filter** - Find logs by keyword
- **Date Range Filter** - 1h, 24h, 7d presets
- **Audit Trail** - Wszystkie akcje systemu
- **Export** - JSON/CSV export

### Tab 4: Orchestrator Console 🎛️
- **Crisis Mode** - Ręczna aktywacja w nagłych wypadkach
- **Conflict Resolver** - Resolve disagreements między agentami
- **Rollback Checkpoints** - Create/restore system snapshots
- **Healing Dashboard** - Suggested repairs

### Tab 5: Self-Healing ❤️
- **Healer Suggestions** - Automatic optimization ideas
- **Last 24h Fixes** - Applied repairs history
- **Performance Heatmap** - CPU/RAM/DB metrics

---

## 📁 Important Directories

| Folder | Purpose |
|--------|---------|
| `scripts/install/` | Setup & initialization scripts |
| `scripts/monitoring/` | Health checks & auto-recovery |
| `scripts/maintenance/` | Backups, cleanup, optimization |
| `.aider/logs/` | System logs & audit trail |
| `backups/` | Database backups (7-day retention) |
| `.runtime/` | Runtime files & temporary data |
| `adrion-swarm/` | Docker Compose configuration |
| `uap/` | Web Admin Panel (frontend + backend) |

---

## ⚙️ Configuration Files

### 🔑 Environment Files

```bash
.env                 # Main configuration (git-tracked)
.env.local          # Secrets (git-ignored, pre-commit blocked)
.env.adrion         # Docker-specific config
.env.offline        # Offline-mode configuration
```

### To Switch to Offline Mode:

```powershell
Copy-Item .env.offline .env -Force
.\admin.ps1 restart all
```

### To Add API Keys:

Edit `.env.local` (git-ignored):
```bash
OPENROUTER_API_KEY=your_key
OPENAI_API_KEY=your_key
GOOGLE_API_KEY=your_key
```

---

## 🔄 Daily Operations

### Morning - Verify System

```powershell
# Check all services
.\admin.ps1 status

# Review overnight logs
.\admin.ps1 logs 100
```

### Throughout Day - Continuous Monitoring

```powershell
# Keep health monitor running in background (30sec intervals)
.\admin.ps1 health monitor

# In another terminal, use admin.ps1 normally
```

### Evening - Maintenance

```powershell
# Backup database
.\admin.ps1 db backup

# Optimize database
.\admin.ps1 db optimize

# View backup summary
Get-ChildItem backups/ | Sort-Object LastWriteTime -Descending | Select -First 5
```

### Weekly - Full System Check

```powershell
# Run all tests
.\admin.ps1 dev test

# Check logs for errors
Get-ChildItem .aider/logs/ -Filter "*.log" |
  ForEach-Object { Write-Host "=== $($_.Name) ==="; tail -20 $_ }

# Verify backup integrity
.\admin.ps1 db backup
```

---

## 🚨 Troubleshooting

### Services Won't Start

```powershell
# Check Docker status
docker ps -a

# Check logs for specific service
.\admin.ps1 logs postgres 50

# Restart all
.\admin.ps1 stop
.\admin.ps1 start
.\admin.ps1 status
```

### Ollama Not Responding

```powershell
# Check if running
Get-Process ollama

# Restart
.\admin.ps1 restart ollama

# Verify
curl.exe http://localhost:11434/api/version
```

### Database Connection Issues

```powershell
# Check PostgreSQL container
docker ps | grep postgres

# View PostgreSQL logs
docker logs adrion-db --tail 50

# Restart
.\admin.ps1 restart postgres
```

### Out of Disk Space

```powershell
# Check free space
Get-PSDrive C

# Clean old backups
Remove-Item backups/*_*.sql.gz -OlderThan (Get-Date).AddDays(-7)

# Check Docker volumes
docker system df
docker system prune -a
```

### High Memory Usage

```powershell
# Check Docker resource usage
docker stats

# Reduce Ollama model size (use smaller model)
ollama pull deepseek-coder-v2:7b  # Instead of 16b

# Restart services
.\admin.ps1 stop
.\admin.ps1 start
```

---

## 📝 Logs & Monitoring

### Real-Time Monitoring

```powershell
# Watch services every 30 seconds (Ctrl+C to stop)
.\admin.ps1 health monitor

# Watch specific service logs
docker logs -f adrion-db
docker logs -f adrion-n8n
```

### Log Files

```bash
.aider/logs/             # All system logs
backups/                 # Database backups with timestamps
.runtime/                # Runtime state
```

### Analyze Issues

```powershell
# Last 100 lines of all logs
Get-ChildItem .aider/logs/*.log |
  ForEach-Object { tail -100 $_ } |
  Select-String "ERROR|WARN|FAIL" -C 2
```

---

## 🔐 Security Notes

### API Key Protection
- Default: `local-dev-key-123` (development only)
- Change in `.env` before production use
- Always use HTTPS in production

### Database Credentials
- PostgreSQL user: `adrion`
- Password: `adrion_pass` (development)
- For production, change in `.env.adrion` BEFORE first run

### Pre-commit Hooks
- Automatically blocks:
  - `.env.local` files
  - Stripe API keys
  - Plain-text passwords
- Verify secrets are NOT in `.env` (use `.env.local`)

### Backup Encryption (Optional)
```powershell
# Encrypt sensitive backups
gpg --encrypt --recipient your_email backups/postgres_*.sql.gz
```

---

## 🚀 Production Deployment

When ready for production:

1. **Change Secrets**
   ```powershell
   # Edit .env with real values
   # Edit .env.local with production API keys
   ```

2. **Setup HTTPS**
   ```powershell
   # Configure reverse proxy (nginx/IIS)
   # Install SSL certificate
   ```

3. **Enable Monitoring**
   ```powershell
   .\admin.ps1 health monitor  # Run 24/7
   ```

4. **Setup Backups**
   ```powershell
   # Schedule daily backups via Windows Task Scheduler
   ```

5. **Test Failover**
   ```powershell
   .\admin.ps1 dev reset  # Full reset test
   .\admin.ps1 setup      # Restore from backup
   ```

---

## 📞 Support & Documentation

| Resource | Link |
|----------|------|
| Architecture Docs | `docs/ARCHITECTURE.md` |
| System Laws | `docs/LAWS.md` |
| Troubleshooting | `docs/TROUBLESHOOTING.md` |
| API Reference | `uap/README.md` |
| Docker Setup | `adrion-swarm/README.md` |
| Genesis Record | `.aider/logs/` |

---

## ✅ Checklist - First Run

- [ ] Run `setup-ADRION.ps1`
- [ ] Verify all services with `.\admin.ps1 status`
- [ ] Open web dashboard at `http://localhost:8003`
- [ ] Create first task in Agent Delegator
- [ ] Check backup created in `backups/`
- [ ] Review logs in Genesis Viewer
- [ ] Test offline mode: `.\admin.ps1 offline enable`
- [ ] Read `docs/ARCHITECTURE.md` for deep dive

---

## 🎊 You're Ready!

Your complete ADRION 369 system is now:
- ✅ Fully automated
- ✅ Locally hosted
- ✅ Continuously monitored
- ✅ Backed up automatically
- ✅ Web + CLI controlled
- ✅ Offline-capable

**Start with:** `.\admin.ps1 ui open`

Enjoy your autonomous AI system! 🚀
