# ADRION 369 Setup & Installation Guide

## Prerequisites
- **Ollama**: Download from [ollama.com](https://ollama.com)
- **Python 3.10+**: For Aider
- **Git**: For version control
- **RAM**: 16GB minimum (more for larger models)

---

## 🚀 Step 1: Install Ollama

### Windows
1. Download from `ollama.com`
2. Run the installer
3. Ollama runs as a background service

### Verify Installation
```powershell
ollama --version
```

---

## 🧠 Step 2: Download DeepSeek-Coder Model

### For Powerful Machines (16GB+ RAM)
```bash
ollama run deepseek-coder-v2:16b
```

### For Lighter Systems (8-12GB RAM)
```bash
ollama run deepseek-coder-v2:lite
```

**First run downloads ~20GB** (be patient)

### Check Model
```bash
ollama list
```

---

## 🔧 Step 3: Install & Configure Aider

### Install
```bash
pip install aider-chat
```

### Verify
```bash
aider --version
```

### Create Aider Configuration
Configuration is already in `.aider/config.yml`

---

## 🎯 Step 4: Start the System

### Terminal 1: Start Ollama Server
```bash
ollama serve
# Or if running as service, verify it's up:
curl http://localhost:11434/api/tags
```

### Terminal 2: Start Aider with Local Model
```bash
aider --model openai/deepseek-coder-v2:16b \
       --openai-api-base http://localhost:11434/v1 \
       --openai-api-key ollama
```

Or simply use the config file:
```bash
aider
```
(Aider loads config from `.aider/config.yml` automatically)

---

## 🧬 Step 5: Activate Multi-Persona System

Once Aider is running, invoke personas by prefix:

### Example Session Flow

**Start:**
```
@librarian
Analyze the project history and structure, then give me a 5-minute summary.
```

**Plan:**
```
@sap
Based on the Librarian's analysis, create a plan to improve code quality today.
```

**Validate:**
```
@auditor
Review the proposed changes against our quality standards.
```

**If Crisis:**
```
@sentinel
We have production errors. Deploy immediate fixes.
```

**Design Review:**
```
@architect
Is this design change aligned with our system principles?
```

**Optimize:**
```
@healer
Run a background optimization cycle on technical debt.
```

---

## 🧪 Test the Setup

Run this command to verify everything works:

```bash
aider "Analyze the current project structure and tell me which files have the most complexity."
```

Expected response: Librarian + Auditor analysis of your codebase.

---

## 🔒 Security & Privacy (Law 7)

✅ **What stays local:**
- All model inference
- All code and project files
- All analysis and logs

❌ **What never leaves:**
- Source code
- Credentials
- Personal data
- Session history

Verify no external calls:
```bash
# Monitor network requests
netstat -an | findstr :11434
# Should only show localhost traffic
```

---

## 📊 Performance Tuning

### If Ollama is slow:
1. Check RAM: `Get-WmiObject -Class Win32_PhysicalMemory`
2. Check GPU: `nvidia-smi` (if NVIDIA)
3. Reduce model size:
   ```bash
   ollama run deepseek-coder-v2:7b
   ```

### If Aider is slow:
1. Reduce context size in `.aider/config.yml`:
   ```yaml
   context-limit: 8000  # was 16000
   ```
2. Disable streaming:
   ```yaml
   stream: false
   ```

---

## 🐛 Troubleshooting

### Error: "Can't connect to Ollama"
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
nssm restart Ollama  # Windows service
# Or restart manually
```

### Error: "Model not found"
```bash
# Download the model
ollama pull deepseek-coder-v2:16b

# List available models
ollama list
```

### Error: "Out of memory"
```bash
# Use smaller model
ollama run deepseek-coder-v2:lite
```

### Aider not loading config
```bash
# Check config validity
cat .aider/config.yml

# Test with explicit config
aider --config .aider/config.yml
```

---

## 📈 Next Steps

1. **Create a project workspace** in any directory
2. **Initialize git**: `git init`
3. **Run Aider** in that directory
4. **Invoke the six personas** to analyze and optimize

---

## 🔗 Resources

- **Ollama**: https://ollama.com
- **Aider**: https://aider.chat
- **DeepSeek Coder**: https://github.com/deepseek-ai/deepseek-coder
- **ADRION 369 Docs**: See `/docs` folder

---

**Last Updated:** March 29, 2026  
**Version:** 1.0
