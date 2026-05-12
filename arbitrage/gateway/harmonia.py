"""
HARMONIA-GATEWAY v1.2 — Semantic Compression & Flag Router

Lossless translator between n8n shorthand and ADRION 369 machine logic.
Flag Registry (GSR v1.2) with 4 tiers: System Control, Routing, Transform, Context/Debug.

Implements ADRION 369 §VII.2 (Harmonia attachment) with DSPy signatures.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class FlagTier(Enum):
    """GSR v1.2 Tier hierarchy for flag priority."""
    TIER_1_SYSTEM = 1      # System control (halt, ping, eth check)
    TIER_2_ROUTING = 2     # Agent routing (SENTINEL, ARCHITECT, LIBRARIAN)
    TIER_3_TRANSFORM = 3   # Output transformation (format, unpack, minify)
    TIER_4_DEBUG = 4       # Context and debug tracing


class OutputFormat(Enum):
    """Output formatting templates per ADRION §V."""
    SBAR = "sbar"      # Sytuacja→Tło→Ocena→Rekomendacja
    PREP = "prep"      # Punkt→Powód→Przykład→Punkt
    STAR = "star"      # Sytuacja→Zadanie→Akcja→Rezultat
    FMT_333 = "fmt_333"  # Piramida Minto + spis + CTA


# ────────────────────────────────────────────────────────────────────────────
# TIER 1 — SYSTEM CONTROL
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class SysCommand:
    """Tier 1: System-level commands (stop, halt, health check)."""
    cmd: str  # "TTL_PING" | "HALT" | "ETH_A369" | "CVC_CHECK"
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ────────────────────────────────────────────────────────────────────────────
# TIER 2 — ROUTING
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class RouterCommand:
    """Tier 2: Route to agent (SENTINEL, ARCHITECT, LIBRARIAN)."""
    agent: str  # "SENTINEL" | "ARCHITECT" | "LIBRARIAN"
    cmd: Optional[str] = None  # "status" etc.

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ────────────────────────────────────────────────────────────────────────────
# TIER 3 — TRANSFORM
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class TransformCommand:
    """Tier 3: Output transformation (format, language, compression)."""
    format: Optional[OutputFormat] = None  # SBAR | PREP | STAR | 333
    language: str = "PL"  # "PL" | "EN"
    minify: bool = False
    unpack: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.format:
            d["format"] = self.format.value
        return d


# ────────────────────────────────────────────────────────────────────────────
# TIER 4 — DEBUG
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class DebugCommand:
    """Tier 4: Debug and context injection."""
    trace: bool = False  # Expose [REASONING] block
    rag_inject: Optional[Dict[str, Any]] = None  # Ephemeral context

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ────────────────────────────────────────────────────────────────────────────
# GSR v1.2 FLAG PARSER
# ────────────────────────────────────────────────────────────────────────────

class FlagRegistry:
    """Global Shorthand Registry v1.2 — Parse and execute flags."""

    # Tier 1 System Control flags
    SYS_FLAGS = {
        "TTL_PING": SysCommand("TTL_PING"),
        "HALT": SysCommand("HALT"),
        "ETH_A369": SysCommand("ETH_A369"),
        "CVC_CHECK": SysCommand("CVC_CHECK"),
    }

    # Tier 2 Routing flags
    AGENT_FLAGS = {
        "SENTINEL": RouterCommand("SENTINEL"),
        "ARCHITECT": RouterCommand("ARCHITECT"),
        "LIBRARIAN": RouterCommand("LIBRARIAN"),
        "STATUS": RouterCommand("STATUS", cmd="status"),
    }

    # Tier 3 Transform flags
    FORMAT_FLAGS = {
        "SBAR": OutputFormat.SBAR,
        "PREP": OutputFormat.PREP,
        "STAR": OutputFormat.STAR,
        "333": OutputFormat.FMT_333,
    }

    @staticmethod
    def parse_flags(flag_string: str) -> Dict[str, Any]:
        """
        Parse shorthand flags: [SYS:HALT], [CMD:AGENT:SENTINEL], [FMT:SBAR], etc.

        DSPy Signature:
            In(flag_string: str) → Out(parsed: dict, tier: int, valid: bool)
        """
        parsed = {
            "tier_1_system": None,
            "tier_2_routing": None,
            "tier_3_transform": None,
            "tier_4_debug": None,
            "flags": [],
            "valid": True,
        }

        if not flag_string or "[" not in flag_string:
            return parsed

        # Extract all flags: [TAG:VALUE] or [TAG:SUBTAG:VALUE]
        import re
        matches = re.findall(r"\[([A-Z_0-9:]+)\]", flag_string)

        for match in matches:
            parts = match.split(":")
            tag = parts[0] if parts else ""

            # Tier 1: System
            if tag == "SYS":
                subcmd = parts[1] if len(parts) > 1 else None
                if subcmd in FlagRegistry.SYS_FLAGS:
                    parsed["tier_1_system"] = FlagRegistry.SYS_FLAGS[subcmd].to_dict()
                    parsed["flags"].append(f"SYS:{subcmd}")

            # Tier 2: Routing
            elif tag == "CMD":
                if len(parts) > 1:
                    subtag = parts[1]
                    if subtag == "AGENT" and len(parts) > 2:
                        agent = parts[2]
                        if agent in FlagRegistry.AGENT_FLAGS:
                            parsed["tier_2_routing"] = FlagRegistry.AGENT_FLAGS[agent].to_dict()
                            parsed["flags"].append(f"CMD:AGENT:{agent}")
                    elif subtag == "MINIFY":
                        if "tier_3_transform" not in parsed or parsed["tier_3_transform"] is None:
                            parsed["tier_3_transform"] = TransformCommand(minify=True).to_dict()
                        else:
                            parsed["tier_3_transform"]["minify"] = True
                        parsed["flags"].append("CMD:MINIFY")

            # Tier 3: Transform
            elif tag == "FMT":
                format_name = parts[1] if len(parts) > 1 else None
                if format_name in FlagRegistry.FORMAT_FLAGS:
                    if "tier_3_transform" not in parsed or parsed["tier_3_transform"] is None:
                        parsed["tier_3_transform"] = {}
                    parsed["tier_3_transform"]["format"] = format_name
                    parsed["flags"].append(f"FMT:{format_name}")

            elif tag == "LANG":
                lang = parts[1] if len(parts) > 1 else "PL"
                if "tier_3_transform" not in parsed or parsed["tier_3_transform"] is None:
                    parsed["tier_3_transform"] = {}
                parsed["tier_3_transform"]["language"] = lang
                parsed["flags"].append(f"LANG:{lang}")

            # Tier 4: Debug
            elif tag == "DBG":
                subcmd = parts[1] if len(parts) > 1 else None
                if subcmd == "TRACE":
                    if "tier_4_debug" not in parsed or parsed["tier_4_debug"] is None:
                        parsed["tier_4_debug"] = {}
                    parsed["tier_4_debug"]["trace"] = True
                    parsed["flags"].append("DBG:TRACE")

            elif tag == "RAG":
                if parts[1] == "INJ":
                    if "tier_4_debug" not in parsed or parsed["tier_4_debug"] is None:
                        parsed["tier_4_debug"] = {}
                    parsed["tier_4_debug"]["rag_inject"] = True
                    parsed["flags"].append("RAG:INJ")

        logger.info(f"Parsed flags: {parsed['flags']}")
        return parsed

    @staticmethod
    def priority_sort(flags: Dict[str, Any]) -> List[tuple]:
        """
        Determine execution order by tier priority (Tier 1 > Tier 2 > Tier 3 > Tier 4).

        DSPy Signature:
            In(flags: dict) → Out(order: list[(tier_num, command_dict)])
        """
        order = []
        if flags.get("tier_1_system"):
            order.append((1, flags["tier_1_system"]))
        if flags.get("tier_2_routing"):
            order.append((2, flags["tier_2_routing"]))
        if flags.get("tier_3_transform"):
            order.append((3, flags["tier_3_transform"]))
        if flags.get("tier_4_debug"):
            order.append((4, flags["tier_4_debug"]))
        return order


# ────────────────────────────────────────────────────────────────────────────
# GENESIS RECORD WRITER
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class GenesisRecord:
    """Schema for Genesis Record audit trail entry (§XII)."""
    genesis_id: str
    timestamp: str
    session_id: str
    agent: str  # "ORCHESTRATOR" | "SENTINEL" | "ARCHITECT" | "LIBRARIAN"
    action_type: str  # "DECISION" | "SAV_PASS" | "SAV_FAIL" | "TOOL_CALL" etc.
    payload: Dict[str, Any]
    prev_hash: str
    entry_hash: str

    def to_jsonl(self) -> str:
        """Serialize to JSONL format (one entry per line)."""
        return json.dumps(asdict(self))


def create_genesis_record(
    agent: str,
    action_type: str,
    payload: Dict[str, Any],
    prev_hash: str = "GENESIS",
    session_id: str = "default",
) -> GenesisRecord:
    """
    Create a new Genesis Record entry with hash chain integrity.

    DSPy Signature:
        In(agent:str, action_type:str, payload:dict, prev_hash:str, session_id:str)
        → Out(genesis_id:str, entry_hash:str, record:GenesisRecord)
    """
    import time
    genesis_id = f"GR-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{int(time.time()*1000)%1000:03d}"
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Compute entry hash: SHA256(genesis_id + timestamp + agent + payload + prev_hash)
    hash_input = (
        f"{genesis_id}{timestamp}{agent}{json.dumps(payload, sort_keys=True)}{prev_hash}"
    ).encode("utf-8")
    entry_hash = hashlib.sha256(hash_input).hexdigest()

    record = GenesisRecord(
        genesis_id=genesis_id,
        timestamp=timestamp,
        session_id=session_id,
        agent=agent,
        action_type=action_type,
        payload=payload,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
    )

    return record


# ────────────────────────────────────────────────────────────────────────────
# SELF-AUDIT PIPELINE
# ────────────────────────────────────────────────────────────────────────────

def audit_output(
    output: Dict[str, Any],
    format_spec: Optional[OutputFormat] = None,
    flags: Optional[Dict[str, Any]] = None,
) -> tuple[bool, Optional[str]]:
    """
    Self-audit before output (§E from attachment).

    DSPy Signature:
        In(output:dict, format_spec:OutputFormat|None, flags:dict|None)
        → Out(audit_pass:bool, error_msg:str|None)
    """
    checks = []

    # Check 1: Format compliance
    if format_spec and "description" not in output:
        checks.append("Missing 'description' for format compliance")

    # Check 2: No fillers (intro, meta spam)
    if isinstance(output, dict):
        forbidden_keys = ["greeting", "intro", "preamble", "meta"]
        for key in forbidden_keys:
            if key in output:
                checks.append(f"Filler key found: {key}")

    # Check 3: Guardian checks (placeholder)
    if flags and flags.get("tier_1_system", {}).get("cmd") == "ETH_A369":
        # Simulate G6/G7/G8 check
        if "sensitive_data" in str(output).lower():
            checks.append("G7 Privacy violation detected")

    if checks:
        error_msg = " | ".join(checks)
        return False, error_msg
    return True, None


if __name__ == "__main__":
    # Test flag parsing
    test_flags = "[SYS:ETH_A369] [CMD:AGENT:SENTINEL] [FMT:SBAR] [DBG:TRACE]"
    parsed = FlagRegistry.parse_flags(test_flags)
    print(json.dumps(parsed, indent=2))

    # Test Genesis Record
    rec = create_genesis_record(
        agent="SENTINEL",
        action_type="ETH_VETO",
        payload={"description": "Test action", "guardian_ref": "G7"},
    )
    print("\nGenesis Record:")
    print(rec.to_jsonl())
