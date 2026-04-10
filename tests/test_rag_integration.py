"""
Tests for arbitrage/rag_integration.py — RAGFlow + Ollama Integration

Covers:
  - RAG Integration initialization
  - Context retrieval
  - Ollama reasoning
  - Guardian Laws ingestion
  - Trinity score enhancement
"""
import pytest
from arbitrage.rag_integration import (
    RAGIntegration,
    get_rag_integration,
    retrieve_guardian_context,
    reason_with_guardian_context,
    enhance_trinity_score,
)


class TestRAGIntegration:
    """Tests for RAG Integration."""

    def test_initialization(self):
        """Test RAG integration initialization."""
        rag = RAGIntegration()
        assert rag is not None
        assert rag.ragflow_host == "localhost"
        assert rag.ragflow_port == 9380
        assert rag.ollama_url == "http://localhost:11434"

    def test_get_singleton(self):
        """Test RAG singleton instance."""
        rag1 = get_rag_integration()
        rag2 = get_rag_integration()
        assert rag1 is rag2

    def test_retrieve_context_unavailable(self):
        """Test context retrieval when RAGFlow is unavailable."""
        rag = RAGIntegration()
        # When RAGFlow is unavailable, should return empty list
        result = rag.retrieve_context("test query")
        assert isinstance(result, list)

    def test_reason_with_context_unavailable(self):
        """Test reasoning when Ollama is unavailable."""
        rag = RAGIntegration()
        # When Ollama is unavailable, should return fallback response
        result = rag.reason_with_context("test query", [])
        assert "reasoning" in result
        assert isinstance(result, dict)

    def test_reasoning_structure(self):
        """Test that reasoning response has correct structure."""
        rag = RAGIntegration()
        result = rag.reason_with_context("ethical decision", [])

        assert "reasoning" in result
        assert "context_docs" in result
        assert isinstance(result["context_docs"], int)

    def test_enhance_intellectual_scoring(self):
        """Test Trinity score enhancement with RAG."""
        rag = RAGIntegration()

        enhanced = rag.enhance_intellectual_scoring(
            job={"type": "content writing", "title": "Blog Article"},
            analysis={"score": 8, "fit": "Good", "risks": "None"},
            base_score=0.75,
        )

        assert "base_score" in enhanced
        assert "enhanced_score" in enhanced
        assert "rag_boost" in enhanced
        assert "context_docs" in enhanced
        assert "reasoning" in enhanced
        assert "rag_available" in enhanced

        # Enhanced score should be close to base score
        assert 0 <= enhanced["enhanced_score"] <= 1.0
        assert abs(enhanced["enhanced_score"] - enhanced["base_score"]) <= 0.1

    def test_context_with_multiple_docs(self):
        """Test context handling with multiple retrieved documents."""
        rag = RAGIntegration()

        # Simulate multiple context documents
        mock_docs = [
            {"content": "Guardian Law 1: Unity"},
            {"content": "Guardian Law 2: Truth"},
        ]

        result = rag.reason_with_context("ethical evaluation", mock_docs)

        assert result["context_docs"] == 2
        assert "reasoning" in result

    def test_convenience_functions(self):
        """Test convenience wrapper functions."""
        # Test retrieve function
        context = retrieve_guardian_context("nonmaleficence", top_k=3)
        assert isinstance(context, list)

        # Test reason function
        reasoning = reason_with_guardian_context("test", context)
        assert isinstance(reasoning, dict)
        assert "reasoning" in reasoning

        # Test enhance function
        enhanced = enhance_trinity_score(
            {"type": "test"},
            {"score": 7},
            0.7,
        )
        assert isinstance(enhanced, dict)
        assert "enhanced_score" in enhanced


class TestRAGIntegrationErrorHandling:
    """Tests for RAG error handling and edge cases."""

    def test_empty_context_handling(self):
        """Test reasoning with empty context."""
        rag = RAGIntegration()
        result = rag.reason_with_context("test", [])

        assert "reasoning" in result
        assert result["context_docs"] == 0

    def test_missing_content_in_docs(self):
        """Test reasoning with malformed document structure."""
        rag = RAGIntegration()

        # Document missing 'content' key
        docs = [{"title": "Test"}]

        result = rag.reason_with_context("test", docs)

        assert isinstance(result, dict)
        assert "reasoning" in result

    def test_score_clamping(self):
        """Test that enhanced scores are clamped to [0, 1]."""
        rag = RAGIntegration()

        # Try to enhance with extreme scores
        enhanced = rag.enhance_intellectual_scoring(
            {"type": "test"},
            {"score": 10},
            1.5,  # Over-clamped score
        )

        assert 0 <= enhanced["enhanced_score"] <= 1.0
        assert 0 <= enhanced["base_score"] <= 1.0

    def test_configuration_custom_hosts(self):
        """Test RAG with custom host configuration."""
        rag = RAGIntegration(
            ragflow_host="custom-ragflow",
            ragflow_port=8080,
            ollama_url="http://custom-ollama:11434",
        )

        assert rag.ragflow_host == "custom-ragflow"
        assert rag.ragflow_port == 8080
        assert rag.ollama_url == "http://custom-ollama:11434"
