# ADRION 369 - Ollama Installation Guide

## Windows Installation

### Option 1: Direct Download (Recommended)

1. **Download Ollama Installer**
   - Go to: https://ollama.ai/download
   - Click "Download for Windows"
   - Run the installer: `OllamaSetup.exe`

2. **Verify Installation**
   ```powershell
   ollama --version
   ```

3. **If command not found:**
   - Go to: `C:\Users\YourUsername\AppData\Local\Programs\Ollama`
   - Copy full path
   - Add to PATH:
     - Right-click "This PC" → Properties → Advanced System Settings
     - Environment Variables → New (User Variable)
     - Name: `PATH`
     - Value: `C:\Users\YourUsername\AppData\Local\Programs\Ollama`

### Option 2: Chocolatey
```powershell
choco install ollama
```

### Option 3: Docker (if Ollama crashes)
```powershell
docker run -d --name ollama -p 11434:11434 ollama/ollama
ollama pull deepseek-coder-v2:16b
```

---

## Next Steps

### 1. Download Model
```powershell
ollama pull deepseek-coder-v2:16b
```
⏱️ *This will take 5-10 minutes (9GB download)*

### 2. Start Ollama Server
```powershell
# Terminal 1: Start Ollama
ollama serve

# You should see:
# [GIN] listening on 127.0.0.1:11434
```

### 3. Test Connection
```powershell
# Terminal 2: Test Ollama
$response = curl -X POST http://localhost:11434/api/generate -d '{"model":"deepseek-coder-v2:16b","prompt":"test"}' 
$response
```

### 4. Install Aider
```powershell
pip install aider-chat
```

### 5. Connect Aider to Ollama
```powershell
aider --model openai/deepseek-coder-v2:16b --openai-api-base http://localhost:11434/v1
```

### 6. Open Dashboard
- URL: `file:///C:/Users/adiha/162%20demencje%20w%20schemacie%20369/dashboard/index.html`
- Or in VS Code: Right-click `dashboard/index.html` → "Open with Live Server"

---

## Common Issues

### Error: "Connection refused"
✅ Make sure `ollama serve` is running in first terminal

### Error: "Model not found"
```powershell
ollama pull deepseek-coder-v2:16b
```

### Slow performance
- Try lite model: `ollama pull deepseek-coder-v2:lite`
- Or use GPU acceleration (NVIDIA/AMD)

### Out of memory
- Stop other programs
- Reduce model size to `lite` version
- Allocate more RAM to Ollama

---

## Verification Checklist

- [ ] Ollama installed (`ollama --version`)
- [ ] Model downloaded (`ollama list`)
- [ ] Server running (`ollama serve`)
- [ ] Connection works (`curl http://localhost:11434/api/tags`)
- [ ] Aider installed (`aider --version`)
- [ ] Aider connects to Ollama
- [ ] Dashboard opens in browser

---

Once complete, you can:
```powershell
# In Aider terminal:
@librarian analyze
@sap plan
@auditor review
@amplifier publish
```

Dashboard will track everything! 📊

