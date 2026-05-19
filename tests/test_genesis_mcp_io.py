"""Tests for Genesis MCP file I/O: session save, log event, checkpoint create."""

import json
import os
import pytest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mcp_servers.genesis_mcp import GenesisMCP


@pytest.fixture
def genesis(tmp_path):
    """Create a GenesisMCP instance with record_path pointing to tmp_path."""
    g = GenesisMCP()
    g.record_path = str(tmp_path / "genesis_records")
    return g


class TestSaveSession:
    """Gap 2.7: handle_save_session writes JSON to disk."""

    def test_file_created_on_save(self, genesis):
        result = genesis.handle_save_session("sess-001", {"key": "value"})
        filepath = os.path.join(genesis.record_path, "sess-001.json")
        assert os.path.exists(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["session_id"] == "sess-001"
        assert data["state_data"]["key"] == "value"

    def test_save_session_result_structure(self, genesis):
        result = genesis.handle_save_session("sess-002", {"x": 1})
        assert result["success"] is True
        assert result["result"]["saved"] is True
        assert result["result"]["session_id"] == "sess-002"


class TestLogEvent:
    """Gap 2.7: handle_log_event appends to JSONL file."""

    def test_log_appended_to_file(self, genesis):
        genesis.handle_log_event("First event", level="info")
        genesis.handle_log_event("Second event", level="warning")

        log_path = os.path.join(genesis.record_path, "genesis_audit.jsonl")
        assert os.path.exists(log_path)

        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 2
        first = json.loads(lines[0])
        assert first["event"] == "First event"
        assert first["level"] == "info"

        second = json.loads(lines[1])
        assert second["event"] == "Second event"
        assert second["level"] == "warning"


class TestCheckpointCreate:
    """Gap 2.7: handle_checkpoint_create writes checkpoint JSON to disk."""

    def test_checkpoint_file_created(self, genesis):
        data = {"tasks": [1, 2, 3], "state": "snapshot"}
        genesis.handle_checkpoint_create("ckpt-001", data)

        ckpt_path = os.path.join(genesis.record_path, "checkpoints", "ckpt-001.json")
        assert os.path.exists(ckpt_path)

        with open(ckpt_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["tasks"] == [1, 2, 3]
        assert loaded["state"] == "snapshot"


class TestRagSearch:
    """Gap 2.5: handle_rag_search returns results (mock fallback when no RAG deps)."""

    def test_rag_search_returns_docs(self, genesis):
        result = genesis.handle_rag_search([0.1] * 512, top_k=3)
        assert result["success"] is True
        docs = result["result"]["docs"]
        assert len(docs) == 3
        assert docs[0]["score"] >= docs[1]["score"]  # Sorted by score desc

    def test_rag_search_reports_source(self, genesis):
        result = genesis.handle_rag_search([0.1] * 512, top_k=2)
        # Without RAG dependencies loaded, should use mock
        assert result["result"]["source"] in ("mock", "hnsw")
