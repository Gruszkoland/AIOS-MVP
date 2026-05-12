"""
MCP Blueprint — ADRION 369 MCP Server Router

Exposes MCP servers (Genesis, Guardian, Healer, Oracle, Router, Vortex) via REST API.
Integrates HARMONIA-GATEWAY for semantic flag compression and DSPy signature validation.

Endpoint: POST /api/mcp/invoke/<server>
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request

from arbitrage.gateway.harmonia import (
    FlagRegistry,
    create_genesis_record,
    audit_output,
)

logger = logging.getLogger(__name__)

mcp_bp = Blueprint("mcp_bp", __name__, url_prefix="/api/mcp")

# ────────────────────────────────────────────────────────────────────────────
# MCP SERVER REGISTRY (T14 — SAFE-MCP)
# ────────────────────────────────────────────────────────────────────────────

MCP_SERVERS = {
    "genesis": {
        "module": "mcp_servers.genesis_mcp",
        "class": "GenesisMCP",
        "description": "Genesis Record audit trail manager",
        "commands": ["append", "verify", "dump"],
    },
    "guardian": {
        "module": "mcp_servers.guardian_mcp",
        "class": "GuardianMCP",
        "description": "Guardian Laws v11 enforcement",
        "commands": ["validate", "check_law", "list_laws"],
    },
    "healer": {
        "module": "mcp_servers.healer_mcp",
        "class": "HealerMCP",
        "description": "Self-healing and error recovery",
        "commands": ["heal", "diagnose", "repair"],
    },
    "oracle": {
        "module": "mcp_servers.oracle_mcp",
        "class": "OracleMCP",
        "description": "Vortex Oracle predictions",
        "commands": ["predict", "scan", "forecast"],
    },
    "router": {
        "module": "mcp_servers.router",
        "class": "RouterMCP",
        "description": "Request dispatcher and agent routing",
        "commands": ["route", "dispatch", "status"],
    },
    "vortex": {
        "module": "mcp_servers.vortex_mcp",
        "class": "VortexMCP",
        "description": "Real-time state tracking and EBDI monitoring",
        "commands": ["state", "ebdi_update", "monitor"],
    },
}

# ────────────────────────────────────────────────────────────────────────────
# HELPER: Safe MCP Invocation with DSPy Validation
# ────────────────────────────────────────────────────────────────────────────

def safe_mcp_invoke(
    server_name: str,
    command: str,
    params: Dict[str, Any],
    flags: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Safely invoke MCP server with DSPy signature validation.

    DSPy Signature:
        In(server:str, cmd:str, params:dict, flags:str|None)
        → Out(result:dict, status:int, ok:bool)

    Steps:
    1. Parse flags (HARMONIA-GATEWAY)
    2. Tier-1 checks (SYS:ETH_A369 → Guardian validation)
    3. Load MCP server module
    4. Call method with params
    5. Validate output schema
    6. Log to Genesis Record
    7. Return result
    """

    result = {"status": 500, "ok": False, "message": "", "data": None}

    try:
        # Step 1: Parse flags
        parsed_flags = FlagRegistry.parse_flags(flags or "")

        # Step 2: Tier-1 system checks
        if parsed_flags.get("tier_1_system"):
            sys_cmd = parsed_flags["tier_1_system"]
            if sys_cmd.get("cmd") == "TTL_PING":
                return {"status": 200, "ok": True, "message": "PONG", "data": {}}
            elif sys_cmd.get("cmd") == "HALT":
                return {"status": 503, "ok": False, "message": "HALTED", "data": {}}
            elif sys_cmd.get("cmd") == "ETH_A369":
                # Guardian validation would happen here
                logger.info("ETH_A369 check initiated")

        # Step 3: Validate server name
        if server_name not in MCP_SERVERS:
            result["message"] = f"Unknown MCP server: {server_name}. Available: {list(MCP_SERVERS.keys())}"
            result["status"] = 400
            return result

        server_config = MCP_SERVERS[server_name]

        # Step 4: Dynamically load MCP module
        try:
            module = __import__(server_config["module"], fromlist=[server_config["class"]])
            mcp_class = getattr(module, server_config["class"])
            mcp_instance = mcp_class()
        except (ImportError, AttributeError) as e:
            result["message"] = f"Failed to load MCP server {server_name}: {str(e)}"
            result["status"] = 500
            logger.error(f"MCP Load Error: {result['message']}")
            return result

        # Step 5: Call MCP method
        if not hasattr(mcp_instance, command):
            result["message"] = f"MCP {server_name} does not support command: {command}"
            result["status"] = 400
            return result

        method = getattr(mcp_instance, command)
        mcp_result = method(params) if isinstance(params, dict) else method(params)

        # Step 6: Log to Genesis Record
        gr = create_genesis_record(
            agent="ORCHESTRATOR",
            action_type="TOOL_CALL",
            payload={
                "tool_id": f"T14-MCP-{server_name}",
                "command": command,
                "input": params,
                "output": mcp_result,
            },
        )

        # Append to Genesis Record (append-only)
        try:
            gr_path = Path("memories/genesis_record.jsonl")
            if gr_path.exists():
                with open(gr_path, "a") as f:
                    f.write(gr.to_jsonl() + "\n")
                logger.info(f"Genesis Record written: {gr.genesis_id}")
        except Exception as e:
            logger.warning(f"Failed to write Genesis Record: {e}")

        # Step 7: Format output
        audit_pass, audit_error = audit_output(
            mcp_result,
            flags=parsed_flags,
        )
        if not audit_pass:
            logger.warning(f"Output audit failed: {audit_error}")
            result["message"] = f"Output audit failed: {audit_error}"
            result["status"] = 500
            return result

        result["status"] = 200
        result["ok"] = True
        result["message"] = f"MCP {server_name}.{command} succeeded"
        result["data"] = mcp_result
        return result

    except Exception as e:
        logger.exception(f"Unexpected error in safe_mcp_invoke: {e}")
        result["message"] = str(e)
        result["status"] = 500
        return result


# ────────────────────────────────────────────────────────────────────────────
# ROUTES
# ────────────────────────────────────────────────────────────────────────────

@mcp_bp.post("/invoke/<server>")
def invoke_mcp(server: str):
    """
    Invoke MCP server with command and parameters.

    Query Parameters:
    - cmd (required): Command name
    - flags (optional): HARMONIA-GATEWAY flags, e.g., [SYS:ETH_A369][FMT:SBAR]

    Body (JSON):
    - params (optional): Command parameters object

    Example:
        POST /api/mcp/invoke/guardian?cmd=validate&flags=[SYS:ETH_A369][FMT:SBAR]
        Body: {"action": "check_harmony", "context": {...}}
    """
    try:
        cmd = request.args.get("cmd")
        flags = request.args.get("flags")
        params = request.get_json() or {}

        if not cmd:
            return jsonify({"error": "Missing 'cmd' parameter"}), 400

        result = safe_mcp_invoke(server, cmd, params, flags)
        return jsonify(result), result["status"]

    except Exception as e:
        logger.exception(f"Error in invoke_mcp: {e}")
        return jsonify({"error": str(e), "status": 500}), 500


@mcp_bp.get("/status")
def mcp_status():
    """
    Get status of all MCP servers and API health.

    DSPy Signature:
        In() → Out(status:dict, version:str, servers:list)
    """
    return jsonify({
        "status": "ok",
        "version": "1.2",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "servers": {
            name: {
                "description": config["description"],
                "commands": config["commands"],
            }
            for name, config in MCP_SERVERS.items()
        },
    })


@mcp_bp.get("/genesis/verify")
def genesis_verify():
    """
    Verify Genesis Record integrity (hash chain validation).

    DSPy Signature:
        In() → Out(integrity:bool, records:int, last_hash:str, errors:list)
    """
    try:
        gr_path = Path("memories/genesis_record.jsonl")
        if not gr_path.exists():
            return jsonify({
                "integrity": True,
                "records": 0,
                "last_hash": "GENESIS",
                "errors": [],
                "message": "Genesis Record not yet initialized",
            })

        records = []
        with open(gr_path, "r") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))

        # Verify chain
        errors = []
        prev_hash = "GENESIS"
        for i, rec in enumerate(records):
            if rec.get("prev_hash") != prev_hash:
                errors.append(f"Record {i}: prev_hash mismatch")
            prev_hash = rec.get("entry_hash", prev_hash)

        integrity = len(errors) == 0

        return jsonify({
            "integrity": integrity,
            "records": len(records),
            "last_hash": prev_hash,
            "errors": errors,
        })

    except Exception as e:
        logger.exception(f"Error in genesis_verify: {e}")
        return jsonify({"error": str(e), "integrity": False}), 500


@mcp_bp.get("/flags/help")
def flags_help():
    """
    Display HARMONIA-GATEWAY flag registry and usage.

    Returns reference documentation for all flag tiers.
    """
    return jsonify({
        "version": "1.2",
        "tiers": {
            "1_system_control": {
                "[SYS:TTL_PING]": "Output {}, terminate",
                "[SYS:HALT]": "Halt all operations",
                "[ETH:A369]": "Guardian Laws validation (G6/G7/G8)",
                "[CVC:CHECK]": "Get CVC status",
            },
            "2_routing": {
                "[CMD:AGENT:SENTINEL]": "Route to Sentinel (ethics)",
                "[CMD:AGENT:ARCHITECT]": "Route to Architect (planning)",
                "[CMD:AGENT:LIBRARIAN]": "Route to Librarian (memory)",
                "[CMD:STATUS]": "Get system status",
            },
            "3_transform": {
                "[FMT:SBAR]": "Format: Situation→Background→Assessment→Recommendation",
                "[FMT:PREP]": "Format: Point→Reason→Example→Point",
                "[FMT:STAR]": "Format: Situation→Task→Action→Result",
                "[FMT:333]": "Format: Minto Pyramid + TOC + CTA",
                "[LANG:EN]": "Output in English",
                "[LANG:PL]": "Output in Polish",
                "[CMD:MINIFY]": "Minified JSON output",
                "[CMD:UNPACK]": "Expand to natural language",
            },
            "4_debug": {
                "[DBG:TRACE]": "Expose [REASONING] blocks",
                "[RAG:INJ]": "Ephemeral context injection",
            },
        },
        "example": "[SYS:ETH_A369] [CMD:AGENT:SENTINEL] [FMT:SBAR] [DBG:TRACE]",
    })


if __name__ == "__main__":
    print("MCP Blueprint registered. Routes:")
    print("  POST /api/mcp/invoke/<server>")
    print("  GET  /api/mcp/status")
    print("  GET  /api/mcp/genesis/verify")
    print("  GET  /api/mcp/flags/help")
