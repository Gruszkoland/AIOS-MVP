"""Test suite for Global State Register (GSR) — ADRION 369.

Covers:
  - Initialization (default state structure and agent count)
  - update_agent_status: all 9 agents, validation, confidence clamping
  - get_agent_state: hit and miss
  - get_all_agents: structural integrity
  - heartbeat_check: online/offline detection
  - Metrics: active/error/idle counts
  - Persistence: dump_state / load_state roundtrip

All tests run WITHOUT the mcp SDK.
The conftest.py in this directory adds mcp-servers/ to sys.path.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest

from gsr import (
    CANONICAL_AGENT_IDS,
    DEFAULT_CONFIDENCE,
    GSR_VERSION,
    VALID_STATUSES,
    GlobalStateRegister,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def gsr() -> GlobalStateRegister:
    """Fresh GSR instance with no persistence file."""
    return GlobalStateRegister()


@pytest.fixture
def tmp_state_file(tmp_path: Path) -> Path:
    """Return a path inside pytest's tmp_path for state persistence tests."""
    return tmp_path / "PROJECT_STATE.json"


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestGSRInitialization:
    def test_all_nine_agents_registered(self, gsr: GlobalStateRegister) -> None:
        state = gsr.get_all_agents()
        assert len(state["agents"]) == 9

    def test_canonical_agent_ids_present(self, gsr: GlobalStateRegister) -> None:
        state = gsr.get_all_agents()
        expected_ids = set(CANONICAL_AGENT_IDS.keys())
        assert set(state["agents"].keys()) == expected_ids

    def test_default_version_is_3_0(self, gsr: GlobalStateRegister) -> None:
        state = gsr.get_all_agents()
        assert state["version"] == GSR_VERSION

    def test_default_all_agents_idle(self, gsr: GlobalStateRegister) -> None:
        state = gsr.get_all_agents()
        for agent_id, agent in state["agents"].items():
            assert agent["status"] == "idle", (
                f"Expected 'idle' for {agent_id}, got {agent['status']!r}"
            )

    def test_default_all_agents_full_confidence(self, gsr: GlobalStateRegister) -> None:
        state = gsr.get_all_agents()
        for agent in state["agents"].values():
            assert agent["confidence"] == DEFAULT_CONFIDENCE

    def test_default_metrics_total_is_nine(self, gsr: GlobalStateRegister) -> None:
        state = gsr.get_all_agents()
        assert state["metrics"]["total_agents"] == 9
        assert state["metrics"]["idle_agents"] == 9
        assert state["metrics"]["active_agents"] == 0
        assert state["metrics"]["error_agents"] == 0

    def test_state_has_required_top_level_keys(self, gsr: GlobalStateRegister) -> None:
        state = gsr.get_all_agents()
        assert "timestamp" in state
        assert "version" in state
        assert "agents" in state
        assert "metrics" in state
        assert "last_heartbeat" in state


# ---------------------------------------------------------------------------
# update_agent_status — per-agent and validation
# ---------------------------------------------------------------------------

class TestUpdateAgentStatus:
    @pytest.mark.parametrize("agent_id", list(CANONICAL_AGENT_IDS.keys()))
    def test_update_each_of_nine_agents(
        self, gsr: GlobalStateRegister, agent_id: str
    ) -> None:
        """Each of the 9 canonical agents can be updated independently."""
        result = gsr.update_agent_status(agent_id, "active", 75, "Running task")
        assert "error" not in result
        assert result["status"] == "active"
        assert result["confidence"] == 75
        assert result["id"] == agent_id

    def test_update_status_active(self, gsr: GlobalStateRegister) -> None:
        result = gsr.update_agent_status("MPG-01", "active", 80)
        assert result["status"] == "active"

    def test_update_status_error(self, gsr: GlobalStateRegister) -> None:
        result = gsr.update_agent_status("PAA-02", "error", 10)
        assert result["status"] == "error"

    def test_update_status_idle(self, gsr: GlobalStateRegister) -> None:
        gsr.update_agent_status("TDO-03", "active", 90)
        result = gsr.update_agent_status("TDO-03", "idle", 100)
        assert result["status"] == "idle"

    def test_invalid_status_returns_error_key(self, gsr: GlobalStateRegister) -> None:
        result = gsr.update_agent_status("MPG-01", "running", 50)
        assert "error" in result

    def test_invalid_status_message_mentions_valid_values(
        self, gsr: GlobalStateRegister
    ) -> None:
        result = gsr.update_agent_status("MPG-01", "unknown", 50)
        error_msg: str = result["error"]
        for valid in sorted(VALID_STATUSES):
            assert valid in error_msg

    def test_confidence_clamped_above_100(self, gsr: GlobalStateRegister) -> None:
        result = gsr.update_agent_status("GRA-06", "active", 999)
        assert result["confidence"] == 100

    def test_confidence_clamped_below_0(self, gsr: GlobalStateRegister) -> None:
        result = gsr.update_agent_status("GRA-06", "error", -50)
        assert result["confidence"] == 0

    def test_task_description_stored(self, gsr: GlobalStateRegister) -> None:
        gsr.update_agent_status("OCA-07", "active", 85, "Routing task to VTA-05")
        agent = gsr.get_agent_state("OCA-07")
        assert agent["last_task"] == "Routing task to VTA-05"

    def test_omitting_task_description_preserves_previous(
        self, gsr: GlobalStateRegister
    ) -> None:
        gsr.update_agent_status("KSA-08", "active", 70, "Initial task")
        gsr.update_agent_status("KSA-08", "idle", 100)  # no task_description
        agent = gsr.get_agent_state("KSA-08")
        assert agent["last_task"] == "Initial task"

    def test_update_refreshes_updated_at(self, gsr: GlobalStateRegister) -> None:
        before = gsr.get_agent_state("RIA-09")["updated_at"]
        time.sleep(0.05)
        gsr.update_agent_status("RIA-09", "active", 60)
        after = gsr.get_agent_state("RIA-09")["updated_at"]
        assert after >= before


# ---------------------------------------------------------------------------
# get_agent_state
# ---------------------------------------------------------------------------

class TestGetAgentState:
    def test_get_known_agent_returns_data(self, gsr: GlobalStateRegister) -> None:
        result = gsr.get_agent_state("MPG-01")
        assert "error" not in result
        assert result.get("status") in VALID_STATUSES
        assert result["id"] == "MPG-01"

    def test_get_unknown_agent_returns_not_found(
        self, gsr: GlobalStateRegister
    ) -> None:
        result = gsr.get_agent_state("GHOST-99")
        assert result["status"] == "not_found"
        assert result["agent_id"] == "GHOST-99"

    def test_get_all_agents_returns_deep_copy(
        self, gsr: GlobalStateRegister
    ) -> None:
        """Mutating the returned dict must not affect internal state."""
        state = gsr.get_all_agents()
        state["agents"]["MPG-01"]["status"] = "corrupted"
        fresh = gsr.get_agent_state("MPG-01")
        assert fresh["status"] != "corrupted"


# ---------------------------------------------------------------------------
# heartbeat_check
# ---------------------------------------------------------------------------

class TestHeartbeatCheck:
    def test_freshly_updated_agent_is_online(
        self, gsr: GlobalStateRegister
    ) -> None:
        gsr.update_agent_status("MPG-01", "active", 90)
        result = gsr.heartbeat_check(max_age_seconds=300)
        assert "MPG-01" in result["online"]

    def test_stale_agent_is_offline(self, gsr: GlobalStateRegister) -> None:
        """Manually backdate an agent's updated_at to simulate staleness."""
        stale_time = (
            datetime.now(timezone.utc) - timedelta(seconds=600)
        ).isoformat()
        with gsr._lock:
            gsr._state["agents"]["VTA-05"]["updated_at"] = stale_time
        result = gsr.heartbeat_check(max_age_seconds=300)
        assert "VTA-05" in result["offline"]

    def test_heartbeat_returns_correct_totals(
        self, gsr: GlobalStateRegister
    ) -> None:
        result = gsr.heartbeat_check(max_age_seconds=300)
        total = len(result["online"]) + len(result["offline"])
        assert total == 9

    def test_heartbeat_persists_in_state(self, gsr: GlobalStateRegister) -> None:
        gsr.heartbeat_check(max_age_seconds=300)
        state = gsr.get_all_agents()
        assert "online_agents" in state["last_heartbeat"]
        assert "offline_agents" in state["last_heartbeat"]

    def test_heartbeat_invalid_timestamp_counts_as_offline(
        self, gsr: GlobalStateRegister
    ) -> None:
        with gsr._lock:
            gsr._state["agents"]["AUA-04"]["updated_at"] = "not-a-timestamp"
        result = gsr.heartbeat_check(max_age_seconds=300)
        assert "AUA-04" in result["offline"]


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class TestMetrics:
    def test_metrics_counts_active_agents(self, gsr: GlobalStateRegister) -> None:
        gsr.update_agent_status("MPG-01", "active", 80)
        gsr.update_agent_status("PAA-02", "active", 75)
        state = gsr.get_all_agents()
        assert state["metrics"]["active_agents"] == 2

    def test_metrics_counts_error_agents(self, gsr: GlobalStateRegister) -> None:
        gsr.update_agent_status("TDO-03", "error", 20)
        state = gsr.get_all_agents()
        assert state["metrics"]["error_agents"] == 1

    def test_metrics_idle_count_decreases_on_activation(
        self, gsr: GlobalStateRegister
    ) -> None:
        gsr.update_agent_status("GRA-06", "active", 95)
        state = gsr.get_all_agents()
        assert state["metrics"]["idle_agents"] == 8
        assert state["metrics"]["active_agents"] == 1

    def test_metrics_total_always_nine(self, gsr: GlobalStateRegister) -> None:
        gsr.update_agent_status("OCA-07", "active", 85)
        gsr.update_agent_status("KSA-08", "error", 5)
        state = gsr.get_all_agents()
        m = state["metrics"]
        assert m["idle_agents"] + m["active_agents"] + m["error_agents"] == 9


# ---------------------------------------------------------------------------
# Persistence — dump_state / load_state
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_dump_creates_file(
        self, gsr: GlobalStateRegister, tmp_state_file: Path
    ) -> None:
        gsr.dump_state(tmp_state_file)
        assert tmp_state_file.exists()

    def test_dump_produces_valid_json(
        self, gsr: GlobalStateRegister, tmp_state_file: Path
    ) -> None:
        gsr.dump_state(tmp_state_file)
        with open(tmp_state_file) as fh:
            data = json.load(fh)
        assert "agents" in data
        assert "version" in data

    def test_dump_load_roundtrip_preserves_agent_status(
        self, tmp_state_file: Path
    ) -> None:
        """Update an agent, dump, reload in fresh GSR, verify state survived."""
        gsr_a = GlobalStateRegister()
        gsr_a.update_agent_status("RIA-09", "active", 42, "Deploying v2")
        gsr_a.dump_state(tmp_state_file)

        gsr_b = GlobalStateRegister()
        gsr_b.load_state(tmp_state_file)
        state = gsr_b.get_agent_state("RIA-09")
        assert state["status"] == "active"
        assert state["confidence"] == 42
        assert state["last_task"] == "Deploying v2"

    def test_dump_load_roundtrip_preserves_metrics(
        self, tmp_state_file: Path
    ) -> None:
        gsr_a = GlobalStateRegister()
        gsr_a.update_agent_status("MPG-01", "active", 80)
        gsr_a.update_agent_status("PAA-02", "error", 10)
        gsr_a.dump_state(tmp_state_file)

        gsr_b = GlobalStateRegister()
        gsr_b.load_state(tmp_state_file)
        state = gsr_b.get_all_agents()
        assert state["metrics"]["active_agents"] == 1
        assert state["metrics"]["error_agents"] == 1

    def test_dump_no_filepath_raises_value_error(
        self, gsr: GlobalStateRegister
    ) -> None:
        with pytest.raises(ValueError, match="No filepath"):
            gsr.dump_state()

    def test_load_nonexistent_file_raises_file_not_found(
        self, gsr: GlobalStateRegister, tmp_state_file: Path
    ) -> None:
        with pytest.raises(FileNotFoundError):
            gsr.load_state(tmp_state_file)

    def test_construction_with_filepath_autoloads_existing_state(
        self, tmp_state_file: Path
    ) -> None:
        gsr_a = GlobalStateRegister()
        gsr_a.update_agent_status("VTA-05", "active", 88, "Running tests")
        gsr_a.dump_state(tmp_state_file)

        gsr_b = GlobalStateRegister(state_filepath=tmp_state_file)
        agent = gsr_b.get_agent_state("VTA-05")
        assert agent["status"] == "active"
        assert agent["last_task"] == "Running tests"
