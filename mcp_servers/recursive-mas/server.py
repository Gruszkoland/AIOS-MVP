"""RecursiveMAS MCP Server wrapper for adrion-369.

Exposes RecursiveMAS inference as MCP tools:
- recursive_mas_infer: run inference on a prompt with given style
- recursive_mas_status: check loaded models and system state
- recursive_mas_styles: list available collaboration styles
"""
from __future__ import annotations

import os
import sys
import json
import logging
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Add RecursiveMAS root to path
sys.path.insert(0, "/app")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recursive-mcp")

app = FastAPI(
    title="RecursiveMAS MCP Server",
    description="Multi-Agent System inference via latent-space recursion",
    version="1.0.0",
)

# Lazy-loaded MAS instance
_mas_instance: Any = None
_mas_style: str = os.getenv("RECURSIVE_MAS_STYLE", "sequential_light")
_device: str = os.getenv("RECURSIVE_MAS_DEVICE", "cpu")

AVAILABLE_STYLES = [
    "sequential_light",
    "sequential_scaled",
    "mixture",
    "distillation",
    "deliberation",
]


def _load_mas() -> Any:
    """Lazy-load the MAS system on first inference request."""
    global _mas_instance
    if _mas_instance is not None:
        return _mas_instance
    try:
        from system_loader import load_mas_system  # noqa: PLC0415
        _mas_instance = load_mas_system(
            style=_mas_style,
            device=_device,
            trust_remote_code=True,
        )
        logger.info("RecursiveMAS loaded: style=%s device=%s", _mas_style, _device)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load MAS: %s", exc)
        _mas_instance = None
    return _mas_instance


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "style": _mas_style, "device": _device})


@app.get("/tools/recursive_mas_styles")
def list_styles() -> JSONResponse:
    """MCP tool: list available RecursiveMAS collaboration styles."""
    return JSONResponse({
        "styles": AVAILABLE_STYLES,
        "current": _mas_style,
        "description": {
            "sequential_light": "Planner+Critic+Solver (1-2B) — szybkie pipeline",
            "sequential_scaled": "Planner+Critic+Solver (3-9B) — złożone rozumowanie",
            "mixture": "Domain agents + Summarizer — wielodomenowe analizy",
            "distillation": "Expert + Learner — optymalizacja inference",
            "deliberation": "Reflector + ToolCaller — integracja z narzędziami",
        },
    })


@app.get("/tools/recursive_mas_status")
def status() -> JSONResponse:
    """MCP tool: check MAS system state."""
    mas = _mas_instance
    if mas is None:
        return JSONResponse({"loaded": False, "style": _mas_style, "device": _device})
    agents = list(getattr(mas, "agents", {}).keys())
    return JSONResponse({"loaded": True, "style": _mas_style, "device": _device, "agents": agents})


@app.post("/tools/recursive_mas_infer")
async def infer(payload: dict) -> JSONResponse:
    """MCP tool: run RecursiveMAS inference.

    Payload:
        prompt (str): input prompt
        style (str, optional): override style
        temperature (float, optional): sampling temperature (default 0.6)
        top_p (float, optional): nucleus sampling (default 0.95)
    """
    prompt = payload.get("prompt", "")
    if not prompt:
        return JSONResponse({"error": "prompt is required"}, status_code=400)

    mas = _load_mas()
    if mas is None:
        return JSONResponse(
            {"error": "MAS system not loaded — check logs and model checkpoints"},
            status_code=503,
        )

    try:
        # Basic inference interface — extend per style as needed
        result = mas.run(prompt=prompt)
        return JSONResponse({"result": result, "style": _mas_style})
    except Exception as exc:  # noqa: BLE001
        logger.error("Inference error: %s", exc)
        return JSONResponse({"error": str(exc)}, status_code=500)


if __name__ == "__main__":
    port = int(os.getenv("RECURSIVE_MAS_PORT", "8095"))
    logger.info("Starting RecursiveMAS MCP Server on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
