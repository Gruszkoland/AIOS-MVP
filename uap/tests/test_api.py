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

from api import app, API_KEY, TASKS_STORE, GENESIS_LOGS, AGENT_TRUST_SCORES
import api as api_module

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
    api_module.CHECKPOINTS_STORE.clear()
    yield
    TASKS_STORE.clear()
    GENESIS_LOGS.clear()
    api_module.CHECKPOINTS_STORE.clear()


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
    assert data["task_id"] == task_id


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
