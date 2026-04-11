# LM Studio Integration — ADRIAN 369 Local LLM Deployment

## 🚀 Overview

**LM Studio** to desktopowa aplikacja do uruchamiania dużych modeli językowych (LLM) lokalnie bez konieczności posiadania klucza API. Perfect do **offline development** i **cost optimization**.

### Backend Priority (Auto-Selection)

System ADRIAN 369 używa automatycznego fallback'u:

```
openrouter (API) → openai (API) → anthropic (API) → lmstudio (local) → ollama (local) → mock
```

## 📦 Installation

### 1. Download LM Studio

**Windows (Recommended)**:

```powershell
# Download from:
https://lmstudio.ai/

# Or via Chocolatey:
choco install lmstudio
```

**macOS**:

```bash
brew install lmstudio
```

**Linux**:

```bash
# Download AppImage from https://lmstudio.ai/
chmod +x ~/LM\ Studio-*.AppImage
~/LM\ Studio-*.AppImage
```

### 2. Launch LM Studio

```powershell
# Windows — LM Studio będzie dostępna w Start Menu
# Default port: http://localhost:1234

# Verify server is running:
curl http://localhost:1234/v1/models
```

### 3. Download a Model

LM Studio UI → **Search Models** → Select one:

**Recommended Models** (dla ADRIAN 369):

- **neural-chat** (13B) — **Best for Arbitrage Analysis** ⭐ (balanced speed/quality)
- **mistral** (7B) — Fast, lightweight
- **openchat** (7B) — Good speed, decent quality
- **llama2** (7B/13B) — Versatile

```
Model Size Reference:
- 7B  = ~4.5 GB VRAM
- 13B = ~8 GB VRAM
- 70B = ~45 GB VRAM (powinna mieć ~80GB RAM)
```

**Example: Download Neural-Chat**

1. Search "neural-chat" in LM Studio UI
2. Click "Download"
3. Configure in `.env.lmstudio`:
   ```env
   LMSTUDIO_MODEL=neural-chat
   ```

### 4. Configure ADRIAN 369

```bash
# Copy config template
copy .env.lmstudio .env.local

# Edit .env.local i ustaw:
LLM_BACKEND=lmstudio
LMSTUDIO_URL=http://localhost:1234
LMSTUDIO_MODEL=neural-chat
```

### 5. Start ADRIAN 369 with LM Studio

```powershell
# Activate Python venv
.\.venv\Scripts\Activate.ps1

# Start Arbitrage Server (uses LM Studio backend)
python arbitrage_server.py

# In another terminal, start Dashboard:
python dashboard/server.py
```

## 🔄 Backend Switching

### Option A: Auto-Detection

```env
LLM_BACKEND=auto
# System automatically uses: lmstudio > ollama > openrouter > mock
```

### Option B: Force Specific Backend

```bash
# Force LM Studio
export LLM_BACKEND=lmstudio

# Force Ollama (local fallback)
export LLM_BACKEND=ollama

# Force OpenRouter (API-based)
export LLM_BACKEND=openrouter

# Force Mock (for testing)
export LLM_BACKEND=mock
```

### Option C: Runtime Override (Python)

```python
from arbitrage.analyzer import analyze_job
from arbitrage.config import get_active_llm_backend

# Check which backend is active
print(get_active_llm_backend())  # Output: lmstudio, ollama, openrouter, etc.

# Analyze a job (uses active backend)
result = analyze_job({
    "id": "job_123",
    "title": "Write SEO Blog Post",
    "platform": "upwork",
    "budget_min": 100,
    "budget_max": 300,
    "description": "Need 5000-word blog on Python performance...",
})

print(f"Backend used: {result['llm_backend']}")
print(f"Score: {result['score']}/10")
```

## 📊 Dashboard Integration

The Dashboard shows the active LLM backend:

```
GET /api/status
→ {
    "llm_backend": "lmstudio",
    "model": "neural-chat",
    "available": true
  }
```

## ⚡ Performance Tuning

### 1. Context Window Size

Larger context = better understanding, but slower:

```env
# In LM Studio UI: Settings → Context Length
# Default: 4096 tokens
# Larger: 8192, 16384 (if VRAM allows)
```

### 2. Temperature Control

```python
# config.py — Lower = more deterministic
temperature=0.3  # Conservative (current: good for job scoring)
temperature=0.7  # Creative
temperature=1.0  # Random
```

### 3. Response Time Optimization

```python
# Faster responses = less tokens:
max_tokens=400  # Current setting (job analysis only)
max_tokens=200  # Ultra-fast
max_tokens=800  # More detailed
```

### 4. GPU Acceleration

```
LM Studio Settings → GPU:
- NVIDIA CUDA: AUTO (if available)
- Metal (macOS): AUTO
- CPU-only: Slower but works
```

## 🔧 Troubleshooting

### Issue 1: "Connection refused: localhost:1234"

```powershell
# Check if LM Studio is running:
Test-NetConnection -ComputerName localhost -Port 1234

# If not running, launch LM Studio desktop app
# Then verify:
curl http://localhost:1234/v1/models
```

### Issue 2: "Model not loaded in LM Studio"

```powershell
# LM Studio UI → Make sure model is:
# 1. Downloaded ✓
# 2. Loaded (button shows "Stop" not "Load")
# 3. Correct name in .env.lmstudio

# Test model directly:
curl -X POST http://localhost:1234/v1/chat/completions `
  -H "Content-Type: application/json" `
  -d '{
    "model": "neural-chat",
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.3,
    "max_tokens": 100
  }'
```

### Issue 3: "Out of memory (OOM)"

```
Solution:
1. Reduce model size (7B instead of 13B)
2. Reduce context length (4096 instead of 8192)
3. Reduce batch size (process 1 job at a time)
4. Use CPU-only mode (slower but works with less VRAM)
```

### Issue 4: Very Slow Responses

```powershell
# Check GPU is being used:
Get-Process lm-studio* | Format-List

# If CPU usage is high + GPU is 0% → GPU not enabled
# Solution: LM Studio Settings → GPU → Enable CUDA/Metal

# Alternative: Smaller model (mistral 7B vs neural-chat 13B)
```

## 📈 Benchmarks

### ADRIAN 369 Job Analysis Performance

| Model            | Size | Speed | Quality    | VRAM  | Notes               |
| ---------------- | ---- | ----- | ---------- | ----- | ------------------- |
| neural-chat      | 13B  | 2-3s  | ⭐⭐⭐⭐⭐ | 8GB   | **Recommended**     |
| mistral          | 7B   | 1-2s  | ⭐⭐⭐⭐   | 4.5GB | Fast, good          |
| openchat         | 7B   | 1-2s  | ⭐⭐⭐     | 4.5GB | Lightweight         |
| llama2           | 7B   | 2-3s  | ⭐⭐⭐⭐   | 4.5GB | Versatile           |
| openrouter (API) | —    | 1-2s  | ⭐⭐⭐⭐⭐ | —     | Cost: $0.05 per job |

## 🛡️ Cost Comparison

### Local (LM Studio + Ollama)

- **Cost per job**: $0.00 (just electricity)
- **Latency**: 2-5s (depends on model/hardware)
- **Privacy**: All-local, no API calls
- **Dependencies**: GPU/CPU required

### Cloud (OpenRouter API)

- **Cost per job**: $0.01-0.10 (depends on model)
- **Latency**: 500ms-2s
- **Privacy**: Data sent to cloud
- **Dependencies**: API key + internet

### Hybrid (Recommended for Production)

```env
LLM_BACKEND=auto
# Development: Use LM Studio (free, local)
# Production: OpenRouter (reliable, cost-controlled)
```

## 🚀 Production Deployment

### Option 1: Docker + LM Studio

```yaml
# docker-compose.lmstudio.yml
version: "3.8"
services:
  lmstudio:
    image: lmstudio:latest # Custom image with LM Studio
    ports:
      - "1234:1234"
    volumes:
      - ./models:/home/lmstudio/models
    environment:
      - GPU_ACCELERATION=true

  arbitrage-api:
    depends_on:
      - lmstudio
    environment:
      - LMSTUDIO_URL=http://lmstudio:1234
      - LLM_BACKEND=lmstudio
```

### Option 2: Kubernetes + LocalLLM

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: arbitrage-analyzer
spec:
  containers:
    - name: lmstudio
      image: lmstudio:latest
      resources:
        limits:
          nvidia.com/gpu: 1 # GPU allocation
    - name: arbitrage-api
      image: arbitrage-api:latest
      env:
        - name: LMSTUDIO_URL
          value: "http://localhost:1234"
```

## 📚 Resources

- **LM Studio Official**: https://lmstudio.ai/
- **Hugging Face Models**: https://huggingface.co/models
- **Model Recommendations**: https://lmstudio.ai/docs#models

## ✅ Verification Checklist

- [ ] LM Studio installed and running
- [ ] Model downloaded (neural-chat recommended)
- [ ] `.env.lmstudio` configured correctly
- [ ] `python arbitrage_server.py` starts without errors
- [ ] Dashboard shows `llm_backend: lmstudio`
- [ ] Test job analysis returns valid JSON response
- [ ] Performance is acceptable (< 5s per job)

## 🎯 Quick Start (5 minutes)

```powershell
# 1. Start LM Studio desktop app (or check it's already running)
# 2. In terminal:
copy .env.lmstudio .env.local
# 3. Edit .env.local with your model name
# 4. Start server:
.\.venv\Scripts\Activate.ps1
python arbitrage_server.py
# 5. Visit http://localhost:5000 → Dashboard shows lmstudio backend
```

---

**Status**: ✅ Production Ready
**Last Updated**: 2026-04-07
**Maintenance**: Keep LM Studio updated via app auto-update
