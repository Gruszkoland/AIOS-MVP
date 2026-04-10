# 🚀 ADRION 369 Dashboard - Quick Start

## ⚡ Super Szybko (30 sekund)

### Windows
```powershell
cd "C:\Users\adiha\162 demencje w schemacie 369"
.\start-dashboard.bat
```

### macOS/Linux
```bash
cd ~/your-workspace
bash start-dashboard.sh
```

Otwórz przeglądarkę: **http://localhost:8000**

---

## 🔧 Wymagania

- **Python 3.6+** (install from https://python.org if needed)
- **Ollama** (download from https://ollama.ai)
- **Modern Browser** (Chrome, Firefox, Safari, Edge)

---

## 📋 Workflow

### Terminal 1: Start Ollama
```bash
ollama serve
# Będzie słuchać na localhost:11434
```

### Terminal 2: Start Dashboard
```bash
# Windows
.\start-dashboard.bat

# macOS/Linux
bash start-dashboard.sh
```

### Terminal 3: Start Aider
```bash
aider --model openai/deepseek-coder-v2:16b --openai-api-base http://localhost:11434/v1
```

---

## ✅ Then

1. **Dashboard będzie dostępny**: http://localhost:8000
2. **Will show**:
   - ✅ Ollama status (Online/Offline)
   - ✅ All 7 personas with Trinity scores
   - ✅ Threat monitoring (12 vectors)
   - ✅ LinkedIn publishing status
   - ✅ Genesis Record logs (live)

3. **Use Quick Controls buttons** to invoke personas or view instructions

---

## 🐛 Troubleshooting

### "Address already in use" on port 8000
```bash
# Use different port
python server.py --port 8001
# Then open http://localhost:8001
```

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Ollama still shows offline"
- Make sure `ollama serve` is running in another terminal
- Check: `curl http://localhost:11434/api/tags`

### Dashboard doesn't load
- Refresh browser (Ctrl+R or Cmd+R)
- Check browser console (F12) for errors
- Verify Python server is running on terminal

---

## 📱 Next Steps

1. ✅ Open http://localhost:8000 in browser
2. ✅ Click "🚀 Start Ollama"
3. ✅ Follow the instructions
4. ✅ Click "🤖 Connect Aider" 
5. ✅ Start using personas with @ commands
6. ✅ Changes auto-publish to LinkedIn when Trinity ≥ 0.75

---

**Dashboard provides**:
- 📊 Real-time system monitoring
- 👥 Persona status tracking
- 🛡️ Threat vector detection
- 📱 LinkedIn publishing pipeline
- 📋 Genesis Record logs
- ⚙️ Quick action buttons

Enjoy! 🎯

