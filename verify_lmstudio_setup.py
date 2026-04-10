#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  LM STUDIO INTEGRATION VERIFICATION

  Usage:
    python verify_lmstudio_setup.py              # Full check
    python verify_lmstudio_setup.py --quick     # Just connection test
    python verify_lmstudio_setup.py --test-job  # Analyze sample job
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import json
import time
import argparse
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any

# ═══ Parser ═══
parser = argparse.ArgumentParser()
parser.add_argument("--quick", action="store_true", help="Quick connection test")
parser.add_argument("--test-job", action="store_true", help="Analyze a sample job")
parser.add_argument("--backend", default="auto", help="LLM backend to test (auto/lmstudio/ollama/openrouter)")
args = parser.parse_args()

# ═══ Colors ═══
class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    END = "\033[0m"

def success(msg):
    print(f"{Color.GREEN}✅ {msg}{Color.END}")

def error(msg):
    print(f"{Color.RED}❌ {msg}{Color.END}")

def info(msg):
    print(f"{Color.CYAN}ℹ️  {msg}{Color.END}")

def warn(msg):
    print(f"{Color.YELLOW}⚠️  {msg}{Color.END}")

# ═══ Phase 1: Environment Check ═══
print(f"\n{Color.CYAN}═══════════════════════════════════════════════════════════{Color.END}")
print(f"{Color.CYAN}  LM STUDIO INTEGRATION VERIFICATION{Color.END}")
print(f"{Color.CYAN}═══════════════════════════════════════════════════════════{Color.END}\n")

info("Checking environment...")

# Check venv
venv_path = Path(".venv")
if not venv_path.exists():
    error("Python venv not found. Run: python -m venv .venv")
    sys.exit(1)
success("Python venv found")

# Check config files
env_file = Path(".env")
if env_file.exists():
    success(".env configuration found")
else:
    warn(".env not found (using defaults)")

# ═══ Phase 2: Import Check ═══
info("Checking Python imports...")
try:
    from arbitrage.config import (
        LLM_BACKEND,
        get_active_llm_backend,
        LMSTUDIO_URL,
        LMSTUDIO_MODEL,
        OLLAMA_URL,
        OLLAMA_MODEL,
    )
    success("Config imports successful")
except ImportError as e:
    error(f"Config import failed: {e}")
    sys.exit(1)

try:
    from arbitrage.analyzer import analyze_job
    success("Analyzer imports successful")
except ImportError as e:
    error(f"Analyzer import failed: {e}")
    sys.exit(1)

# ═══ Phase 3: Backend Detection ═══
print(f"\n{Color.CYAN}[3/5] Backend Detection{Color.END}")
try:
    active_backend = get_active_llm_backend()
    print(f"  Active backend (auto): {active_backend}")
    print(f"  LM Studio URL: {LMSTUDIO_URL}")
    print(f"  LM Studio Model: {LMSTUDIO_MODEL}")
    print(f"  Ollama URL: {OLLAMA_URL}")
    print(f"  Ollama Model: {OLLAMA_MODEL}")
except Exception as e:
    error(f"Backend detection failed: {e}")
    sys.exit(1)

# ═══ Phase 4: Service Health Check ═══
print(f"\n{Color.CYAN}[4/5] Service Health Check{Color.END}")

def check_service(name: str, url: str) -> bool:
    """Check if a service is responding."""
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            return resp.status == 200
    except Exception as e:
        return False

# Check LM Studio
lmstudio_ok = check_service("LM Studio", f"{LMSTUDIO_URL}/v1/models")
if lmstudio_ok:
    success(f"LM Studio: ✅ {LMSTUDIO_URL}")
else:
    error(f"LM Studio: ❌ {LMSTUDIO_URL} (not responding)")

# Check Ollama
ollama_ok = check_service("Ollama", f"{OLLAMA_URL}/api/tags")
if ollama_ok:
    success(f"Ollama: ✅ {OLLAMA_URL}")
else:
    warn(f"Ollama: ❌ {OLLAMA_URL} (not responding)")

# Check overall status
if lmstudio_ok or ollama_ok:
    success("At least one LLM server is available")
else:
    error("No LLM servers available (lmstudio + ollama)")
    warn("Start LM Studio: https://lmstudio.ai/ (recommended)")
    warn("OR Start Ollama: ollama pull deepseek:7b && ollama serve")

# ═══ Phase 5: Model Verification ═══
if not args.quick:
    print(f"\n{Color.CYAN}[5/5] Model Verification{Color.END}")

    if lmstudio_ok:
        try:
            with urllib.request.urlopen(f"{LMSTUDIO_URL}/v1/models", timeout=3) as resp:
                data = json.loads(resp.read())
                models = data.get("data", [])
                if models:
                    success(f"LM Studio models: {[m.get('id') for m in models[:3]]}")
                else:
                    warn("No models loaded in LM Studio")
        except Exception as e:
            error(f"Could not fetch LM Studio models: {e}")

    if ollama_ok:
        try:
            with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3) as resp:
                data = json.loads(resp.read())
                models = data.get("models", [])
                if models:
                    success(f"Ollama models: {[m.get('name') for m in models[:3]]}")
                else:
                    warn("No models available in Ollama")
        except Exception as e:
            error(f"Could not fetch Ollama models: {e}")

# ═══ Phase 6: Job Analysis Test ═══
if args.test_job and (lmstudio_ok or ollama_ok):
    print(f"\n{Color.CYAN}[6/x] Job Analysis Test{Color.END}")
    info("Analyzing sample job...")

    sample_job = {
        "id": "test_job_001",
        "title": "Write SEO Blog Post",
        "platform": "upwork",
        "budget_min": 100,
        "budget_max": 300,
        "description": "Need 5000-word blog post about Python optimization. Include code examples."
    }

    start = time.time()
    try:
        result = analyze_job(sample_job)
        elapsed = time.time() - start

        success(f"Analysis completed in {elapsed:.2f}s")
        print(f"  Backend: {result.get('llm_backend')}")
        print(f"  Score: {result.get('score')}/10")
        print(f"  Fit: {result.get('fit')}")
        print(f"  Est. Profit: ${result.get('est_profit')}")
        print(f"  Est. Cost: ${result.get('est_cost')}")

    except Exception as e:
        error(f"Job analysis failed: {e}")
        warn(f"Stack trace: {e.__class__.__name__}: {str(e)}")

# ═══ Summary ═══
print(f"\n{Color.CYAN}═══════════════════════════════════════════════════════════{Color.END}")

status = "✅ READY" if (lmstudio_ok or ollama_ok) else "❌ ISSUES"
print(f"{Color.CYAN}Status: {status}{Color.END}")

print(f"\n{Color.CYAN}📋 Next Steps:{Color.END}")
if not lmstudio_ok:
    print(f"  1. Download LM Studio: https://lmstudio.ai/")
    print(f"  2. Launch the desktop app")
    print(f"  3. Download a model (neural-chat recommended)")
    print(f"  4. Start local server (Settings → Local Server → Start)")
if not ollama_ok:
    print(f"  1. Install Ollama: https://ollama.ai/")
    print(f"  2. Download a model: ollama pull deepseek:7b")
    print(f"  3. Start server: ollama serve")

print(f"\n{Color.CYAN}🚀 To start ADRIAN 369:{Color.END}")
print(f"  .\\\.venv\\\Scripts\\\Activate.ps1")
print(f"  python arbitrage_server.py")
print(f"  python dashboard/server.py  # (another terminal)")

print(f"\n{Color.CYAN}═══════════════════════════════════════════════════════════{Color.END}\n")
