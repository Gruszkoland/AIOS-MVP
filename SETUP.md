# ADRION 369 Setup Instructions

## ⚡ Quick Start

### 1️⃣ Install Ollama

**Windows:**
- Download from: https://ollama.ai/download
- Run installer
- Add to PATH: `C:\Users\YourUsername\AppData\Local\Programs\Ollama`

**macOS:**
```bash
brew install ollama
```

**Linux (Ubuntu/Debian):**
```bash
curl https://ollama.ai/install.sh | sh
```

### 2️⃣ Run Setup Script

**Windows:**
```powershell
cd "C:\Users\adiha\162 demencje w schemacie 369"
.\setup.bat
```

**macOS/Linux:**
```bash
cd ~/your-workspace
bash setup.sh
```

### 3️⃣ Manual Setup (if script fails)

```bash
# 1. Download model
ollama pull deepseek-coder-v2:16b

# 2. Start Ollama server (keep this terminal open)
ollama serve

# 3. In a NEW terminal window, start Aider
aider --model openai/deepseek-coder-v2:16b --openai-api-base http://localhost:11434/v1

# 4. Open Dashboard
# Windows: Open file:///C:/Users/adiha/162%20demencje%20w%20schemacie%20369/dashboard/index.html in browser
# macOS/Linux: open file:///path/to/dashboard/index.html
```

---

## 📊 Using the Dashboard

### Open Dashboard
- **VS Code**: Right-click `dashboard/index.html` → "Open with Live Server"
- **Browser**: Open `file:///C:/Users/adiha/162%20demencje%20w%20schemacie%20369/dashboard/index.html`
- **Python Server**: `python -m http.server 8000` then visit `localhost:8000/dashboard`

### Dashboard Features
- ✅ **System Status**: Ollama, Aider, Genesis Record
- 👥 **Persona Monitoring**: Trinity scores, EBDI states
- 🛡️ **Threat Detection**: 12 attack vectors monitoring
- 📱 **LinkedIn Status**: Publishing queue, metrics
- 📋 **Genesis Record**: Activity logs, decisions

### Quick Commands (in Aider)
```
@librarian analyze          # Analyze git history
@sap plan                   # Plan session
@auditor review             # Review code quality
@sentinel monitor           # Monitor for errors
@architect review [file]    # Design review
@healer optimize            # Optimize code
@amplifier publish          # Publish to LinkedIn
```

---

## 🚨 Troubleshooting

### "Ollama not found"
- Check PATH: `echo $PATH` (macOS/Linux) or `echo %PATH%` (Windows)
- Add Ollama to PATH manually if needed

### "Model not found"
```bash
ollama pull deepseek-coder-v2:16b
```

### "Connection refused localhost:11434"
- Make sure `ollama serve` is running in another terminal
- Check: `curl http://localhost:11434/api/health`

### Aider won't connect
```bash
# Start with verbose logging
aider --model openai/deepseek-coder-v2:16b --openai-api-base http://localhost:11434/v1 -v
```

---

## 📝 Logs Location

```
.aider/logs/
├── session.log              # Aider session logs
├── audit_trail.log          # Genesis Record audit
├── linkedin_publish.log     # LinkedIn publishing logs
└── linkedin_metrics.json    # Publishing metrics
```

---

## ✅ Verify Installation

```bash
# Check Ollama
ollama list
ollama serve --help

# Check Aider  
aider --version

# Check model
curl http://localhost:11434/api/tags

# Test connection
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "deepseek-coder-v2:16b",
  "prompt": "Hello",
  "stream": false
}'
```

Expected response: `{"response":"...","done":true}`

---

## 🎯 Next Steps

1. ✅ Run setup script
2. ✅ Verify Ollama is serving on localhost:11434
3. ✅ Open Dashboard
4. ✅ Start Aider
5. ✅ Run `@librarian analyze` in Aider
6. ✅ Push changes to GitHub
7. ✅ AMPLIFIER automatically publishes to LinkedIn!

---

**Need help?** Check [docs/LINKEDIN-INTEGRATION.md](../docs/LINKEDIN-INTEGRATION.md) or [.github/copilot-instructions.md](../.github/copilot-instructions.md)

