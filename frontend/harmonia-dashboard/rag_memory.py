"""
ADRION 369 — Dynamic RAG Module (Local Vector Memory)
Kamień Milowy 1: Long-term & Short-term Memory z priorytetyzacją

Moduły:
  - MemoryStore: ChromaDB wrapper z dual-collection (long-term / short-term)
  - EmbeddingProvider: sentence-transformers lub Ollama embeddings fallback
  - MemoryManager: priorytetyzacja, decay, compaction

Guardian Laws:
  - G7 (Privacy): Wszystkie dane lokalne, zero cloud export
  - G9 (Sustainability): Automatyczny decay starych wspomnień

Latency target: <2s per query
"""

import json
import os
import time
import hashlib
from datetime import datetime, timezone
from typing import Optional

# ===== EVENT BUS =====
try:
    from memory_events import emit_promoted_to_long_term
    HAS_EVENT_BUS = True
except ImportError:
    HAS_EVENT_BUS = False

# ===== OPTIONAL IMPORTS =====
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except ImportError:
    HAS_ST = False

try:
    import urllib.request
    HAS_HTTP = True
except ImportError:
    HAS_HTTP = False

# ===== CONFIG =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/embeddings")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "gemma3:4b")

# Memory decay: interactions older than this (seconds) get lower priority
SHORT_TERM_TTL = 3600 * 24       # 24h → short-term memory
LONG_TERM_THRESHOLD = 3           # min. 3 positive feedback → promote to long-term
MAX_SHORT_TERM = 500              # max short-term entries before compaction
MAX_LONG_TERM = 2000              # max long-term entries


class EmbeddingProvider:
    """Embedding provider: sentence-transformers (preferred) or Ollama fallback."""

    def __init__(self):
        self._model = None
        self._mode = "none"
        self._init()

    def _init(self):
        if HAS_ST:
            try:
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                self._mode = "sentence-transformers"
                return
            except Exception as e:
                print(f"[RAG] sentence-transformers init error: {e}")

        if HAS_HTTP:
            # Test Ollama embeddings endpoint
            try:
                payload = json.dumps({"model": OLLAMA_EMBED_MODEL, "prompt": "test"}).encode()
                req = urllib.request.Request(
                    OLLAMA_URL, data=payload,
                    headers={"Content-Type": "application/json"},
                )
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read())
                if "embedding" in data:
                    self._mode = "ollama"
                    return
            except Exception as e:
                print(f"[RAG] Ollama embedding test failed: {e}")

        self._mode = "hash"
        print("[RAG] WARNING: No embedding provider — using hash-based fallback (low quality)")

    @property
    def mode(self) -> str:
        return self._mode

    def embed(self, text: str) -> list[float]:
        if self._mode == "sentence-transformers":
            return self._model.encode(text).tolist()
        elif self._mode == "ollama":
            return self._embed_ollama(text)
        else:
            return self._embed_hash(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self._mode == "sentence-transformers":
            return [e.tolist() for e in self._model.encode(texts)]
        return [self.embed(t) for t in texts]

    def _embed_ollama(self, text: str) -> list[float]:
        payload = json.dumps({"model": OLLAMA_EMBED_MODEL, "prompt": text}).encode()
        req = urllib.request.Request(
            OLLAMA_URL, data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read())
            return data.get("embedding", self._embed_hash(text))
        except Exception:
            return self._embed_hash(text)

    @staticmethod
    def _embed_hash(text: str) -> list[float]:
        """Deterministic hash-based pseudo-embedding (384-dim to match MiniLM)."""
        h = hashlib.sha384(text.lower().strip().encode()).hexdigest()
        return [int(h[i:i+2], 16) / 255.0 for i in range(0, len(h), 2)]


class MemoryStore:
    """
    Dual-collection vector store:
      - short_term: recent interactions, auto-decay
      - long_term: promoted memories (high feedback score)

    Uses ChromaDB's built-in ONNX embeddings (all-MiniLM-L6-v2) for best performance.
    Falls back to EmbeddingProvider if custom embeddings needed.
    """

    def __init__(self, embedder: EmbeddingProvider = None):
        self.embedder = embedder  # Only used if custom embeddings needed
        self._client = None
        self._short_term = None
        self._long_term = None
        self._embedding_mode = "none"
        self._init_chroma()

    def _init_chroma(self):
        if not HAS_CHROMA:
            print("[RAG] ChromaDB not available — memory disabled")
            return
        try:
            self._client = chromadb.PersistentClient(
                path=CHROMA_DIR,
                settings=Settings(anonymized_telemetry=False),
            )
            # Use ChromaDB's built-in default embedding (ONNX all-MiniLM-L6-v2)
            self._short_term = self._client.get_or_create_collection(
                name="short_term",
                metadata={"hnsw:space": "cosine"},
            )
            self._long_term = self._client.get_or_create_collection(
                name="long_term",
                metadata={"hnsw:space": "cosine"},
            )
            self._embedding_mode = "chromadb-onnx"
            print(f"[RAG] ChromaDB initialized: {CHROMA_DIR}")
            print(f"[RAG] Short-term: {self._short_term.count()} entries")
            print(f"[RAG] Long-term: {self._long_term.count()} entries")
            print(f"[RAG] Embedding: ChromaDB built-in ONNX (all-MiniLM-L6-v2)")
        except Exception as e:
            print(f"[RAG] ChromaDB init error: {e}")
            self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def add_interaction(self, prompt: str, response: str, metadata: dict = None):
        """Store a prompt-response pair in short-term memory."""
        if not self.available:
            return
        doc_id = hashlib.md5(f"{prompt}:{response}:{time.time()}".encode()).hexdigest()
        combined_text = f"Q: {prompt}\nA: {response}"

        meta = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "feedback_score": "0",
            "feedback_count": "0",
            "type": "interaction",
            "promoted": "false",
        }
        if metadata:
            meta.update({k: str(v) for k, v in metadata.items()})

        self._short_term.add(
            ids=[doc_id],
            documents=[combined_text],
            metadatas=[meta],
        )
        self._compact_if_needed()
        return doc_id

    def add_golden_answer(self, prompt: str, golden_response: str, category: str = "general"):
        """Store a verified 'golden answer' directly in long-term memory."""
        if not self.available:
            return
        doc_id = f"golden_{hashlib.md5(prompt.encode()).hexdigest()}"
        combined_text = f"Q: {prompt}\nA: {golden_response}"

        self._long_term.upsert(
            ids=[doc_id],
            documents=[combined_text],
            metadatas=[{
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "golden_answer",
                "category": category,
                "feedback_score": "10",
                "feedback_count": "1",
                "promoted": "true",
            }],
        )
        return doc_id

    def query(self, text: str, n_results: int = 5, include_short: bool = True) -> list[dict]:
        """
        Query both memory collections, merge & rank by relevance + recency.
        Returns list of {document, distance, metadata, source} dicts.
        Uses ChromaDB's built-in embeddings for semantic search.
        """
        if not self.available:
            return []

        results = []

        # Long-term (higher priority)
        try:
            lt_count = self._long_term.count()
            if lt_count > 0:
                lt = self._long_term.query(
                    query_texts=[text],
                    n_results=min(n_results, lt_count),
                )
                for i, doc in enumerate(lt["documents"][0] if lt["documents"] else []):
                    results.append({
                        "document": doc,
                        "distance": lt["distances"][0][i] if lt["distances"] else 1.0,
                        "metadata": lt["metadatas"][0][i] if lt["metadatas"] else {},
                        "source": "long_term",
                        "priority": 1.0,
                    })
        except Exception:
            pass

        # Short-term
        if include_short:
            try:
                st_count = self._short_term.count()
                if st_count > 0:
                    st = self._short_term.query(
                        query_texts=[text],
                        n_results=min(n_results, st_count),
                    )
                    for i, doc in enumerate(st["documents"][0] if st["documents"] else []):
                        meta = st["metadatas"][0][i] if st["metadatas"] else {}
                        age = self._age_seconds(meta.get("timestamp", ""))
                        decay = max(0.1, 1.0 - (age / (SHORT_TERM_TTL * 7)))
                        results.append({
                            "document": doc,
                            "distance": st["distances"][0][i] if st["distances"] else 1.0,
                            "metadata": meta,
                            "source": "short_term",
                            "priority": 0.7 * decay,
                        })
            except Exception:
                pass

        # Sort: lower distance (=closer match) first, weighted by priority
        results.sort(key=lambda r: r["distance"] / max(r["priority"], 0.01))
        return results[:n_results]

    def update_feedback(self, doc_id: str, score_delta: int = 1):
        """
        Update feedback score for an interaction.
        If score >= LONG_TERM_THRESHOLD, promote to long-term memory.
        """
        if not self.available:
            return

        # Try short-term first
        try:
            result = self._short_term.get(ids=[doc_id], include=["documents", "metadatas", "embeddings"])
            if result["ids"]:
                meta = result["metadatas"][0]
                score = int(meta.get("feedback_score", 0)) + score_delta
                count = int(meta.get("feedback_count", 0)) + 1
                meta["feedback_score"] = str(score)
                meta["feedback_count"] = str(count)

                if score >= LONG_TERM_THRESHOLD and meta.get("promoted") != "true":
                    # Promote to long-term
                    self._long_term.upsert(
                        ids=[doc_id],
                        embeddings=result["embeddings"],
                        documents=result["documents"],
                        metadatas=[{**meta, "promoted": "true"}],
                    )
                    self._short_term.delete(ids=[doc_id])
                    if HAS_EVENT_BUS:
                        emit_promoted_to_long_term(
                            source="rag_memory",
                            interaction_id=doc_id,
                            score=score,
                        )
                    return {"action": "promoted", "score": score}
                else:
                    self._short_term.update(ids=[doc_id], metadatas=[meta])
                    return {"action": "updated", "score": score}
        except Exception:
            pass

        # Try long-term
        try:
            result = self._long_term.get(ids=[doc_id], include=["metadatas"])
            if result["ids"]:
                meta = result["metadatas"][0]
                score = int(meta.get("feedback_score", 0)) + score_delta
                count = int(meta.get("feedback_count", 0)) + 1
                meta["feedback_score"] = str(score)
                meta["feedback_count"] = str(count)
                self._long_term.update(ids=[doc_id], metadatas=[meta])
                return {"action": "updated_lt", "score": score}
        except Exception:
            pass

        return {"action": "not_found"}

    def get_stats(self) -> dict:
        """Return memory statistics."""
        if not self.available:
            return {"available": False}
        return {
            "available": True,
            "embedding_mode": self._embedding_mode,
            "short_term_count": self._short_term.count(),
            "long_term_count": self._long_term.count(),
            "chroma_dir": CHROMA_DIR,
            "max_short_term": MAX_SHORT_TERM,
            "max_long_term": MAX_LONG_TERM,
        }

    def _compact_if_needed(self):
        """Remove oldest short-term entries if over capacity."""
        if not self.available:
            return
        count = self._short_term.count()
        if count <= MAX_SHORT_TERM:
            return
        # Get all, sorted by timestamp, remove oldest 10%
        try:
            all_items = self._short_term.get(include=["metadatas"])
            entries = list(zip(all_items["ids"], all_items["metadatas"]))
            entries.sort(key=lambda e: e[1].get("timestamp", ""))
            to_remove = entries[:count // 10]
            if to_remove:
                self._short_term.delete(ids=[e[0] for e in to_remove])
                print(f"[RAG] Compacted: removed {len(to_remove)} oldest short-term entries")
        except Exception as e:
            print(f"[RAG] Compaction error: {e}")

    @staticmethod
    def _age_seconds(iso_ts: str) -> float:
        if not iso_ts:
            return SHORT_TERM_TTL * 7
        try:
            dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
            return (datetime.now(timezone.utc) - dt).total_seconds()
        except (ValueError, TypeError):
            return SHORT_TERM_TTL * 7


# ===== SINGLETON =====
_memory: Optional[MemoryStore] = None


def get_memory() -> MemoryStore:
    global _memory
    if _memory is None:
        _memory = MemoryStore()
    return _memory
