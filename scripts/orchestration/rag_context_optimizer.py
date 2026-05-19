#!/usr/bin/env python3
"""
ADRION 369: RAG Context Optimizer
Retrieval-Augmented Generation system to compress context window
Used by Context Window Manager (CWM) [5] in copilot-instructions.md

Features:
- HNSW-based semantic search
- Map-Reduce summarization
- Token budget enforcement
- Relevance ranking
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple
import logging
from datetime import datetime

try:
    import hnswlib
    import numpy as np
except ImportError:
    print("❌ ERROR: hnswlib not installed. Run: pip install hnswlib numpy")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("❌ ERROR: sentence-transformers not installed. Run: pip install sentence-transformers")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


class RAGContextOptimizer:
    """
    Optimizes context window using Retrieval-Augmented Generation.

    Workflow:
    1. Embed incoming task → vector
    2. Search history embeddings (HNSW index) → find k most relevant docs
    3. Concatenate relevant docs → respect token budget
    4. Return compressed context
    """

    def __init__(self,
                 embedding_model: str = "sentence-transformers/distiluse-base-multilingual-v2",
                 max_context_tokens: int = 50000,
                 index_dim: int = 512,
                 max_neighbors: int = 10):
        """
        Initialize RAG optimizer.

        Args:
            embedding_model: HuggingFace model name for embeddings
            max_context_tokens: Maximum tokens for output context
            index_dim: Embedding dimension
            max_neighbors: Max documents to retrieve
        """
        self.embedding_model = SentenceTransformer(embedding_model)
        self.max_context_tokens = max_context_tokens
        self.index_dim = index_dim
        self.max_neighbors = max_neighbors

        # HNSW index for semantic search
        self.index = hnswlib.Index(space='cosine', dim=index_dim)
        self.index.init_index(max_elements=100000, ef_construction=200, M=16)

        # Document store
        self.documents = {}  # {doc_id: {"text": ..., "metadata": ...}}
        self.doc_counter = 0

        logger.info(f"RAG initialized: model={embedding_model}, max_tokens={max_context_tokens}")

    def add_document(self, text: str, metadata: Dict = None) -> int:
        """Add document to index."""
        doc_id = self.doc_counter

        # Embed
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)

        # Add to HNSW
        self.index.add_items(np.array([embedding]), np.array([doc_id]))

        # Store
        self.documents[doc_id] = {
            "text": text,
            "metadata": metadata or {},
            "timestamp": datetime.now(),
            "token_count": self._count_tokens(text)
        }

        self.doc_counter += 1
        return doc_id

    def get_relevant_context(self, task: str, top_k: int = None) -> str:
        """
        Retrieve most relevant documents and assemble context within token budget.

        Args:
            task: User task/query
            top_k: Number of documents to consider (default: max_neighbors)

        Returns:
            Compressed context string respecting token budget
        """
        if not self.documents:
            logger.warning("No documents in index. Returning empty context.")
            return ""

        top_k = top_k or self.max_neighbors

        # Embed task
        task_embedding = self.embedding_model.encode(task, convert_to_numpy=True)

        # Search HNSW
        labels, distances = self.index.knn_query(np.array([task_embedding]), k=top_k)
        doc_ids = labels[0]

        # Retrieve documents
        relevant_docs = []
        for doc_id in doc_ids:
            doc = self.documents[int(doc_id)]
            relevant_docs.append({
                "id": doc_id,
                "text": doc["text"],
                "score": 1 - distances[0][list(doc_ids).index(doc_id)],  # cosine similarity
                "tokens": doc["token_count"]
            })

        # Sort by relevance
        relevant_docs.sort(key=lambda x: x["score"], reverse=True)

        # Assemble context within budget
        context_parts = []
        token_budget = self.max_context_tokens

        for doc in relevant_docs:
            if doc["tokens"] <= token_budget:
                context_parts.append(doc["text"])
                token_budget -= doc["tokens"]
            else:
                # Truncate to fit
                truncated = self._truncate_to_tokens(doc["text"], token_budget)
                if truncated:
                    context_parts.append(truncated)
                break

        context = "\n\n---\n\n".join(context_parts)

        logger.info(f"RAG: Selected {len(context_parts)} docs, {len(context.split())} words")
        return context

    def map_reduce_summarize(self, text: str, chunk_size: int = 1000, depth: int = 2) -> str:
        """
        Map-Reduce based summarization for long texts.

        Recursively summarizes by breaking text into chunks,
        summarizing each chunk, then summarizing summaries.
        """
        if len(text) <= chunk_size:
            return self._summarize_chunk(text)

        # MAP: Break into chunks
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i+chunk_size])

        # Summarize each chunk
        summaries = [self._summarize_chunk(chunk) for chunk in chunks]

        # REDUCE: Recursively summarize summaries
        combined = "\n\n".join(summaries)

        if depth > 1 and len(combined) > chunk_size:
            return self.map_reduce_summarize(combined, chunk_size=chunk_size, depth=depth-1)
        else:
            return self._summarize_chunk(combined)

    def _summarize_chunk(self, text: str) -> str:
        """Summarize a single chunk (placeholder - use LLM in production)."""
        # In production: call LLM API (OpenAI, Anthropic, etc.)
        # For now: extractive summary (first 30% of text)
        words = text.split()
        target_words = max(3, len(words) // 3)
        return " ".join(words[:target_words])

    def _count_tokens(self, text: str) -> int:
        """Estimate token count (roughly 1 token per 1.3 words)."""
        return int(len(text.split()) / 1.3)

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to approximately max_tokens."""
        words = text.split()
        target_words = int(max_tokens * 1.3)
        return " ".join(words[:target_words])

    def stats(self) -> Dict:
        """Return optimizer statistics."""
        total_tokens = sum(doc["token_count"] for doc in self.documents.values())
        avg_tokens = total_tokens / len(self.documents) if self.documents else 0

        return {
            "num_documents": len(self.documents),
            "total_tokens_stored": total_tokens,
            "avg_tokens_per_doc": avg_tokens,
            "max_context_budget": self.max_context_tokens,
            "compression_ratio": total_tokens / self.max_context_tokens if self.max_context_tokens > 0 else 0
        }


class ContextWindowManager:
    """
    Wrapper for CWM [5] that uses RAG to manage context window.
    Integration point with copilot-instructions.md
    """

    def __init__(self):
        self.rag = RAGContextOptimizer()
        self.session_history = []

    def add_session_event(self, event_type: str, content: str, tokens: int):
        """Log session event (used for context optimization)."""
        self.session_history.append({
            "type": event_type,
            "content": content,
            "tokens": tokens,
            "timestamp": datetime.now()
        })

        # Add to RAG for future retrieval
        self.rag.add_document(content, metadata={"type": event_type, "tokens": tokens})

    def get_compressed_context(self, task: str) -> Tuple[str, Dict]:
        """
        Get optimized context for task.

        Returns:
            (context_string, stats_dict)
        """
        context = self.rag.get_relevant_context(task)
        stats = self.rag.stats()

        return context, stats


if __name__ == "__main__":
    # Demo usage
    logger.info("Starting RAG Context Optimizer demo...")

    optimizer = RAGContextOptimizer()

    # Add sample documents
    docs = [
        "Agent Librarian: Retrieves indexed knowledge from databases",
        "Agent SAP: Strategic Analysis Planner for task decomposition",
        "Agent Auditor: Verifies compliance with Guardian Laws",
        "Agent Sentinel: Monitors system health and anomalies",
        "Agent Architect: Designs system solutions",
        "Agent Healer: Performs self-repair diagnostics",
        "Guardian Law G1 (Unity): Maintains system coherence",
        "Guardian Law G7 (Privacy): Ensures local-first data handling"
    ]

    for doc in docs:
        optimizer.add_document(doc)

    # Query
    task = "Which agent verifies system rules?"
    context = optimizer.get_relevant_context(task, top_k=3)

    print(f"\n[TASK]: {task}")
    print(f"[CONTEXT]:\n{context}")
    print(f"\n[STATS]: {optimizer.stats()}")
