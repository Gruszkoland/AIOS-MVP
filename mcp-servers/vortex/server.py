"""Vortex MCP Server — ADRION 369.

EBDI state machine, Tesla 3-6-9 digital root, 174 Hz orchestration pulse.
Port: 9001 (informational — stdio transport for VS Code MCP).

Tools (5):
  get_ebdi_state      — current Pleasure/Arousal/Dominance vector
  update_ebdi_state   — mutate PAD values with clamping
  calculate_digital_root — 3-6-9 harmonic reduction
  pulse_heartbeat     — 174 Hz synchronisation tick
  estimate_next_state — predict next EBDI state from direction + intensity

Resources (3):
  adrion://vortex/ebdi-spec      — EBDI specification JSON
  adrion://vortex/trinity-matrix — 3-6-9 mapping table
  adrion://vortex/pulse-log      — recent pulse history
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

_MCP_DIR = Path(__file__).parent.parent
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from shared import EBDIState, MCP_PORTS, TrustScore, digital_root, utc_now  # noqa: E402

logger = logging.getLogger("adrion.vortex")

HARMONIC_FREQUENCY = 174.0  # Hz — Solfeggio healing frequency

# Static 3-6-9 Trinity Matrix
TRINITY_MATRIX: dict[str, Any] = {
    "description": "Tesla 3-6-9 harmony mapping — digital roots and system resonance",
    "sacred_numbers": [3, 6, 9],
    "mappings": [
        {"input_range": "1-9",    "root": "1-9",  "resonance": "base"},
        {"input_range": "10-18",  "root": "1-9",  "resonance": "first_harmonic"},
        {"input_range": "19-27",  "root": "1-9",  "resonance": "second_harmonic"},
        {"input_range": "36",     "root": "9",    "resonance": "CRITICAL — Tesla peak"},
        {"input_range": "369",    "root": "9",    "resonance": "CRITICAL — Master number"},
    ],
    "ebdi_mapping": {
        "pleasure_root":   "maps to system satisfaction",
        "arousal_root":    "maps to system activation level",
        "dominance_root":  "maps to system control capacity",
    },
}


# ---------------------------------------------------------------------------
# Business Logic
# ---------------------------------------------------------------------------
class VortexLogic:
    """EBDI state machine and harmonic orchestration logic."""

    def __init__(self) -> None:
        self._state = EBDIState()
        self._trust = TrustScore(agent="vortex")
        self._pulse_log: list[dict[str, Any]] = []

    # -- Tools ---------------------------------------------------------------

    def get_ebdi_state(self) -> dict[str, Any]:
        """Return current EBDI vector with crisis indicator."""
        return {
            "status": "ok",
            "pleasure":   self._state.pleasure,
            "arousal":    self._state.arousal,
            "dominance":  self._state.dominance,
            "is_crisis":  self._state.is_crisis,
            "updated_at": self._state.updated_at,
            "timestamp":  utc_now(),
        }

    def update_ebdi_state(
        self,
        pleasure: float | None = None,
        arousal: float | None = None,
        dominance: float | None = None,
    ) -> dict[str, Any]:
        """Update one or more PAD dimensions; values are clamped to [0, 1]."""
        self._state.update(pleasure=pleasure, arousal=arousal, dominance=dominance)
        result = self.get_ebdi_state()
        result["updated_fields"] = [
            k for k, v in [("pleasure", pleasure), ("arousal", arousal), ("dominance", dominance)]
            if v is not None
        ]
        if self._state.is_crisis:
            result["warning"] = "Arousal > 0.7 — Crisis Mode active, route to HEALER"
        return result

    def calculate_digital_root(self, n: int) -> dict[str, Any]:
        """Reduce n to its 3-6-9 digital root."""
        root = digital_root(n)
        is_tesla = root in (3, 6, 9)
        ebdi_root_pleasure  = digital_root(int(self._state.pleasure  * 100))
        ebdi_root_arousal   = digital_root(int(self._state.arousal   * 100))
        ebdi_root_dominance = digital_root(int(self._state.dominance * 100))
        return {
            "status": "ok",
            "input": n,
            "digital_root": root,
            "is_tesla_number": is_tesla,
            "resonance": "CRITICAL" if is_tesla else "base",
            "current_ebdi_roots": {
                "pleasure":  ebdi_root_pleasure,
                "arousal":   ebdi_root_arousal,
                "dominance": ebdi_root_dominance,
            },
            "timestamp": utc_now(),
        }

    def pulse_heartbeat(self) -> dict[str, Any]:
        """Emit a 174 Hz synchronisation tick and record it."""
        import math

        phase_deg = (self._state.arousal * 360) % 360
        amplitude = 0.5 if self._state.is_crisis else 1.0
        tick: dict[str, Any] = {
            "status": "ok",
            "frequency_hz": HARMONIC_FREQUENCY,
            "phase_degrees": round(phase_deg, 2),
            "amplitude": amplitude,
            "sine_value": round(math.sin(math.radians(phase_deg)), 4),
            "in_crisis": self._state.is_crisis,
            "timestamp": utc_now(),
        }
        self._pulse_log.append(tick)
        if len(self._pulse_log) > 100:  # keep last 100 ticks
            self._pulse_log.pop(0)
        return tick

    def estimate_next_state(self, direction: str, intensity: float) -> dict[str, Any]:
        """Predict next EBDI state based on a named direction and intensity [0, 1]."""
        intensity = max(0.0, min(1.0, intensity))
        deltas: dict[str, dict[str, float]] = {
            "calm":    {"arousal": -0.1 * intensity, "pleasure": 0.05 * intensity},
            "excite":  {"arousal":  0.15 * intensity, "pleasure": 0.05 * intensity},
            "stress":  {"arousal":  0.2 * intensity,  "pleasure": -0.1 * intensity},
            "recover": {"arousal": -0.15 * intensity, "pleasure": 0.1 * intensity},
            "neutral": {},
        }
        delta = deltas.get(direction.lower(), {})
        predicted_pleasure  = max(0.0, min(1.0, self._state.pleasure  + delta.get("pleasure",  0.0)))
        predicted_arousal   = max(0.0, min(1.0, self._state.arousal   + delta.get("arousal",   0.0)))
        predicted_dominance = max(0.0, min(1.0, self._state.dominance + delta.get("dominance", 0.0)))
        return {
            "status": "ok",
            "direction": direction,
            "intensity": intensity,
            "current":  {"pleasure": self._state.pleasure,   "arousal": self._state.arousal,   "dominance": self._state.dominance},
            "predicted_pleasure":  round(predicted_pleasure,  3),
            "predicted_arousal":   round(predicted_arousal,   3),
            "predicted_dominance": round(predicted_dominance, 3),
            "predicted_crisis": predicted_arousal > 0.7,
            "timestamp": utc_now(),
        }


# ---------------------------------------------------------------------------
# MCP Server Wiring
# ---------------------------------------------------------------------------
def _build_server() -> Any:
    from mcp.server import Server  # type: ignore[import-untyped]
    from mcp.types import Resource, TextContent, Tool  # type: ignore[import-untyped]

    logic = VortexLogic()
    server = Server("adrion-vortex")

    @server.list_tools()
    async def list_tools() -> list[Tool]:  # type: ignore[return]
        return [
            Tool(name="get_ebdi_state",
                 description="Return current Pleasure/Arousal/Dominance EBDI vector with crisis indicator.",
                 inputSchema={"type": "object", "properties": {}, "required": []}),
            Tool(name="update_ebdi_state",
                 description="Update one or more PAD dimensions. Values clamped to [0.0, 1.0].",
                 inputSchema={"type": "object",
                              "properties": {
                                  "pleasure":  {"type": "number", "minimum": 0, "maximum": 1},
                                  "arousal":   {"type": "number", "minimum": 0, "maximum": 1},
                                  "dominance": {"type": "number", "minimum": 0, "maximum": 1},
                              },
                              "required": []}),
            Tool(name="calculate_digital_root",
                 description="Reduce an integer to its Tesla 3-6-9 digital root (1-9).",
                 inputSchema={"type": "object",
                              "properties": {
                                  "n": {"type": "integer", "description": "Integer to reduce"},
                              },
                              "required": ["n"]}),
            Tool(name="pulse_heartbeat",
                 description="Emit a 174 Hz synchronisation heartbeat tick.",
                 inputSchema={"type": "object", "properties": {}, "required": []}),
            Tool(name="estimate_next_state",
                 description="Predict next EBDI state given a direction (calm/excite/stress/recover) and intensity.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "direction": {"type": "string",
                                                "enum": ["calm", "excite", "stress", "recover", "neutral"]},
                                  "intensity": {"type": "number", "minimum": 0, "maximum": 1},
                              },
                              "required": ["direction", "intensity"]}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:  # type: ignore[return]
        args: dict[str, Any] = arguments or {}
        if name == "get_ebdi_state":
            result = logic.get_ebdi_state()
        elif name == "update_ebdi_state":
            result = logic.update_ebdi_state(
                pleasure=args.get("pleasure"), arousal=args.get("arousal"), dominance=args.get("dominance"))
        elif name == "calculate_digital_root":
            result = logic.calculate_digital_root(int(args["n"]))
        elif name == "pulse_heartbeat":
            result = logic.pulse_heartbeat()
        elif name == "estimate_next_state":
            result = logic.estimate_next_state(args["direction"], float(args["intensity"]))
        else:
            raise ValueError(f"Unknown tool: {name}")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    @server.list_resources()
    async def list_resources() -> list[Resource]:  # type: ignore[return]
        return [
            Resource(uri="adrion://vortex/ebdi-spec",      # type: ignore[arg-type]
                     name="EBDI Specification",
                     description="PAD model definition with crisis thresholds",
                     mimeType="application/json"),
            Resource(uri="adrion://vortex/trinity-matrix", # type: ignore[arg-type]
                     name="Trinity Matrix",
                     description="Tesla 3-6-9 digital root harmony mapping",
                     mimeType="application/json"),
            Resource(uri="adrion://vortex/pulse-log",      # type: ignore[arg-type]
                     name="Pulse Log",
                     description="Recent 174 Hz heartbeat history (last 100 ticks)",
                     mimeType="application/json"),
        ]

    @server.read_resource()
    async def read_resource(uri: Any) -> str:  # type: ignore[return]
        uri_str = str(uri)
        if uri_str == "adrion://vortex/ebdi-spec":
            return json.dumps({
                "model": "PAD (Pleasure-Arousal-Dominance)",
                "crisis_threshold": 0.7,
                "blocked_threshold": 0.6,
                "harmonic_frequency_hz": HARMONIC_FREQUENCY,
                "dimensions": {"pleasure": [0.0, 1.0], "arousal": [0.0, 1.0], "dominance": [0.0, 1.0]},
            }, indent=2)
        if uri_str == "adrion://vortex/trinity-matrix":
            return json.dumps(TRINITY_MATRIX, indent=2)
        if uri_str == "adrion://vortex/pulse-log":
            return json.dumps({"pulses": logic._pulse_log, "total": len(logic._pulse_log)}, indent=2)
        raise ValueError(f"Unknown resource URI: {uri_str}")

    return server


async def main() -> None:
    from mcp.server.stdio import stdio_server  # type: ignore[import-untyped]

    server = _build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
    logger.info("[Vortex] MCP ready on port 9001")
    asyncio.run(main())
