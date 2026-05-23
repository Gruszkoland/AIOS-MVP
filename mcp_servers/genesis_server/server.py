"""Genesis MCP Server — ADRION 369.

Immutable records management with SHA-256 linked hash chain.
Port: 9004 (informational — stdio transport for VS Code MCP).

Tools (5): create_record, get_record, audit_chain, verify_integrity, export_archive
Resources (3): adrion://genesis/records, adrion://genesis/hash-chain, adrion://genesis/access-log
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any

_MCP_DIR = Path(__file__).parent.parent
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from shared import sha256_hex, utc_now  # noqa: E402

logger = logging.getLogger("adrion.genesis")

# In-memory store (SQLite-in-memory equivalent for this implementation)
_RECORDS: dict[str, dict[str, Any]] = {}
_CHAIN_HEAD: str = "GENESIS"  # Virtual genesis block hash
_CHAIN: list[dict[str, Any]] = []   # Ordered append-only chain
_ACCESS_LOG: list[dict[str, Any]] = []


def _compute_hash(record_id: str, record_type: str, data_str: str,
                  timestamp: str, prev_hash: str) -> str:
    payload = f"{record_id}|{record_type}|{data_str}|{timestamp}|{prev_hash}"
    return sha256_hex(payload)


# ---------------------------------------------------------------------------
# Business Logic
# ---------------------------------------------------------------------------
class GenesisLogic:
    """Immutable record management with SHA-256 hash chain."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}
        self._chain: list[dict[str, Any]] = []
        self._access_log: list[dict[str, Any]] = []
        self._prev_hash: str = sha256_hex("GENESIS_BLOCK")

    # -- Tools ---------------------------------------------------------------

    def create_record(self, record_type: str, data: dict[str, Any], author: str) -> dict[str, Any]:
        """Create an immutable record appended to the hash chain."""
        record_id = str(uuid.uuid4())
        timestamp = utc_now()
        data_str = json.dumps(data, sort_keys=True)
        record_hash = _compute_hash(record_id, record_type, data_str, timestamp, self._prev_hash)

        record: dict[str, Any] = {
            "record_id":   record_id,
            "type":        record_type,
            "data":        data,
            "author":      author,
            "timestamp":   timestamp,
            "prev_hash":   self._prev_hash,
            "hash":        record_hash,
        }
        self._records[record_id] = record
        chain_entry = {
            "record_id": record_id,
            "type":      record_type,
            "hash":      record_hash,
            "prev_hash": self._prev_hash,
            "timestamp": timestamp,
        }
        self._chain.append(chain_entry)
        self._prev_hash = record_hash

        logger.debug("Genesis record created: %s (type=%s)", record_id, record_type)
        return {
            "status": "ok",
            "record_id": record_id,
            "type": record_type,
            "hash": record_hash,
            "chain_length": len(self._chain),
            "timestamp": timestamp,
        }

    def get_record(self, record_id: str) -> dict[str, Any]:
        """Retrieve a record and verify its hash integrity."""
        self._access_log.append({"record_id": record_id, "action": "read", "timestamp": utc_now()})
        record = self._records.get(record_id)
        if not record:
            return {"status": "not_found", "record_id": record_id}

        # Re-compute hash to verify integrity
        data_str = json.dumps(record["data"], sort_keys=True)
        expected_hash = _compute_hash(
            record["record_id"], record["type"], data_str,
            record["timestamp"], record["prev_hash"],
        )
        integrity_ok = expected_hash == record["hash"]
        return {
            "status": "ok",
            "record_id": record_id,
            "type": record["type"],
            "author": record["author"],
            "data": record["data"],
            "hash": record["hash"],
            "integrity_ok": integrity_ok,
            "timestamp": record["timestamp"],
        }

    def audit_chain(self, record_id_prefix: str) -> dict[str, Any]:
        """Return hash chain entries matching the given record ID prefix."""
        matching = [
            e for e in self._chain
            if e["record_id"].startswith(record_id_prefix)
        ]
        return {
            "status": "ok",
            "prefix": record_id_prefix,
            "chain": matching,
            "total_in_chain": len(self._chain),
            "timestamp": utc_now(),
        }

    def verify_integrity(self, record_id: str) -> dict[str, Any]:
        """Verify that a record's hash is consistent with the chain."""
        record = self._records.get(record_id)
        if not record:
            return {"status": "not_found", "record_id": record_id, "valid": False}

        data_str = json.dumps(record["data"], sort_keys=True)
        expected = _compute_hash(
            record["record_id"], record["type"], data_str,
            record["timestamp"], record["prev_hash"],
        )
        valid = expected == record["hash"]
        return {
            "status": "ok",
            "record_id": record_id,
            "valid": valid,
            "stored_hash": record["hash"],
            "computed_hash": expected,
            "tamper_detected": not valid,
            "timestamp": utc_now(),
        }

    def export_archive(self, record_type: str, since: str | None = None) -> dict[str, Any]:
        """Export all records of a given type; include an archive checksum."""
        filtered = [
            r for r in self._records.values()
            if r["type"] == record_type
            and (since is None or r["timestamp"] >= since)
        ]
        # Compute archive hash over all record hashes (order-preserving)
        combined = "".join(r["hash"] for r in sorted(filtered, key=lambda r: r["timestamp"]))
        archive_hash = sha256_hex(combined) if combined else sha256_hex("empty")
        return {
            "status": "ok",
            "record_type": record_type,
            "since": since,
            "count": len(filtered),
            "records": [{"record_id": r["record_id"], "hash": r["hash"],
                          "timestamp": r["timestamp"], "author": r["author"]} for r in filtered],
            "archive_hash": archive_hash,
            "timestamp": utc_now(),
        }


# ---------------------------------------------------------------------------
# MCP Server Wiring
# ---------------------------------------------------------------------------
def _build_server() -> Any:
    from mcp.server import Server  # type: ignore[import-untyped]
    from mcp.types import Resource, TextContent, Tool  # type: ignore[import-untyped]

    logic = GenesisLogic()
    server = Server("adrion-genesis")

    @server.list_tools()
    async def list_tools() -> list[Tool]:  # type: ignore[return]
        return [
            Tool(name="create_record",
                 description="Create an immutable Genesis record appended to the SHA-256 hash chain.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "record_type": {"type": "string",
                                                  "enum": ["session", "audit", "decision", "report", "deployment"]},
                                  "data":        {"type": "object", "description": "Arbitrary record payload"},
                                  "author":      {"type": "string", "description": "Agent or user name"},
                              },
                              "required": ["record_type", "data", "author"]}),
            Tool(name="get_record",
                 description="Retrieve a Genesis record by ID and verify its hash integrity.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "record_id": {"type": "string"},
                              },
                              "required": ["record_id"]}),
            Tool(name="audit_chain",
                 description="Return all hash chain entries matching a record ID prefix.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "record_id_prefix": {"type": "string",
                                                       "description": "Prefix of record_id to search"},
                              },
                              "required": ["record_id_prefix"]}),
            Tool(name="verify_integrity",
                 description="Verify that a specific record's hash matches the stored value.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "record_id": {"type": "string"},
                              },
                              "required": ["record_id"]}),
            Tool(name="export_archive",
                 description="Export all records of a given type with an archive checksum.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "record_type": {"type": "string"},
                                  "since":       {"type": "string",
                                                  "description": "ISO 8601 timestamp filter (optional)"},
                              },
                              "required": ["record_type"]}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:  # type: ignore[return]
        args: dict[str, Any] = arguments or {}
        if name == "create_record":
            result = logic.create_record(args["record_type"], args.get("data", {}), args["author"])
        elif name == "get_record":
            result = logic.get_record(args["record_id"])
        elif name == "audit_chain":
            result = logic.audit_chain(args.get("record_id_prefix", ""))
        elif name == "verify_integrity":
            result = logic.verify_integrity(args["record_id"])
        elif name == "export_archive":
            result = logic.export_archive(args["record_type"], args.get("since"))
        else:
            raise ValueError(f"Unknown tool: {name}")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    @server.list_resources()
    async def list_resources() -> list[Resource]:  # type: ignore[return]
        return [
            Resource(uri="adrion://genesis/records",    # type: ignore[arg-type]
                     name="Genesis Records",
                     description="Last 50 immutable Genesis records (this session)",
                     mimeType="application/json"),
            Resource(uri="adrion://genesis/hash-chain", # type: ignore[arg-type]
                     name="Hash Chain",
                     description="Full append-only hash chain summary",
                     mimeType="application/json"),
            Resource(uri="adrion://genesis/access-log", # type: ignore[arg-type]
                     name="Access Log",
                     description="Record read/access history this session",
                     mimeType="application/json"),
        ]

    @server.read_resource()
    async def read_resource(uri: Any) -> str:  # type: ignore[return]
        uri_str = str(uri)
        if uri_str == "adrion://genesis/records":
            recent = list(logic._records.values())[-50:]
            return json.dumps({"records": recent, "total": len(logic._records)}, indent=2)
        if uri_str == "adrion://genesis/hash-chain":
            return json.dumps({"chain": logic._chain, "length": len(logic._chain)}, indent=2)
        if uri_str == "adrion://genesis/access-log":
            return json.dumps({"access_log": logic._access_log, "total": len(logic._access_log)}, indent=2)
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
    logger.info("[Genesis] MCP ready on port 9004")
    asyncio.run(main())
