"""
LLM abstraction layer — tries Ollama (local) first, falls back to OpenRouter.
Provides a single `chat(prompt)` function for all agents.
"""

import hashlib
import json
import logging
import os
import re
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from arbitrage.config import LLM_BACKEND, LLM_MODEL, OPENROUTER_KEY

logger = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

PROMPT_MAX_CHARS = int(os.getenv("LLM_PROMPT_MAX_CHARS", "12000"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.9"))
LLM_NUM_PREDICT = int(os.getenv("LLM_NUM_PREDICT", "700"))
LLM_CANARY_ENABLED = os.getenv("LLM_CANARY_ENABLED", "0").strip() == "1"
LLM_CANARY_PERCENT = float(os.getenv("LLM_CANARY_PERCENT", "10"))
LLM_CANARY_BACKEND = os.getenv("LLM_CANARY_BACKEND", "openrouter").strip().lower()
LLM_ROLLOUT_STATE_PATH = os.getenv(
    "LLM_ROLLOUT_STATE_PATH",
    str(os.path.join("monitoring", "llm_rollout_state.json")),
)
LLM_KPI_LOG_PATH = os.getenv(
    "LLM_KPI_LOG_PATH",
    str(os.path.join("monitoring", "llm_kpi_events.jsonl")),
)
LLM_KPI_MAX_ERROR_RATE = float(os.getenv("LLM_KPI_MAX_ERROR_RATE", "0.05"))
LLM_KPI_MAX_P95_MS = float(os.getenv("LLM_KPI_MAX_P95_MS", "8000"))

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"developer\s*message", re.IGNORECASE),
    re.compile(r"reveal\s+.*(secret|token|key|password)", re.IGNORECASE),
]


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


def _sanitize_text(value: str) -> str:
    """Normalize user/system text and remove NULL characters."""
    if value is None:
        return ""
    return value.replace("\x00", "").strip()


def _validate_prompt(prompt: str, system: str = "") -> None:
    """Fail-fast validation to reduce injection and malformed input risk."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    if len(prompt) > PROMPT_MAX_CHARS:
        raise ValueError(f"Prompt exceeds max length ({PROMPT_MAX_CHARS} chars)")

    merged = f"{system}\n{prompt}".strip()
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(merged):
            raise ValueError("Prompt rejected by safety guardrails")


def _safe_temperature() -> float:
    """Clamp configured temperature to deterministic-safe range."""
    return max(0.0, min(0.5, LLM_TEMPERATURE))


def _safe_top_p() -> float:
    """Clamp configured top_p to valid range."""
    return max(0.1, min(1.0, LLM_TOP_P))


def _safe_canary_percent() -> float:
    """Clamp canary percentage into [0, 100]."""
    return max(0.0, min(100.0, LLM_CANARY_PERCENT))


def _read_rollout_state() -> dict:
    """Read local rollout state overrides (if present)."""
    if not os.path.exists(LLM_ROLLOUT_STATE_PATH):
        return {}
    try:
        with open(LLM_ROLLOUT_STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.warning("Rollout state read failed: %s", exc)
        return {}


def _write_rollout_state(state: dict) -> None:
    """Persist local rollout state in JSON format."""
    os.makedirs(os.path.dirname(LLM_ROLLOUT_STATE_PATH), exist_ok=True)
    with open(LLM_ROLLOUT_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=True, indent=2)


def get_effective_canary_settings() -> dict:
    """Return merged canary settings from env defaults + runtime state file."""
    state = _read_rollout_state()
    enabled = bool(state.get("canary_enabled", LLM_CANARY_ENABLED))
    percent = float(state.get("canary_percent", _safe_canary_percent()))
    percent = max(0.0, min(100.0, percent))
    backend = str(state.get("canary_backend", LLM_CANARY_BACKEND)).strip().lower()
    if backend not in ("ollama", "openrouter"):
        backend = LLM_CANARY_BACKEND
    return {
        "canary_enabled": enabled,
        "canary_percent": percent,
        "canary_backend": backend,
        "source": "state" if state else "env",
    }


def force_canary_rollback(reason: str = "kpi_gate_failed") -> dict:
    """Immediately disable canary traffic using local rollout state override."""
    state = {
        "canary_enabled": False,
        "canary_percent": 0.0,
        "reason": reason,
        "ts": int(time.time()),
    }
    _write_rollout_state(state)
    return state


def set_canary_rollout(percent: float, backend: str = "openrouter",
                       reason: str = "manual") -> dict:
    """Persist canary rollout percentage (0-100) with selected backend."""
    safe_percent = max(0.0, min(100.0, float(percent)))
    safe_backend = str(backend).strip().lower()
    if safe_backend not in ("ollama", "openrouter"):
        safe_backend = "openrouter"

    state = {
        "canary_enabled": safe_percent > 0.0,
        "canary_percent": safe_percent,
        "canary_backend": safe_backend,
        "reason": reason,
        "ts": int(time.time()),
    }
    _write_rollout_state(state)
    return state


def _is_canary_candidate(prompt: str, system: str) -> bool:
    """Deterministic bucketing for canary rollout based on request content."""
    settings = get_effective_canary_settings()
    if not settings["canary_enabled"]:
        return False
    percent = float(settings["canary_percent"])
    if percent <= 0:
        return False

    token = f"{system}\n{prompt}".encode("utf-8", errors="ignore")
    digest = hashlib.sha256(token).hexdigest()
    bucket = int(digest[:8], 16) % 10000
    return bucket < int(percent * 100)


def _log_kpi_event(event: dict) -> None:
    """Append a compact KPI record as JSONL for canary and rollout gates."""
    try:
        os.makedirs(os.path.dirname(LLM_KPI_LOG_PATH), exist_ok=True)
        with open(LLM_KPI_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=True) + "\n")
    except Exception as exc:
        logger.warning("KPI logging failed: %s", exc)


def get_kpi_snapshot(max_events: int = 200, age_limit_seconds: float | None = None) -> dict:
    """Read latest KPI events and compute simple rollout metrics.

    Args:
        max_events: Maximum number of most-recent events to evaluate.
        age_limit_seconds: If set, exclude events older than this many seconds
            from ``now``. Useful to avoid stale historical outages poisoning
            the rolling metric (e.g. ``age_limit_seconds=7*86400`` for 7 days).
    """
    if max_events <= 0:
        return {"count": 0, "error_rate": 0.0, "p95_latency_ms": 0.0}

    if not os.path.exists(LLM_KPI_LOG_PATH):
        return {"count": 0, "error_rate": 0.0, "p95_latency_ms": 0.0}

    events = []
    try:
        with open(LLM_KPI_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception as exc:
        logger.warning("KPI snapshot read failed: %s", exc)
        return {"count": 0, "error_rate": 0.0, "p95_latency_ms": 0.0}

    if age_limit_seconds is not None and age_limit_seconds > 0:
        cutoff = time.time() - age_limit_seconds
        events = [e for e in events if float(e.get("ts", 0)) >= cutoff]

    window = events[-max_events:]
    if not window:
        return {"count": 0, "error_rate": 0.0, "p95_latency_ms": 0.0}

    errors = sum(1 for e in window if not e.get("success", False))
    latencies = sorted(
        float(e.get("latency_ms", 0.0)) for e in window if e.get("latency_ms") is not None
    )
    if latencies:
        idx = max(0, min(len(latencies) - 1, int(0.95 * (len(latencies) - 1))))
        p95 = latencies[idx]
    else:
        p95 = 0.0

    return {
        "count": len(window),
        "error_rate": errors / len(window),
        "p95_latency_ms": p95,
    }


def kpi_gate_passed(snapshot: dict = None) -> tuple[bool, list[str]]:
    """Evaluate rollout gate against current KPI thresholds."""
    snap = snapshot or get_kpi_snapshot()
    reasons = []
    if snap.get("error_rate", 0.0) > LLM_KPI_MAX_ERROR_RATE:
        reasons.append("error_rate")
    if snap.get("p95_latency_ms", 0.0) > LLM_KPI_MAX_P95_MS:
        reasons.append("p95_latency_ms")
    return len(reasons) == 0, reasons


def _ollama_chat(prompt: str, model: str = "deepseek-coder-v2:16b",
                 system: str = "") -> str:
    """Call local Ollama /api/chat endpoint."""
    prompt = _sanitize_text(prompt)
    system = _sanitize_text(system)
    _validate_prompt(prompt, system)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": _safe_temperature(),
            "top_p": _safe_top_p(),
            "num_predict": LLM_NUM_PREDICT,
        },
    }
    result = _post_json(f"{OLLAMA_BASE}/api/chat", payload)
    return result["message"]["content"].strip()


def _openrouter_chat(prompt: str, model: str = None, system: str = "") -> str:
    """Call OpenRouter chat/completions endpoint."""
    prompt = _sanitize_text(prompt)
    system = _sanitize_text(system)
    _validate_prompt(prompt, system)

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
        "temperature": _safe_temperature(),
        "top_p": _safe_top_p(),
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
    started = time.perf_counter()
    backend = force_backend or LLM_BACKEND
    requested_backend = backend
    selected_backend = backend
    canary = False

    prompt = _sanitize_text(prompt)
    system = _sanitize_text(system)

    canary_settings = get_effective_canary_settings()
    if force_backend is None and backend in ("auto", "ollama") and _is_canary_candidate(prompt, system):
        if canary_settings["canary_backend"] in ("openrouter", "ollama"):
            selected_backend = canary_settings["canary_backend"]
            canary = True

    success = False
    error_kind = ""
    response = None

    try:
        if selected_backend in ("ollama", "auto"):
            try:
                response = _ollama_chat(prompt, system=system)
                success = True
                return response
            except (URLError, KeyError, Exception) as exc:
                logger.warning("Ollama unavailable (%s), falling back to OpenRouter", exc)
                if selected_backend == "ollama":
                    error_kind = exc.__class__.__name__
                    raise RuntimeError(f"Ollama failed and no fallback configured: {exc}") from exc

        response = _openrouter_chat(prompt, system=system)
        success = True
        return response
    except Exception as exc:
        error_kind = exc.__class__.__name__
        raise
    finally:
        latency_ms = (time.perf_counter() - started) * 1000.0
        _log_kpi_event(
            {
                "ts": int(time.time()),
                "requested_backend": requested_backend,
                "selected_backend": selected_backend,
                "canary": canary,
                "success": success,
                "error_kind": error_kind,
                "latency_ms": round(latency_ms, 2),
                "prompt_len": len(prompt),
                "system_len": len(system),
            }
        )


def is_ollama_alive() -> bool:
    """Quick health check for locally running Ollama."""
    try:
        with urlopen(f"{OLLAMA_BASE}/api/tags", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False
