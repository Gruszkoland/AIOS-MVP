# ADRION 369 Quick-Start Guide

## ⚡ 5-Minute Setup

### Step 1: Install Prerequisites (One-time)
```bash
# Download Ollama from ollama.com (Windows installer)
# Then install Aider
pip install aider-chat
```

### Step 2: Terminal 1 - Start Ollama
```bash
# Start Ollama (runs as service on Windows, usually auto-starts)
ollama serve

# Or if already running:
curl http://localhost:11434/api/tags  # Just verify it's up
```

### Step 3: Terminal 2 - Start Your Project
```bash
# Navigate to your project directory
cd your-project-folder

# Start Aider (uses .aider/config.yml automatically)
aider
```

### Step 4: Invoke Your First Persona

```
@librarian
Give me a 2-minute summary of this project's recent history.
```

**Done!** You now have your 6-persona AI system running locally.

---

## 🎯 Your First Session

### Typical Workflow (30 minutes)

```bash
# 1. Librarian - Understand the landscape
@librarian
Analyze this project. What are the main modules?
What was changed recently?

# 2. SAP - Plan the work
@sap
Based on that analysis, what's the priority for today?
Create a prioritized action plan.

# 3. Architect - Design review (if needed)
@architect
Is this architecture aligned with good practices?
What patterns should we follow?

# 4. Implementation - Make changes
# (Aider handles this with your guidance)

# 5. Auditor - Quality check
@auditor
Review these changes for quality, security, regressions.

# 6. Sentinel - Monitor for issues
@sentinel
Check for any runtime errors or performance issues.

# 7. Healer - Optimize (background)
@healer
Run an optimization cycle to reduce technical debt.
```

---

## 📋 Persona Quick Reference

| Persona | Use When | Command |
|---------|----------|---------|
| **LIBRARIAN** | Need to understand the codebase | `@librarian` |
| **SAP** | Creating an action plan | `@sap` |
| **AUDITOR** | Validating code quality | `@auditor` |
| **SENTINEL** | Responding to errors/crisis | `@sentinel` |
| **ARCHITECT** | Designing new systems | `@architect` |
| **HEALER** | Improving code quality | `@healer` |

---

## 🚨 Crisis Mode

If production is down:

```bash
@sentinel
CRITICAL ALERT: [describe the problem]
We need immediate fixes. What's the issue?

# Sentinel will:
# 1. Identify root cause (< 10 seconds)
# 2. Deploy hotfix (< 30 seconds)
# 3. Verify stability (< 1 minute)
```

---

## 🛠️ VS Code Tasks

Open Command Palette (`Ctrl+Shift+P`) and run:

- **Tasks: Run Task** → Select from:
  - 🚀 Start Ollama Server
  - 🤖 Start Aider (Librarian Mode)
  - 📊 Show Ollama Models
  - 📥 Download DeepSeek Model
  - ✅ Check System Status
  - 📋 View Session Logs

Or use **Terminal** → **Run Task** directly.

---

## 📊 Monitoring & Logs

### Check Status
```bash
# View current Ollama models
ollama list

# Test Ollama connection
curl http://localhost:11434/api/tags

# View recent session logs
Get-Content -Tail 50 .aider/logs/session.log
```

### Understanding Log Entries
Each persona interaction is logged with:
- Timestamp
- Persona name
- Input query
- Key findings
- Decisions made

```
[2026-03-29 14:30:15] LIBRARIAN: Analyzed recent commits
  → 5 commits in last 24h
  → Focus: Payment module refactoring
  → Risk level: LOW
  
[2026-03-29 14:32:42] SAP: Created action plan
  → 4 tasks prioritized
  → Total effort: 6 hours
  → Critical item: Dependency upgrade
```

---

## 🔧 Common Scenarios

### Scenario 1: Add a New Feature
```
@librarian → Understand current architecture
@architect → Design the new feature
@sap → Prioritize implementation
[Implement changes]
@auditor → Validate quality
@sentinel → Monitor for issues
```

### Scenario 2: Performance Issue
```
@sentinel → Identify bottleneck
[Deploy hotfix]
@healer → Root cause analysis & permanent fix
@auditor → Validate improvements
```

### Scenario 3: Code Review
```
@auditor → Check code quality
@architect → Design alignment
@sentinel → Runtime correctness
```

### Scenario 4: Maintenance
```
@healer → Identify technical debt
[Refactor & improve]
@auditor → Validate changes
@sentinel → Monitor performance
```

---

## 📚 When You Need More Info

- **Setup Issues**: See [docs/INSTALL.md](docs/INSTALL.md)
- **Deep Dive Architecture**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **The 9 Governing Laws**: See [docs/LAWS.md](docs/LAWS.md)
- **Detailed Workflows**: See [docs/WORKFLOW.md](docs/WORKFLOW.md)
- **Troubleshooting**: See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## 🎓 Learning Path

1. ✅ **Now**: Get Ollama + Aider running
2. ✅ **Next (5 min)**: Try `@librarian` command
3. ✅ **Then (10 min)**: Try `@sap` to get a plan
4. ✅ **Then (15 min)**: Let Aider implement a simple change
5. ✅ **Then (10 min)**: Use `@auditor` to validate
6. 📖 **Read**: [docs/LAWS.md](docs/LAWS.md) - understand the philosophy
7. 🎯 **Customize**: Adjust `.aider/config.yml` for your needs
8. 🔄 **Integrate**: Use personas in your daily workflow

---

## 💡 Pro Tips

1. **Be Specific**: `@librarian` + detailed question gets better results
2. **Use Context**: Tell personas what you're working on
3. **Read Rationale**: Personas explain their reasoning; learn from it
4. **Trust the System**: The 6-persona workflow usually finds issues humans miss
5. **Review Logs**: Session logs show all decisions (Genesis Record)

---

## ❓ Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| "Can't connect to Ollama" | [Troubleshooting](docs/TROUBLESHOOTING.md#issue-ollama-connection-failed) |
| Model not found | [Troubleshooting](docs/TROUBLESHOOTING.md#issue-model-not-found) |
| Out of memory | [Troubleshooting](docs/TROUBLESHOOTING.md#issue-out-of-memory-errors) |
| Slow responses | [Troubleshooting](docs/TROUBLESHOOTING.md#issue-aider-connection-slow-or-hanging) |
| Other issues | [Full Troubleshooting Guide](docs/TROUBLESHOOTING.md) |

---

## 🚀 Next Steps

1. **Start Ollama** in Terminal 1
2. **Start Aider** in Terminal 2
3. **Try a query**: `@librarian` + your question
4. **Explore**: Try each persona with your codebase
5. **Customize**: Adjust `.aider/config.yml` for your workflow
6. **Integrate**: Make this your daily development companion

---

**Welcome to ADRION 369!**  
Your local, private, multi-persona AI coding system is ready.

🎯 No cloud. No data leaving your machine. Just pure local AI power.

---

**Quick Links:**
- 📖 [Full README](README.md)
- 🏗️ [Architecture](docs/ARCHITECTURE.md)
- ⚖️ [The 9 Laws](docs/LAWS.md)
- 📋 [Workflows](docs/WORKFLOW.md)
- 🔧 [Troubleshooting](docs/TROUBLESHOOTING.md)
- 📥 [Installation](docs/INSTALL.md)

