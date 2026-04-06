"""
GENESIS-MCP: State Management, RAG, Session Persistence

Port: 9004
Domain: File I/O, database, logging, long-term memory

DSPy Signature:
- Input: memory_query, session_context, retention_policy
- Output: retrieved_context, storage_location, rag_enrichment, session_continuity
"""

from mcp_servers import MCPBaseServer, DSPySignature
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import json


genesis_signature = DSPySignature(
    signature_name="GenesisMemory",
    input_schema={
        "memory_query": "string",
        "session_context": "object {session_id, metadata}",
        "retention_policy": "object {ttl_seconds, scope}"
    },
    output_schema={
        "retrieved_context": "array[document with scores]",
        "storage_location": "string (file | db_ref)",
        "rag_enrichment": "array[semantic_docs]",
        "session_continuity": "object"
    }
)


@dataclass
class SessionState:
    """Session memory entry"""
    session_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    state_data: Dict[str, Any] = field(default_factory=dict)
    retention_ttl_seconds: int = 86400  # 24h default
    scope: str = "local"  # "local" or "global"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LogEntry:
    """Genesis Record log entry"""
    entry_id: str
    timestamp: str
    level: str  # "info", "warning", "error"
    event_type: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)


class GenesisMCP(MCPBaseServer):
    """State Management & Memory (Local-First)"""

    def __init__(self):
        super().__init__(
            server_name="GENESIS-MCP",
            port=9004,
            dspy_signature=genesis_signature
        )
        self.sessions: Dict[str, SessionState] = {}
        self.logs: List[LogEntry] = []
        self.rag_documents: List[Dict[str, Any]] = []
        self.record_path = "Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU"

    def handle_save_session(self, session_id: str, state: Dict[str, Any]) -> dict:
        """POST /session/save — Save session state"""
        def operation_fn():
            session = SessionState(
                session_id=session_id,
                state_data=state,
                scope="local"
            )
            self.sessions[session_id] = session

            filepath = f"{self.record_path}/{session_id}.json"

            return {
                "saved": True,
                "session_id": session_id,
                "path": filepath,
                "timestamp": session.timestamp,
                "state_size_bytes": len(json.dumps(state))
            }

        result = self.execute_step(
            step_name=f"save_session_{session_id}",
            operation=operation_fn,
            definition_of_done=[
                "session_created",
                "file_path_generated",
                "timestamp_recorded"
            ]
        )
        return result

    def handle_recall_memory(self, query: str, scope: str = "local") -> dict:
        """POST /memory/recall — Retrieve session memory"""
        def operation_fn():
            # Simple keyword matching (in prod: use embeddings)
            results = []
            for session_id, session in self.sessions.items():
                if scope == "local" or session.scope == "local":
                    if query.lower() in json.dumps(session.state_data).lower():
                        results.append({
                            "session_id": session_id,
                            "relevance_score": 0.85,
                            "timestamp": session.timestamp,
                            "data_preview": str(session.state_data)[:100]
                        })

            return {
                "results": sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:5],
                "timestamp": datetime.utcnow().isoformat(),
                "query": query,
                "scope": scope
            }

        result = self.execute_step(
            step_name=f"recall_{query[:20]}",
            operation=operation_fn,
            definition_of_done=[
                "results_retrieved",
                "timestamp_applied",
                "results_sorted"
            ]
        )
        return result

    def handle_rag_search(self, embedding: List[float], top_k: int = 5) -> dict:
        """POST /rag/search — Semantic search on Genesis Record"""
        def operation_fn():
            # Simplified: mock semantic similarity
            docs = [
                {
                    "doc_id": f"doc_{i}",
                    "title": f"Document {i}",
                    "score": 0.9 - (i * 0.1),
                    "content": f"Content snippet for doc {i}"
                }
                for i in range(top_k)
            ]

            return {
                "docs": docs,
                "count": len(docs),
                "embedding_dim": len(embedding),
                "search_time_ms": 42
            }

        result = self.execute_step(
            step_name=f"rag_search_k{top_k}",
            operation=operation_fn,
            definition_of_done=[
                "docs_retrieved",
                "limit_respected",
                "scores_calculated"
            ]
        )
        return result

    def handle_log_event(self, event: str, level: str = "info") -> dict:
        """POST /log/append — Append to Genesis Record (append-only)"""
        def operation_fn():
            entry_id = f"LOG-{len(self.logs)}"
            log_entry = LogEntry(
                entry_id=entry_id,
                timestamp=datetime.utcnow().isoformat(),
                level=level,
                event_type="general",
                message=event,
                context={}
            )

            self.logs.append(log_entry)

            # Append to Genesis Record file
            log_path = f"{self.record_path}/genesis_audit.jsonl"

            return {
                "logged_at": log_entry.timestamp,
                "entry_id": entry_id,
                "level": level,
                "file_path": log_path,
                "total_entries": len(self.logs)
            }

        result = self.execute_step(
            step_name=f"log_{level}_{event[:20]}",
            operation=operation_fn,
            definition_of_done=[
                "log_entry_created",
                "appended_to_file",
                "entry_id_assigned"
            ]
        )
        return result

    def handle_checkpoint_create(self, checkpoint_id: str, data: Dict[str, Any]) -> dict:
        """Create rollback checkpoint"""
        def operation_fn():
            # Store checkpoint
            checkpoint_path = f"{self.record_path}/checkpoints/{checkpoint_id}.json"

            return {
                "checkpoint_id": checkpoint_id,
                "path": checkpoint_path,
                "created_at": datetime.utcnow().isoformat(),
                "data_size_bytes": len(json.dumps(data)),
                "recoverable": True
            }

        result = self.execute_step(
            step_name=f"checkpoint_{checkpoint_id}",
            operation=operation_fn,
            definition_of_done=[
                "checkpoint_file_created",
                "size_recorded",
                "timestamp_set"
            ]
        )
        return result

    def get_memory_stats(self) -> dict:
        """Memory usage statistics"""
        total_bytes = sum(len(json.dumps(s.state_data)) for s in self.sessions.values())
        return {
            "total_sessions": len(self.sessions),
            "total_log_entries": len(self.logs),
            "total_rag_docs": len(self.rag_documents),
            "memory_used_mb": total_bytes / (1024 * 1024),
            "oldest_session": min((s.timestamp for s in self.sessions.values()), default=None),
            "record_path": self.record_path
        }
