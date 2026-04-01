"""
LLM abstraction layer — tries Ollama (local) first, falls back to OpenRouter.
Provides a single `chat(prompt)` function for all agents.
"""

import json
import logging
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import urlencode
from arbitrage.config import (
    LLM_BACKEND, LLM_MODEL, OPENROUTER_KEY, OPENAI_KEY,
    ANTHROPIC_KEY
)

logger = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _post_json(url: str, payload: dict, headers: dict = None) -> dict:
    """HTTP POST with JSON body; returns parsed JSON response."""
    body = json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = Request(url, data=body, headers=req_headers, method="POST")
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ollama_chat(prompt: str, model: str = "deepseek-coder-v2:16b",
                 system: str = "") -> str:
    """Call local Ollama /api/chat endpoint."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.3}
    }
    result = _post_json(f"{OLLAMA_BASE}/api/chat", payload)
    return result["message"]["content"].strip()


def _openrouter_chat(prompt: str, model: str = None, system: str = "") -> str:
    """Call OpenRouter chat/completions endpoint."""
    if not OPENROUTER_KEY:
        raise ValueError("OPENROUTER_API_KEY not set")
    target_model = model or LLM_MODEL
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": target_model,
        "messages": messages,
        "temperature": 0.3
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://github.com/adrion369",
        "X-Title": "ADRION-369-Arbitrage"
    }
    result = _post_json(f"{OPENROUTER_BASE}/chat/completions", payload, headers)
    return result["choices"][0]["message"]["content"].strip()


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def chat(prompt: str, system: str = "", force_backend: str = None) -> str:
    """
    Send a prompt to the best available LLM.
    Order: Ollama (local) → OpenRouter → raises RuntimeError.

    Args:
        prompt:         User message.
        system:         Optional system prompt.
        force_backend:  'ollama' | 'openrouter' to skip auto-detection.

    Returns:
        Model response string.
    """
    backend = force_backend or LLM_BACKEND

    if backend in ("ollama", "auto"):
        try:
            return _ollama_chat(prompt, system=system)
        except (URLError, KeyError, Exception) as exc:
            logger.warning("Ollama unavailable (%s), falling back to OpenRouter", exc)
            if backend == "ollama":
                raise RuntimeError(f"Ollama failed and no fallback configured: {exc}") from exc

    # OpenRouter / any cloud backend
    return _openrouter_chat(prompt, system=system)


def is_ollama_alive() -> bool:
    """Quick health check for locally running Ollama."""
    try:
        with urlopen(f"{OLLAMA_BASE}/api/tags", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False
