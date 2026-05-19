"""
ADRION 369 — RAG Integration with RAGFlow + Ollama

Integrates Retrieval-Augmented Generation into Trinity's Intellectual Perspective.
Retrieves Guardian Laws from RAGFlow knowledge base and enriches LLM reasoning.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("adrion.rag_integration")

# ─────────────────────────────────────────────────────────────────────
# RAG Integration
# ─────────────────────────────────────────────────────────────────────


class RAGIntegration:
    """
    Retrieval-Augmented Generation integration for enhanced intelligence scoring.

    Retrieves Guardian Laws from RAGFlow knowledge base and uses Ollama
    to reason over retrieved context, improving decision quality.
    """

    def __init__(
        self,
        ragflow_host: str = "localhost",
        ragflow_port: int = 9380,
        ollama_url: str = "http://localhost:11434",
    ):
        self.ragflow_host = ragflow_host
        self.ragflow_port = ragflow_port
        self.ollama_url = ollama_url
        self.logger = logging.getLogger("adrion.rag_integration.rag")

        # Try to initialize RAGFlow and Ollama clients
        self._init_clients()

    def _init_clients(self):
        """Initialize RAGFlow and Ollama clients (with fallback if unavailable)."""
        self.ragflow_available = False
        self.ollama_available = False

        try:
            import requests

            # Test RAGFlow connectivity
            try:
                resp = requests.get(
                    f"http://{self.ragflow_host}:{self.ragflow_port}/api/health",
                    timeout=2,
                )
                self.ragflow_available = resp.status_code == 200
                self.logger.info("✓ RAGFlow available at %s:%d", self.ragflow_host, self.ragflow_port)
            except Exception as e:
                self.logger.warning("RAGFlow not available: %s", e)

            # Test Ollama connectivity
            try:
                resp = requests.get(f"{self.ollama_url}/api/models", timeout=2)
                self.ollama_available = resp.status_code == 200
                self.logger.info("✓ Ollama available at %s", self.ollama_url)
            except Exception as e:
                self.logger.warning("Ollama not available: %s", e)

        except ImportError:
            self.logger.warning("requests library not available — RAG unavailable")

    def retrieve_context(
        self,
        query: str,
        collection: str = "guardian_laws",
        top_k: int = 5,
    ) -> list[dict]:
        """
        Retrieve relevant documents from RAGFlow knowledge base.

        Args:
            query: Search query (e.g., "nonmaleficence")
            collection: Knowledge base collection name
            top_k: Number of documents to retrieve

        Returns:
            List of retrieved documents with content and metadata
        """
        if not self.ragflow_available:
            self.logger.warning("RAGFlow not available — returning empty context")
            return []

        try:
            import requests

            url = f"http://{self.ragflow_host}:{self.ragflow_port}/api/rag/search"

            payload = {
                "query": query,
                "collection": collection,
                "top_k": top_k,
            }

            resp = requests.post(url, json=payload, timeout=5)
            resp.raise_for_status()

            data = resp.json()

            if data.get("status") == "success":
                docs = data.get("documents", [])
                self.logger.debug(
                    "Retrieved %d documents for query: %s",
                    len(docs),
                    query,
                )
                return docs
            else:
                self.logger.warning("RAGFlow returned error: %s", data.get("message"))
                return []

        except Exception as e:
            self.logger.error("RAG retrieval error: %s", e)
            return []

    def reason_with_context(
        self,
        query: str,
        context_docs: list[dict],
        model: str = "deepseek-coder-v2",
    ) -> dict:
        """
        Use Ollama to reason over retrieved context.

        Args:
            query: Original question/decision point
            context_docs: Retrieved documents from RAGFlow
            model: Ollama model to use

        Returns:
            dict with reasoning text and contextual information
        """
        if not self.ollama_available:
            self.logger.warning("Ollama not available — returning default reasoning")
            return {
                "reasoning": "No RAG context available",
                "context_docs": len(context_docs),
                "context_size": 0,
            }

        try:
            import requests

            # Build context string from documents
            context_text = "\n---\n".join(
                [d.get("content", "") for d in context_docs if "content" in d]
            )

            prompt = f"""You are an expert decision-making assistant. Based on the provided context from Guardian Laws, evaluate the following decision question.

Context from Guardian Laws Knowledge Base:
{context_text}

Question: {query}

Provide a concise evaluation (1-2 sentences) considering the Guardian Laws context."""

            url = f"{self.ollama_url}/api/generate"

            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
                "top_k": 10,
                "top_p": 0.9,
            }

            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()

            data = resp.json()

            reasoning_text = data.get("response", "Unable to generate reasoning")

            self.logger.debug(
                "Generated reasoning (%d tokens)",
                data.get("eval_count", 0),
            )

            return {
                "reasoning": reasoning_text,
                "context_docs": len(context_docs),
                "context_size": len(context_text),
                "model": model,
            }

        except Exception as e:
            self.logger.error("Ollama reasoning error: %s", e)
            return {
                "reasoning": "Error generating reasoning",
                "context_docs": len(context_docs),
                "context_size": 0,
                "error": str(e),
            }

    def ingest_guardian_laws(self, collection: str = "guardian_laws") -> bool:
        """
        Ingest all 9 Guardian Laws into RAGFlow knowledge base.

        Args:
            collection: Collection name to store laws in

        Returns:
            True if successful, False otherwise
        """
        if not self.ragflow_available:
            self.logger.warning("RAGFlow not available — skipping ingestion")
            return False

        try:
            from arbitrage.guardian import GUARDIAN_LAWS
            import requests

            url = f"http://{self.ragflow_host}:{self.ragflow_port}/api/rag/ingest"

            documents = []
            for law_name, law_rule in GUARDIAN_LAWS.items():
                doc = {
                    "title": law_name.upper(),
                    "content": law_rule.description if hasattr(law_rule, "description") else str(law_rule),
                    "metadata": {
                        "type": "guardian_law",
                        "law_name": law_name,
                        "weight": str(law_rule.weight) if hasattr(law_rule, "weight") else "MEDIUM",
                    }
                }
                documents.append(doc)

            payload = {
                "collection": collection,
                "documents": documents,
            }

            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()

            data = resp.json()

            if data.get("status") == "success":
                self.logger.info(
                    "✓ Ingested %d Guardian Laws into RAGFlow collection: %s",
                    len(documents),
                    collection,
                )
                return True
            else:
                self.logger.error("Ingestion failed: %s", data.get("message"))
                return False

        except Exception as e:
            self.logger.error("Guardian Laws ingestion error: %s", e)
            return False

    def enhance_intellectual_scoring(
        self,
        job: dict,
        analysis: dict,
        base_score: float,
    ) -> dict:
        """
        Enhance intellectual scoring using RAG context.

        Args:
            job: Job data
            analysis: LLM analysis
            base_score: Base intellectual score from trinity.py

        Returns:
            dict with enhanced scoring and RAG context
        """
        # Build query from job context
        query = f"Ethical evaluation of {job.get('type', 'job')}: {job.get('title', 'untitled')}"

        # Retrieve context
        context_docs = self.retrieve_context(query, top_k=3)

        # Reason over context
        reasoning = self.reason_with_context(query, context_docs)

        # Adjust score based on RAG context
        rag_boost = 0.0

        # Positive boost if context is available and reasoning is positive
        if len(context_docs) > 0 and "positive" in reasoning["reasoning"].lower():
            rag_boost = 0.05
        elif len(context_docs) > 0 and "concern" in reasoning["reasoning"].lower():
            rag_boost = -0.05

        clamped_base_score = min(1.0, max(0.0, base_score))
        enhanced_score = min(1.0, max(0.0, clamped_base_score + rag_boost))

        return {
            "base_score": round(clamped_base_score, 4),
            "rag_boost": round(rag_boost, 4),
            "enhanced_score": round(enhanced_score, 4),
            "context_docs": len(context_docs),
            "reasoning": reasoning["reasoning"],
            "rag_available": self.ragflow_available and self.ollama_available,
        }


# Singleton instance
_rag_instance: Optional[RAGIntegration] = None


def get_rag_integration() -> RAGIntegration:
    """Get or create RAG integration singleton."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGIntegration()
    return _rag_instance


# Convenience functions
def retrieve_guardian_context(query: str, top_k: int = 5) -> list[dict]:
    """Retrieve Guardian Laws context."""
    rag = get_rag_integration()
    return rag.retrieve_context(query, top_k=top_k)


def reason_with_guardian_context(query: str, context: list[dict]) -> dict:
    """Reason over Guardian Laws context."""
    rag = get_rag_integration()
    return rag.reason_with_context(query, context)


def enhance_trinity_score(job: dict, analysis: dict, base_score: float) -> dict:
    """Enhance Trinity intellectual score with RAG."""
    rag = get_rag_integration()
    return rag.enhance_intellectual_scoring(job, analysis, base_score)
