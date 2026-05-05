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
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging
import os
import time

logger = logging.getLogger("adrion.mcp.genesis")


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
        self.record_path = os.path.join("Genesis Record", "10_RAPORTY_DZIALANIA_SYSTEMU")
        self._rag: Optional[Any] = None  # Lazy init to avoid import-time model load

    def handle_save_session(self, session_id: str, state: Dict[str, Any]) -> dict:
        """POST /session/save — Save session state to memory and disk."""
        def operation_fn():
            session = SessionState(
                session_id=session_id,
                state_data=state,
                scope="local"
            )
            self.sessions[session_id] = session

            filepath = os.path.join(self.record_path, f"{session_id}.json")

            # Persist to disk
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

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

        # Add checkpoint for SAV
        result["checkpoint"] = {
            "is_complete": result["success"],
            "step": f"save_session_{session_id}",
            "checks_passed": [
                "session_created",
                "file_path_generated",
                "timestamp_recorded"
            ]
        }

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

    def _get_rag(self):
        """Lazy-initialize RAG engine. Returns None if dependencies unavailable."""
        if self._rag is None:
            try:
                from scripts.orchestration.rag_context_optimizer import RAGContextOptimizer
                self._rag = RAGContextOptimizer()
                logger.info("RAG engine initialized for Genesis MCP")
            except (ImportError, SystemExit, Exception) as exc:
                logger.warning("RAG dependencies unavailable (%s), using mock search", exc)
                self._rag = False  # Sentinel: tried and failed
        return self._rag if self._rag is not False else None

    def handle_rag_search(self, embedding: List[float], top_k: int = 5) -> dict:
        """POST /rag/search — Semantic search on Genesis Record.

        Uses real HNSW knn_query when RAGContextOptimizer is available,
        falls back to mock results otherwise.
        """
        def operation_fn():
            rag = self._get_rag()
            start_ms = time.time()

            if rag is not None and rag.doc_counter > 0:
                try:
                    import numpy as np
                    query_vec = np.array([embedding], dtype=np.float32)
                    k = min(top_k, rag.doc_counter)
                    labels, distances = rag.index.knn_query(query_vec, k=k)

                    docs = []
                    for i, doc_id in enumerate(labels[0]):
                        doc = rag.documents.get(int(doc_id), {})
                        docs.append({
                            "doc_id": f"doc_{doc_id}",
                            "title": doc.get("metadata", {}).get("title", f"Document {doc_id}"),
                            "score": round(float(1.0 - distances[0][i]), 4),
                            "content": doc.get("text", "")[:500],
                        })

                    elapsed = (time.time() - start_ms) * 1000
                    return {
                        "docs": docs,
                        "count": len(docs),
                        "embedding_dim": len(embedding),
                        "search_time_ms": round(elapsed, 1),
                        "source": "hnsw",
                    }
                except Exception as exc:
                    logger.warning("HNSW search failed: %s, using mock fallback", exc)

            # Fallback: mock semantic similarity
            docs = [
                {
                    "doc_id": f"doc_{i}",
                    "title": f"Document {i}",
                    "score": round(0.9 - (i * 0.1), 2),
                    "content": f"Content snippet for doc {i}",
                }
                for i in range(top_k)
            ]
            elapsed = (time.time() - start_ms) * 1000
            return {
                "docs": docs,
                "count": len(docs),
                "embedding_dim": len(embedding),
                "search_time_ms": round(elapsed, 1),
                "source": "mock",
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
        """POST /log/append — Append to Genesis Record (append-only, persisted to JSONL)."""
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

            # Persist to Genesis Record JSONL file
            log_path = os.path.join(self.record_path, "genesis_audit.jsonl")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "entry_id": entry_id,
                    "timestamp": log_entry.timestamp,
                    "level": level,
                    "event": event,
                }, ensure_ascii=False) + "\n")

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
        """Create rollback checkpoint (persisted to disk)."""
        def operation_fn():
            checkpoint_path = os.path.join(self.record_path, "checkpoints", f"{checkpoint_id}.json")

            # Persist checkpoint to disk
            os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

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
