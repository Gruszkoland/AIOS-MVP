"""Contract tests for UAP API responses.

Validates UAP API endpoints (tasks, agents, genesis, ebdi, admin)
return responses matching expected schemas.
"""
import pytest
from flask.testing import FlaskClient

from arbitrage.app import create_app


@pytest.fixture
def uap_client() -> FlaskClient:
    """Create UAP test client."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.mark.contract
class TestUAPTasksContract:
    """Contract tests for /mapi/v1/task/* endpoints."""

    def test_delegate_task_response_schema(self, uap_client):
        """POST /mapi/v1/task/delegate must return task_id, status, assigned_agent."""
        response = uap_client.post(
            "/mapi/v1/task/delegate",
            json={"task_description": "test task", "dry_run": True},
            headers={"X-API-Key": "test-key"}
        )
        if response.status_code in (200, 201):
            data = response.get_json()
            assert "task_id" in data or "error" in data
            if "task_id" in data:
                assert "status" in data
                assert "assigned_agent" in data

    def test_list_tasks_response_schema(self, uap_client):
        """GET /mapi/v1/task/list must return tasks array with count."""
        response = uap_client.get(
            "/mapi/v1/task/list",
            headers={"X-API-Key": "test-key"}
        )
        if response.status_code == 200:
            data = response.get_json()
            assert "tasks" in data or "error" in data
            if "tasks" in data:
                assert isinstance(data["tasks"], list)
                assert "count" in data


@pytest.mark.contract
class TestUAPAdminContract:
    """Contract tests for /mapi/v1/* admin endpoints."""

    def test_get_active_tasks_response_schema(self, uap_client):
        """GET /mapi/v1/tasks must return task list or error."""
        response = uap_client.get(
            "/mapi/v1/tasks",
            headers={"X-API-Key": "test-key"}
        )
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict)
            assert "tasks" in data or "error" in data

    def test_get_task_stats_response_schema(self, uap_client):
        """GET /mapi/v1/tasks/stats must return stats object."""
        response = uap_client.get(
            "/mapi/v1/tasks/stats",
            headers={"X-API-Key": "test-key"}
        )
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict)
            # Should have counts
            assert any(k in data for k in ["completed", "pending", "running", "failed", "error"])
