# Troubleshooting Guide for ADRION 369

## 🔴 Common Issues & Solutions

---

## Issue: Ollama Connection Failed

### Error Message
```
Error: Can't connect to http://localhost:11434
Connection refused
```

### Solutions

#### 1. Verify Ollama is Running
```powershell
# Check if Ollama process exists
Get-Process ollama

# Test connection
curl http://localhost:11434/api/tags

# If curl returns error, Ollama isn't running
```

#### 2. Start Ollama Service
```bash
# Windows: Start Ollama application
# Or restart the service:
nssm restart Ollama

# Check status:
nssm status Ollama
```

#### 3. Check Firewall
```powershell
# Verify port 11434 is listening
netstat -ano | findstr :11434

# Should show LISTENING on 127.0.0.1
```

#### 4. Wrong Port Configuration
```yaml
# Check .aider/config.yml
openai-api-base: http://localhost:11434/v1
                                    ^^^^^ Correct port
```

---

## Issue: Model Not Found

### Error Message
```
Error: Model 'deepseek-coder-v2:16b' not found
```

### Solutions

#### 1. Download Missing Model
```bash
# Pull the model
ollama pull deepseek-coder-v2:16b

# Or for lighter systems:
ollama pull deepseek-coder-v2:lite
```

#### 2. Verify Model is Downloaded
```bash
ollama list
# Should show deepseek-coder-v2:16b in the list
```

#### 3. Check Model Size Compatibility
```powershell
# Get available disk space
dir C:\  # Note free space

# Get available RAM
Get-WmiObject -Class Win32_PhysicalMemory | 
  Measure-Object -Property Capacity -Sum
```

**Requirements:**
- `16b` model: 16GB RAM, 25GB disk
- `lite` model: 8GB RAM, 12GB disk

#### 4. Verify Ollama Home Directory
```powershell
# Ollama stores models in:
$env:OLLAMA_HOME
# Usually: C:\Users\[YourUser]\.ollama

# Check if models are there:
ls C:\Users\[YourUser]\.ollama\models\
```

---

## Issue: Out of Memory Errors

### Error Message
```
GPU out of memory / CUDA out of memory
or
cudaMalloc failed: out of memory
```

### Solutions

#### 1. Use Smaller Model
```bash
# Instead of 16b:
ollama run deepseek-coder-v2:lite

# Or try even smaller:
ollama run phi:2b
```

#### 2. Reduce Model Context
```yaml
# In .aider/config.yml
context-limit: 8000  # was 16000
max-thinking-length: 12000  # was 24000
```

#### 3. Free Up Memory
```powershell
# Check memory usage
Get-WmiObject -Class Win32_Process -Filter "Name='ollama.exe'" |
  Select-Object ProcessId, @{Name="MemoryMB";Expression={$_.WorkingSetSize/1MB -as [int]}}

# Close unnecessary applications
# Restart Ollama:
nssm restart Ollama
```

#### 4. Check GPU Memory
```bash
# If using NVIDIA:
nvidia-smi

# If VRAM < 4GB, you need at least 8GB system RAM
```

---

## Issue: Aider Not Loading Configuration

### Error Message
```
Warning: Config file not found
Using defaults instead
```

### Solutions

#### 1. Verify Config File Exists
```powershell
ls .aider/config.yml

# If not found, check you're in the right directory:
pwd  # Should show project root
```

#### 2. Fix YAML Syntax
```bash
# Config must be valid YAML
# Common mistakes:
# ❌ Spaces instead of dashes: " - key: value"
# ❌ Tabs instead of spaces (use spaces only)
# ❌ Missing colons: "key value" should be "key: value"

# Validate YAML:
# Use https://www.yamllint.com/ or similar
```

#### 3. Use Explicit Config Path
```bash
aider --config .aider/config.yml
```

#### 4. Check File Permissions
```powershell
# Ensure file is readable:
Get-ItemProperty .aider/config.yml | Select-Object Name, Mode
# Mode should include 'r' for read
```

---

## Issue: Aider Connection Slow or Hanging

### Error Message
```
Waiting for response... (takes 30+ seconds)
or
Timeout: No response from model
```

### Solutions

#### 1. Check Network (Ollama Server)
```bash
# Test connection quality
curl -v http://localhost:11434/api/tags

# Should respond within 1 second
```

#### 2. Check Ollama Load
```powershell
# High CPU/Memory by ollama.exe?
Get-Process ollama | 
  Format-Table ProcessId, CPU, WorkingSet, Path
```

#### 3. Reduce Inference Load
```yaml
# In .aider/config.yml
temperature: 0.5    # was 0.7 (lower = faster)
max-thinking-length: 8000  # was 24000
stream: false       # Try disabling streaming
```

#### 4. Check System Resources
```powershell
# Overall system load
Get-Counter '\Processor(_Total)\% Processor Time'

# If > 90%, system is overloaded
```

#### 5. Restart Ollama
```bash
# Kill and restart
nssm stop Ollama
Start-Sleep -Seconds 5
nssm start Ollama
```

---

## Issue: Persona Commands Not Recognized

### Error Message
```
Unknown command: @librarian
or
Persona not recognized
```

### Solutions

#### 1. Verify Persona Names (Case Sensitive)
```
Correct:
@librarian  (lowercase)
@sap
@auditor
@sentinel
@architect
@healer

Incorrect:
@Librarian  (capital L)
@LIBRARIAN  (all caps)
```

#### 2. Check Config File
```bash
# Ensure config/personas.yml exists:
ls config/personas.yml

# Verify persona entries in the file:
grep "^  [a-z]" config/personas.yml
```

#### 3. Reload Aider
```bash
# Exit Aider (Ctrl+C) and restart:
aider

# This reloads all configurations
```

---

## Issue: Git Commits Not Working

### Error Message
```
Error: No git repository found
or
Failed to create commit
```

### Solutions

#### 1. Initialize Git
```bash
# If you don't have git initialized:
git init

# Configure git:
git config user.name "Your Name"
git config user.email "your@email.com"
```

#### 2. Check Git Installation
```bash
git --version

# If command not found, install Git from git-scm.com
```

#### 3. Verify Aider Git Settings
```yaml
# In .aider/config.yml
auto-commits: true
commit-message: "{role}: {action} ({timestamp})"
```

#### 4. Manual Commit
```bash
# If auto-commits fail, do manually:
git add .
git commit -m "LIBRARIAN: Code analysis and updates (2026-03-29)"
```

---

## Issue: High Token Usage / Context Limit

### Error Message
```
Context limit exceeded
or
File too large to include
```

### Solutions

#### 1. Reduce Context Size
```yaml
# In .aider/config.yml
context-limit: 8000  # was 16000
```

#### 2. Exclude Large Files
```yaml
# In .aider/config.yml, add:
exclude-patterns:
  - "*.pyc"
  - "node_modules/**"
  - "dist/**"
  - ".git/**"
  - "*.exe"
```

#### 3. Work on Smaller Portions
```
# Instead of:
Optimize entire codebase

# Try:
Optimize just the payment module
```

#### 4. Use Streaming Responsibly
```yaml
stream: true       # Shows tokens as they come
# With streaming, context is freed incrementally
```

---

## Issue: GPU Not Being Used (Slow CPU-Only Mode)

### Error Message
No explicit error, but Aider is very slow.

### Solutions

#### 1. Check GPU Availability
```bash
# For NVIDIA:
nvidia-smi

# For AMD:
rocm-smi

# If nothing shows, GPU support not available
```

#### 2. Enable CUDA in Ollama
```powershell
# Set environment variable before starting Ollama
$env:OLLAMA_DEBUG="1"

# Start Ollama
ollama serve

# Check logs for GPU initialization
```

#### 3. Install NVIDIA Drivers
```
GPU Support: https://developer.nvidia.com/cuda-downloads
AMD ROCm: https://rocmdocs.amd.com/
```

#### 4. Verify Ollama GPU Support
```bash
# Ollama checks automatically on startup
# Look for: "GPU acceleration" messages in console

# Force CPU:
set OLLAMA_NUM_GPU=0  (but this is slower)
```

---

## Issue: Logs Not Being Written

### Error Message
```
Genesis Record (logs) are empty or missing
```

### Solutions

#### 1. Check Log Directory
```powershell
ls .aider/logs/
# Should contain session.log files
```

#### 2. Create Missing Directory
```bash
mkdir -Force .aider/logs

# Grant write permissions:
icacls .aider/logs /grant %USERNAME%:F
```

#### 3. Enable Logging
```yaml
# In .aider/config.yml
log-all-messages: true
log-file: .aider/logs/session.log
```

#### 4. Verify Disk Space
```powershell
# Check free space
Get-Volume

# If < 100MB free, logs may fail
```

---

## Issue: Persona Responses Are Generic/Unhelpful

### Error Message
```
Response doesn't match expected persona behavior
or
Output isn't specialized enough
```

### Solutions

#### 1. Check Persona Context
```
Before querying persona, provide context:

@librarian
[First, read this summary of the project]
Now analyze [specific aspect]
```

#### 2. Verify System Prompts
```bash
# Check persona definitions:
grep -A 20 "system_prompt:" config/personas.yml
```

#### 3. Increase Model Quality
```bash
# Use larger model:
ollama run deepseek-coder-v2:16b  # not lite

# Or higher temperature:
temperature: 0.9  # was 0.7 (more creative)
```

#### 4. Restart with Fresh Context
```bash
# Exit Aider
# Clear cache:
ollama list  # verify model is loaded

# Restart Aider
aider
```

---

## Quick Diagnostic Checklist

```
□ Ollama running? 
  curl http://localhost:11434/api/tags

□ Model downloaded?
  ollama list

□ Config file valid?
  cat .aider/config.yml

□ Git initialized?
  git status

□ Disk space?
  Get-Volume

□ Network working?
  ping localhost

□ Python version OK?
  python --version (should be 3.10+)
```

---

## Getting Help

1. **Check `.aider/logs/session.log`** for detailed error messages
2. **Search GitHub Issues**: https://github.com/paul-gauthier/aider/issues
3. **Ollama Docs**: https://github.com/ollama/ollama
4. **Run with debug**: `aider --debug`

---

**Last Updated:** March 29, 2026  
**Version:** 1.0
