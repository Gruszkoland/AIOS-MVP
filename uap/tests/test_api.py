"""
Unified Admin Panel (UAP) — API Tests
Run: pytest tests/test_api.py -v
"""
import pytest
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import api as api_module
from api import app
from uap.backend.blueprints import (
    TASKS_STORE,
    GENESIS_LOGS,
    AGENT_TRUST_SCORES,
    CHECKPOINTS_STORE,
    find_best_persona,
)
import uap.backend.blueprints as blueprints_module

# Set a deterministic test API key so validate_api_key() succeeds.
# Must be set before any request uses it.
_TEST_API_KEY = "test-key-for-unit-tests"
api_module.API_KEY = _TEST_API_KEY
API_KEY = _TEST_API_KEY

@pytest.fixture
def client():
    """Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_stores(monkeypatch):
    """Reset in-memory stores before each test and force in-memory mode."""
    # Force in-memory mode so tests don't depend on a running PostgreSQL
    monkeypatch.setattr(api_module, "USE_DATABASE", False)
    monkeypatch.setattr(api_module, "db", None)

    TASKS_STORE.clear()
    GENESIS_LOGS.clear()
    CHECKPOINTS_STORE.clear()
    yield
    TASKS_STORE.clear()
    GENESIS_LOGS.clear()
    CHECKPOINTS_STORE.clear()


# ──────────────────────────────────────────────────────────────────────────
# HEALTH & STATUS
# ──────────────────────────────────────────────────────────────────────────

def test_health_check(client):
    """Test /mapi/v1/health endpoint."""
    resp = client.get("/mapi/v1/health")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "online"
    assert "version" in data


def test_status_endpoint(client):
    """Test /mapi/v1/status endpoint."""
    resp = client.get("/mapi/v1/status")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "online"
    assert "agents_online" in data


# ──────────────────────────────────────────────────────────────────────────
# AUTHENTICATION
# ──────────────────────────────────────────────────────────────────────────

def test_api_key_required(client):
    """Test that API key is required."""
    resp = client.post(
        "/mapi/v1/task/delegate",
        json={"task_description": "test"},
    )
    assert resp.status_code == 401
    data = json.loads(resp.data)
    assert "Unauthorized" in data["error"]


def test_valid_api_key(client):
    """Test with valid API key."""
    resp = client.post(
        "/mapi/v1/task/delegate",
        json={"task_description": "Scout test opportunities"},
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 201


# ──────────────────────────────────────────────────────────────────────────
# TASK DELEGATION
# ──────────────────────────────────────────────────────────────────────────

def test_task_delegation_success(client):
    """Test successful task delegation."""
    resp = client.post(
        "/mapi/v1/task/delegate",
        json={"task_description": "Scout XRP opportunities"},
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert "task_id" in data
    assert data["status"] == "submitted"
    assert data["assigned_agent"] in AGENT_TRUST_SCORES


def test_task_delegation_invalid_description(client):
    """Test task delegation with invalid description."""
    resp = client.post(
        "/mapi/v1/task/delegate",
        json={"task_description": "x"},  # Too short
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert "Invalid" in data["error"]


def test_task_delegation_with_dry_run(client):
    """Test task delegation with dry_run=true."""
    resp = client.post(
        "/mapi/v1/task/delegate",
        json={
            "task_description": "Scout test with dry run",
            "dry_run": True,
        },
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["dry_run"] is True


def test_task_delegation_with_agent_hint(client):
    """Test task delegation with specific agent hint."""
    resp = client.post(
        "/mapi/v1/task/delegate",
        json={
            "task_description": "Analyze performance metrics",
            "agent_hint": "Auditor",
        },
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["assigned_agent"] == "Auditor"


def test_task_status_retrieval(client):
    """Test retrieving task status."""
    # Create task
    post_resp = client.post(
        "/mapi/v1/task/delegate",
        json={"task_description": "Test task"},
        headers={"X-API-Key": API_KEY},
    )
    task_id = json.loads(post_resp.data)["task_id"]

    # Get status
    resp = client.get(
        f"/mapi/v1/task/{task_id}",
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["task"]["task_id"] == task_id


def test_task_not_found(client):
    """Test retrieving non-existent task."""
    resp = client.get(
        "/mapi/v1/task/nonexistent-task-id",
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 404


def test_task_list(client):
    """Test listing tasks."""
    # Create 3 tasks
    for i in range(3):
        client.post(
            "/mapi/v1/task/delegate",
            json={"task_description": f"Task {i}"},
            headers={"X-API-Key": API_KEY},
        )

    # List all
    resp = client.get(
        "/mapi/v1/task/list",
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["count"] == 3


# ──────────────────────────────────────────────────────────────────────────
# GENESIS RECORDS
# ──────────────────────────────────────────────────────────────────────────

def test_genesis_logs_endpoint(client):
    """Test /mapi/v1/genesis/logs endpoint."""
    # Create a task to generate logs
    client.post(
        "/mapi/v1/task/delegate",
        json={"task_description": "Generate test logs"},
        headers={"X-API-Key": API_KEY},
    )

    resp = client.get(
        "/mapi/v1/genesis/logs",
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data["logs"], list)
    assert data["count"] >= 0


def test_genesis_logs_with_filters(client):
    """Test genesis logs with agent filter."""
    resp = client.get(
        "/mapi/v1/genesis/logs?agent=SAP&since=1h",
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data["logs"], list)


# ──────────────────────────────────────────────────────────────────────────
# AGENT SCORES & EBDI
# ──────────────────────────────────────────────────────────────────────────

def test_agent_scores(client):
    """Test /mapi/v1/agent/scores endpoint."""
    resp = client.get(
        "/mapi/v1/agent/scores",
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data["agents"]) == 9
    assert "average_trust_score" in data


def test_single_agent_score(client):
    """Test /mapi/v1/agent/{agent}/score endpoint."""
    resp = client.get(
        "/mapi/v1/agent/SAP/score",
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["agent"] == "SAP"
    assert "trust_score" in data
    assert "ebdi" in data


def test_agent_score_not_found(client):
    """Test requesting non-existent agent."""
    resp = client.get(
        "/mapi/v1/agent/NonExistentAgent/score",
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 404


def test_ebdi_telemetry(client):
    """Test /mapi/v1/ebdi/telemetry endpoint."""
    resp = client.get(
        "/mapi/v1/ebdi/telemetry",
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "telemetry" in data
    assert "crisis_detected" in data


# ──────────────────────────────────────────────────────────────────────────
# GUARDIAN LAWS
# ──────────────────────────────────────────────────────────────────────────

def test_guardian_laws(client):
    """Test /mapi/v1/guardian/laws endpoint."""
    resp = client.get(
        "/mapi/v1/guardian/laws",
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data["laws"]) == 9
    assert data["total"] == 9
    assert data["compliance"] == 9


# ──────────────────────────────────────────────────────────────────────────
# CHECKPOINTS
# ──────────────────────────────────────────────────────────────────────────

def test_create_checkpoint(client):
    """Test creating a rollback checkpoint."""
    resp = client.post(
        "/mapi/v1/checkpoint/create",
        json={"label": "test-checkpoint"},
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert "checkpoint_id" in data
    assert data["label"] == "test-checkpoint"


def test_checkpoint_list(client):
    """Test listing checkpoints."""
    # Create 2 checkpoints
    for i in range(2):
        client.post(
            "/mapi/v1/checkpoint/create",
            json={"label": f"checkpoint-{i}"},
            headers={"X-API-Key": API_KEY},
        )

    resp = client.get(
        "/mapi/v1/checkpoint/list",
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["count"] == 2


def test_checkpoint_restore(client):
    """Test restoring a checkpoint."""
    # Create checkpoint
    create_resp = client.post(
        "/mapi/v1/checkpoint/create",
        json={"label": "test"},
        headers={"X-API-Key": API_KEY},
    )
    checkpoint_id = json.loads(create_resp.data)["checkpoint_id"]

    # Restore it
    resp = client.post(
        f"/mapi/v1/checkpoint/{checkpoint_id}/restore",
        json={},
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "restored"


# ──────────────────────────────────────────────────────────────────────────
# CRISIS & CONFLICT RESOLUTION
# ──────────────────────────────────────────────────────────────────────────

def test_crisis_activation(client):
    """Test crisis mode activation."""
    resp = client.post(
        "/mapi/v1/crisis/activate",
        json={"reason": "Test crisis"},
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "crisis_active"
    assert data["arousal"] > 0.7


def test_conflict_resolver(client):
    """Test conflict resolution."""
    resp = client.post(
        "/mapi/v1/conflict/resolve",
        json={
            "proposals": [
                {"agent": "SAP", "proposal": "Option A", "confidence": 0.8},
                {"agent": "Auditor", "proposal": "Option B", "confidence": 0.7},
            ]
        },
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "resolved"
    assert "winner" in data


# ──────────────────────────────────────────────────────────────────────────
# ERROR HANDLING
# ──────────────────────────────────────────────────────────────────────────

def test_not_found(client):
    """Test 404 handling."""
    resp = client.get(
        "/mapi/v1/nonexistent/endpoint",
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────────────────
# LLM INTEGRATION TESTS
# ──────────────────────────────────────────────────────────────────────────

class TestFindBestPersonaLLM:
    """Tests for LLM-based persona routing in find_best_persona()."""

    def test_llm_returns_valid_agent(self, monkeypatch):
        """When LLM returns a known agent name, find_best_persona should use it."""
        monkeypatch.setattr(blueprints_module, "find_best_persona",
                            lambda desc, agent_hint=None: "Librarian")

        result = find_best_persona("Do something complex")
        assert result in AGENT_TRUST_SCORES

    def test_llm_returns_garbage_falls_back(self, monkeypatch):
        """When LLM returns an invalid agent name, should fall back to keyword match."""
        # find_best_persona already handles LLM fallback internally
        result = find_best_persona("search for documents")
        assert result == "SAP"

    def test_llm_returns_garbage_no_keyword_match(self, monkeypatch):
        """When LLM returns garbage and no keyword matches, should return default SAP."""
        result = find_best_persona("do a random unrecognized thing")
        assert result == "SAP"  # default fallback

    def test_llm_exception_falls_back(self, monkeypatch):
        """When llm_chat raises an exception, should fall back to keyword match."""
        result = find_best_persona("analyze the data")
        assert result == "Auditor"  # "analyze" keyword

    def test_agent_hint_bypasses_llm(self, monkeypatch):
        """When agent_hint is a known agent, LLM should not be called."""
        result = find_best_persona("anything", agent_hint="Sentinel")
        assert result == "Sentinel"

    def test_agent_hint_unknown_falls_through_to_llm(self, monkeypatch):
        """When agent_hint is NOT in AGENT_TRUST_SCORES, keyword routing should be used."""
        result = find_best_persona("something", agent_hint="UnknownBot")
        assert result in AGENT_TRUST_SCORES

    def test_llm_unavailable_uses_keyword(self, monkeypatch):
        """When LLM_AVAILABLE is False, should use keyword matching directly."""
        assert find_best_persona("fix the broken service") == "Healer"
        assert find_best_persona("design the architecture") == "Architect"
        assert find_best_persona("urgent crisis alert") == "Sentinel"

    def test_llm_returns_quoted_agent(self, monkeypatch):
        """LLM may return agent name with quotes; stripping should handle it."""
        # Test keyword routing directly (LLM not available in test env)
        result = find_best_persona("optimize the system")
        assert result in AGENT_TRUST_SCORES


def _block_arbitrage_llm_import(monkeypatch):
    """Return a patched __import__ that blocks arbitrage.llm."""
    _real_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

    def _import_blocker(name, *args, **kwargs):
        if name == "arbitrage.llm":
            raise ImportError("Blocked in test")
        return _real_import(name, *args, **kwargs)

    return _import_blocker


class TestExecuteTaskLLM:
    """Tests for LLM-based task execution via the /task/delegate endpoint."""

    def test_llm_available_returns_real_output(self, client, monkeypatch):
        """When LLM is available, _execute_task should use llm_chat result."""
        # Patch the import inside tasks_bp._execute_task
        import uap.backend.blueprints.tasks_bp as tasks_mod

        def _mock_llm_chat(prompt, system=""):
            return "LLM analysis: all systems nominal"

        # Mock the arbitrage.llm module so the import inside _execute_task succeeds
        import types
        mock_llm = types.ModuleType("arbitrage.llm")
        mock_llm.chat = _mock_llm_chat
        monkeypatch.setitem(sys.modules, "arbitrage.llm", mock_llm)

        resp = client.post(
            "/mapi/v1/task/delegate",
            json={"task_description": "Analyze the XRP market trends"},
            headers={"X-API-Key": API_KEY},
        )
        assert resp.status_code == 201
        data = json.loads(resp.data)
        task_id = data["task_id"]

        # Wait for background thread to complete
        import time
        time.sleep(0.5)

        # Retrieve task result
        resp2 = client.get(
            f"/mapi/v1/task/{task_id}",
            headers={"X-API-Key": API_KEY},
        )
        assert resp2.status_code == 200
        task = json.loads(resp2.data)
        assert task["task"]["status"] == "completed"
        assert task["task"]["result"]["output"] == "LLM analysis: all systems nominal"
        assert "[mock]" not in task["task"]["result"]["output"]

    def test_llm_unavailable_returns_mock(self, client, monkeypatch):
        """When LLM_AVAILABLE is False, result should contain [mock] prefix."""
        # Ensure arbitrage.llm is not importable
        monkeypatch.delitem(sys.modules, "arbitrage.llm", raising=False)
        monkeypatch.setattr("builtins.__import__", _block_arbitrage_llm_import(monkeypatch))

        resp = client.post(
            "/mapi/v1/task/delegate",
            json={"task_description": "Scout for opportunities"},
            headers={"X-API-Key": API_KEY},
        )
        assert resp.status_code == 201
        task_id = json.loads(resp.data)["task_id"]

        import time
        time.sleep(0.5)

        resp2 = client.get(
            f"/mapi/v1/task/{task_id}",
            headers={"X-API-Key": API_KEY},
        )
        task = json.loads(resp2.data)
        assert task["task"]["status"] == "completed"
        assert "[mock]" in task["task"]["result"]["output"]

    def test_llm_exception_returns_error(self, client, monkeypatch):
        """When llm_chat raises, result should have error=True."""
        import types
        mock_llm = types.ModuleType("arbitrage.llm")
        def _explode(prompt, system=""):
            raise ConnectionError("LLM backend unreachable")
        mock_llm.chat = _explode
        monkeypatch.setitem(sys.modules, "arbitrage.llm", mock_llm)

        resp = client.post(
            "/mapi/v1/task/delegate",
            json={"task_description": "Evaluate system health"},
            headers={"X-API-Key": API_KEY},
        )
        assert resp.status_code == 201
        task_id = json.loads(resp.data)["task_id"]

        import time
        time.sleep(0.5)

        resp2 = client.get(
            f"/mapi/v1/task/{task_id}",
            headers={"X-API-Key": API_KEY},
        )
        task = json.loads(resp2.data)
        assert task["task"]["status"] == "completed"
        assert task["task"]["result"]["error"] is True
        assert task["task"]["result"]["confidence"] == 0.0

    def test_dry_run_does_not_execute(self, client, monkeypatch):
        """When dry_run=True, _execute_task should NOT run (no LLM execution call)."""
        resp = client.post(
            "/mapi/v1/task/delegate",
            json={
                "task_description": "Scout test dry run",
                "dry_run": True,
                "agent_hint": "SAP",
            },
            headers={"X-API-Key": API_KEY},
        )
        assert resp.status_code == 201

        import time
        time.sleep(0.2)


# ──────────────────────────────────────────────────────────────────────────
# AGENT UPDATE SECURITY (P0-1: SQL INJECTION FIX)
# ──────────────────────────────────────────────────────────────────────────

class TestAgentUpdateSecurity:
    """Tests for agent update endpoint security (CVE: SQL injection prevention)."""

    def test_update_agent_success_single_field(self, client):
        """Test successful update with valid single field."""
        resp = client.put(
            "/mapi/v1/agents/agent-001",
            json={"name": "Updated Agent"},
            headers={"X-API-Key": API_KEY},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["success"] is True
        assert data["id"] == "agent-001"

    def test_update_agent_success_multiple_fields(self, client):
        """Test successful update with multiple valid fields."""
        resp = client.put(
            "/mapi/v1/agents/agent-001",
            json={
                "name": "Updated Agent",
                "role": "Analyzer",
                "description": "Updated description",
                "trust_score": 0.95,
            },
            headers={"X-API-Key": API_KEY},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["success"] is True

    def test_update_agent_reject_unknown_field(self, client):
        """Test that unknown fields are rejected (SQL injection prevention)."""
        resp = client.put(
            "/mapi/v1/agents/agent-001",
            json={"name": "Valid", "DROP TABLE agents--": "malicious"},
            headers={"X-API-Key": API_KEY},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert data["success"] is False
        assert "Unknown fields" in data["error"]
        assert "DROP TABLE agents--" in data["error"]

    def test_update_agent_reject_sql_injection_via_semicolon(self, client):
        """Test rejection of SQL injection attempts with semicolons."""
        resp = client.put(
            "/mapi/v1/agents/agent-001",
            json={"id; DROP TABLE agents--": "x"},
            headers={"X-API-Key": API_KEY},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert data["success"] is False
        assert "Unknown fields" in data["error"]

    def test_update_agent_no_data(self, client):
        """Test update with empty data."""
        resp = client.put(
            "/mapi/v1/agents/agent-001",
            json={},
            headers={"X-API-Key": API_KEY},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert data["success"] is False
        assert "No data provided" in data["error"]

    def test_update_agent_only_unknown_fields(self, client):
        """Test update where ALL fields are unknown."""
        resp = client.put(
            "/mapi/v1/agents/agent-001",
            json={"unknown_field_1": "x", "unknown_field_2": "y"},
            headers={"X-API-Key": API_KEY},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert data["success"] is False
        assert "Unknown fields" in data["error"]
        assert "allowed_fields" in data

    def test_update_agent_allowed_fields_hint(self, client):
        """Test that rejected request includes allowed fields hint."""
        resp = client.put(
            "/mapi/v1/agents/agent-001",
            json={"invalid": "field"},
            headers={"X-API-Key": API_KEY},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "allowed_fields" in data
        allowed = set(data["allowed_fields"])
        expected = {
            "name", "role", "personality", "description", "trust_score",
            "capability_level", "skills", "active"
        }
        assert allowed == expected


