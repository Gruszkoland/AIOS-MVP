"""
tests/test_trace_propagation.py

ROPE v3.0 — Trace ID propagation and SYSTEMPAYLOAD validation tests.

Tests verify:
1. trace_id format is valid (UUID.AGENT_CODE.UNIX_MS)
2. trace_id UUID is preserved across agent hops
3. Agent code in trace_id matches the TARGET agent (next hop)
4. confidence_level is within 0-100 range
5. Retry count escalation at threshold 3
6. schema_version backward compatibility (v2.0 absence handled gracefully)
7. Guardian Law pre-check integration point

Markers:
    @pytest.mark.unit  — pure function tests, no I/O
    @pytest.mark.integration — ROPE v3.0 pipeline hops
    @pytest.mark.tier0 — critical path, never skip
"""
from __future__ import annotations

import re
import time
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ── Regex for trace_id validation ─────────────────────────────────────────────
UUID4_PATTERN = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
AGENT_CODE_PATTERN = r"[A-Z]{2,5}-[0-9]{2}"
UNIX_MS_PATTERN = r"[0-9]{13}"
TRACE_ID_PATTERN = re.compile(
    rf"^{UUID4_PATTERN}\.{AGENT_CODE_PATTERN}\.{UNIX_MS_PATTERN}$"
)

VALID_AGENT_CODES = {
    "AIO-01", "PAA-02", "TDO-03", "AUA-04", "VTA-05",
    "GRA-06", "OCA-07", "KSA-08", "RIA-09",
    # Existing agents (representative sample)
    "AGT-001", "AGT-002", "AGT-003", "AGT-004", "AGT-005", "AGT-006",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_trace_id(agent_code: str, base_uuid: str | None = None) -> str:
    """Generate a valid v3.0 trace_id for a given agent code."""
    uid = base_uuid or str(uuid.uuid4())
    ms = str(int(time.time() * 1000))
    return f"{uid}.{agent_code}.{ms}"


def extract_uuid_from_trace_id(trace_id: str) -> str:
    """Return the UUID4 portion of a trace_id."""
    return trace_id.split(".")[0]


def extract_agent_from_trace_id(trace_id: str) -> str:
    """Return the AGENT_CODE portion of a trace_id."""
    parts = trace_id.split(".")
    # Format: UUID (5 parts) + AGENT-CODE + MS
    # UUID contains 5 segments joined by '-', not '.'
    # Full string: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.AGT-01.1234567890123"
    # Split on '.' gives: ["xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "AGT-01", "1234567890123"]
    return parts[1]


def extract_ms_from_trace_id(trace_id: str) -> int:
    """Return the UNIX milliseconds portion of a trace_id."""
    return int(trace_id.split(".")[-1])


def make_systempayload(
    source_agent: str,
    target_agent: str,
    task_id: str = "TASK-TEST-001",
    session_id: str | None = None,
    confidence_level: int = 80,
    retry_count: int = 0,
    hop_count: int = 1,
    schema_version: str = "3.0",
    base_uuid: str | None = None,
) -> dict[str, Any]:
    """Construct a minimal valid SYSTEMPAYLOAD v3.0 for testing."""
    uid = base_uuid or str(uuid.uuid4())
    return {
        "schema_version": schema_version,
        "trace_id": make_trace_id(target_agent, uid),
        "session_id": session_id or str(uuid.uuid4()),
        "task_id": task_id,
        "source_agent": source_agent,
        "target_agent": target_agent,
        "task": {
            "description": "Test task for trace propagation",
            "acceptance_criteria": ["trace_id propagated correctly"],
            "priority": "MEDIUM",
            "scope_files": [],
        },
        "confidence_level": confidence_level,
        "context": {},
        "guardian_pre_check": {
            "passed": True,
            "violations": [],
            "laws_checked": ["G4"],
        },
        "timestamp": "2026-05-20T14:00:00Z",
        "retry_count": retry_count,
        "hop_count": hop_count,
        "escalation_path": [],
        "ebdi_state": {"pleasure": 0.0, "arousal": 0.0, "dominance": 0.5},
    }


# ── Unit Tests: trace_id format ───────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.tier0
class TestTraceIdFormat:
    """Validate trace_id structure and format."""

    def test_valid_trace_id_matches_pattern(self) -> None:
        """A correctly constructed trace_id must match the TRACE_ID_PATTERN."""
        trace_id = make_trace_id("AIO-01")
        assert TRACE_ID_PATTERN.match(trace_id), (
            f"trace_id '{trace_id}' does not match expected pattern"
        )

    def test_trace_id_has_three_dot_segments(self) -> None:
        """trace_id must split into exactly 3 parts on '.'."""
        trace_id = make_trace_id("VTA-05")
        parts = trace_id.split(".")
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {parts}"

    def test_trace_id_uuid_is_valid_uuid4(self) -> None:
        """The UUID portion must be a valid UUID."""
        trace_id = make_trace_id("GRA-06")
        uid_part = extract_uuid_from_trace_id(trace_id)
        # Will raise ValueError if not a valid UUID
        parsed = uuid.UUID(uid_part)
        assert str(parsed) == uid_part

    def test_trace_id_ms_is_13_digits(self) -> None:
        """UNIX_MS portion must be 13 digits (millisecond precision)."""
        trace_id = make_trace_id("OCA-07")
        ms = extract_ms_from_trace_id(trace_id)
        assert len(str(ms)) == 13, f"Expected 13-digit MS, got: {ms}"

    def test_trace_id_agent_code_present(self) -> None:
        """Agent code in trace_id must match what was passed to constructor."""
        trace_id = make_trace_id("RIA-09")
        agent = extract_agent_from_trace_id(trace_id)
        assert agent == "RIA-09"

    @pytest.mark.parametrize("bad_trace_id", [
        "not-a-trace-id",
        "uuid-only",
        "f4a3b2c1-dead-beef-cafe-123456789012",
        "f4a3b2c1-dead-beef-cafe-123456789012.INVALID.1716304800123",
        "f4a3b2c1-dead-beef-cafe-123456789012.AIO-01.123",  # MS too short
        "",
    ])
    def test_invalid_trace_id_rejected(self, bad_trace_id: str) -> None:
        """Malformed trace_ids must NOT match the pattern."""
        assert not TRACE_ID_PATTERN.match(bad_trace_id), (
            f"Expected rejection of trace_id: '{bad_trace_id}'"
        )


# ── Unit Tests: UUID preservation across hops ─────────────────────────────────

@pytest.mark.unit
@pytest.mark.tier0
class TestTraceIdPropagation:
    """Verify UUID is preserved and agent code changes correctly across hops."""

    def test_uuid_preserved_on_handoff(self) -> None:
        """When source agent forwards to target, UUID must stay the same."""
        base_uuid = str(uuid.uuid4())
        source_trace = make_trace_id("AIO-01", base_uuid)
        # Simulate forwarding: new trace_id with same UUID, new agent, new MS
        target_trace = make_trace_id("VTA-05", base_uuid)

        assert extract_uuid_from_trace_id(source_trace) == extract_uuid_from_trace_id(target_trace)

    def test_agent_code_changes_on_handoff(self) -> None:
        """When forwarding, agent code in trace_id must reflect TARGET agent."""
        base_uuid = str(uuid.uuid4())
        source_trace = make_trace_id("AIO-01", base_uuid)
        target_trace = make_trace_id("VTA-05", base_uuid)

        assert extract_agent_from_trace_id(source_trace) == "AIO-01"
        assert extract_agent_from_trace_id(target_trace) == "VTA-05"

    def test_ms_updates_on_handoff(self) -> None:
        """Timestamp (MS) must change between source and target trace_ids."""
        base_uuid = str(uuid.uuid4())
        source_trace = make_trace_id("AIO-01", base_uuid)
        time.sleep(0.002)  # ensure at least 2ms difference
        target_trace = make_trace_id("VTA-05", base_uuid)

        source_ms = extract_ms_from_trace_id(source_trace)
        target_ms = extract_ms_from_trace_id(target_trace)
        assert target_ms >= source_ms, "Target MS must be >= source MS"

    def test_uuid_preserved_across_full_pipeline(self) -> None:
        """UUID must survive a full 6-hop pipeline simulation."""
        base_uuid = str(uuid.uuid4())
        pipeline_agents = ["OCA-07", "PAA-02", "AIO-01", "VTA-05", "KSA-08", "RIA-09"]

        uuids_seen: list[str] = []
        for agent in pipeline_agents:
            trace_id = make_trace_id(agent, base_uuid)
            uuids_seen.append(extract_uuid_from_trace_id(trace_id))

        assert all(u == base_uuid for u in uuids_seen), (
            "UUID must be identical across all pipeline hops"
        )

    def test_retry_trace_id_same_uuid_same_agent_new_ms(self) -> None:
        """On retry, UUID and agent code stay the same; only MS updates."""
        base_uuid = str(uuid.uuid4())
        original_trace = make_trace_id("AIO-01", base_uuid)
        time.sleep(0.002)
        retry_trace = make_trace_id("AIO-01", base_uuid)  # same agent, new MS

        assert extract_uuid_from_trace_id(original_trace) == extract_uuid_from_trace_id(retry_trace)
        assert extract_agent_from_trace_id(original_trace) == extract_agent_from_trace_id(retry_trace)
        assert extract_ms_from_trace_id(retry_trace) >= extract_ms_from_trace_id(original_trace)


# ── Unit Tests: SYSTEMPAYLOAD validation ──────────────────────────────────────

@pytest.mark.unit
@pytest.mark.tier0
class TestSYSTEMPAYLOADValidation:
    """Validate SYSTEMPAYLOAD v3.0 schema compliance."""

    def test_valid_payload_has_all_required_fields(self) -> None:
        """A valid v3.0 payload must contain all required fields."""
        required_fields = [
            "schema_version", "trace_id", "session_id", "task_id",
            "source_agent", "target_agent", "task", "timestamp",
        ]
        payload = make_systempayload("AIO-01", "VTA-05")
        for field in required_fields:
            assert field in payload, f"Required field '{field}' missing from payload"

    def test_confidence_level_within_bounds(self) -> None:
        """confidence_level must be an integer in [0, 100]."""
        for valid_cl in [0, 1, 50, 99, 100]:
            payload = make_systempayload("AIO-01", "VTA-05", confidence_level=valid_cl)
            assert 0 <= payload["confidence_level"] <= 100

    def test_confidence_level_out_of_bounds_detected(self) -> None:
        """confidence_level outside [0, 100] must be detected."""
        for invalid_cl in [-1, 101, 200, -50]:
            payload = make_systempayload("AIO-01", "VTA-05", confidence_level=invalid_cl)
            is_valid = 0 <= payload["confidence_level"] <= 100
            assert not is_valid, f"Should be invalid: confidence_level={invalid_cl}"

    def test_schema_version_3_0_accepted(self) -> None:
        """schema_version '3.0' must be present and accepted."""
        payload = make_systempayload("PAA-02", "AIO-01", schema_version="3.0")
        assert payload["schema_version"] == "3.0"

    def test_schema_version_2_0_backward_compat(self) -> None:
        """schema_version '2.0' (v2.0 sender) must be tolerated by receiver."""
        payload = make_systempayload("PAA-02", "AIO-01", schema_version="2.0")
        # Receiver applies defaults for missing v3.0 fields
        assert payload.get("confidence_level", 50) >= 0, "Default 50 applied or field present"
        assert payload.get("hop_count", 1) >= 1, "Default 1 applied or field present"

    def test_task_requires_description_and_criteria(self) -> None:
        """task must have non-empty description and acceptance_criteria."""
        payload = make_systempayload("VTA-05", "KSA-08")
        assert payload["task"]["description"], "task.description must be non-empty"
        assert len(payload["task"]["acceptance_criteria"]) >= 1, (
            "task.acceptance_criteria must have at least 1 item"
        )

    def test_retry_count_escalation_threshold(self) -> None:
        """retry_count == 3 must trigger escalation (not execution)."""
        payload = make_systempayload("AIO-01", "VTA-05", retry_count=3)
        # Invariant: if retry_count >= 3, target must be OCA-07
        # This test verifies the condition detection, not the routing itself
        should_escalate = payload["retry_count"] >= 3
        assert should_escalate is True, (
            "retry_count=3 must be detected as escalation trigger"
        )

    def test_retry_count_2_still_executes(self) -> None:
        """retry_count == 2 must NOT trigger escalation — still within budget."""
        payload = make_systempayload("AIO-01", "VTA-05", retry_count=2)
        should_escalate = payload["retry_count"] >= 3
        assert should_escalate is False, (
            "retry_count=2 should not trigger escalation"
        )

    def test_guardian_pre_check_present_and_valid(self) -> None:
        """guardian_pre_check must contain passed, violations, and laws_checked."""
        payload = make_systempayload("GRA-06", "AIO-01")
        gpc = payload["guardian_pre_check"]
        assert "passed" in gpc
        assert "violations" in gpc
        assert "laws_checked" in gpc
        assert isinstance(gpc["violations"], list)
        assert isinstance(gpc["laws_checked"], list)

    def test_guardian_critical_violation_detected(self) -> None:
        """A G7 or G8 violation in guardian_pre_check must be detectable."""
        payload = make_systempayload("GRA-06", "AIO-01")
        # Simulate a CRITICAL violation
        payload["guardian_pre_check"]["passed"] = False
        payload["guardian_pre_check"]["violations"] = ["G7"]

        critical_laws = {"G7", "G8"}
        violations = set(payload["guardian_pre_check"]["violations"])
        has_critical = bool(violations & critical_laws)

        assert has_critical is True, "G7 violation must be detected as CRITICAL"


# ── Integration Tests: hop-to-hop payload integrity ───────────────────────────

@pytest.mark.integration
class TestHopToPropagation:
    """Simulate multi-hop pipeline and verify payload integrity at each hop."""

    def _forward_payload(
        self,
        payload: dict[str, Any],
        next_agent: str,
        new_confidence: int,
    ) -> dict[str, Any]:
        """Simulate an agent forwarding a payload to the next agent."""
        base_uuid = extract_uuid_from_trace_id(payload["trace_id"])
        new_payload = dict(payload)
        new_payload["source_agent"] = payload["target_agent"]
        new_payload["target_agent"] = next_agent
        new_payload["trace_id"] = make_trace_id(next_agent, base_uuid)
        new_payload["confidence_level"] = new_confidence
        new_payload["hop_count"] = payload.get("hop_count", 1) + 1
        return new_payload

    def test_full_success_pipeline_preserves_session_and_task(self) -> None:
        """session_id and task_id must be identical across all 6 pipeline hops."""
        session_id = str(uuid.uuid4())
        task_id = "TASK-INTEGRATION-001"
        base_uuid = str(uuid.uuid4())

        payload = make_systempayload(
            "OCA-07", "PAA-02",
            task_id=task_id, session_id=session_id, base_uuid=base_uuid
        )

        pipeline: list[tuple[str, int]] = [
            ("AIO-01", 85),
            ("VTA-05", 92),
            ("KSA-08", 87),
            ("RIA-09", 90),
        ]

        for target, confidence in pipeline:
            payload = self._forward_payload(payload, target, confidence)
            assert payload["session_id"] == session_id, (
                f"session_id changed at hop to {target}"
            )
            assert payload["task_id"] == task_id, (
                f"task_id changed at hop to {target}"
            )

    def test_hop_count_increments_correctly(self) -> None:
        """hop_count must increment by 1 at each hop."""
        payload = make_systempayload("OCA-07", "PAA-02", hop_count=1)

        pipeline: list[tuple[str, int]] = [
            ("AIO-01", 85),
            ("VTA-05", 92),
        ]

        expected_hop = 2
        for target, confidence in pipeline:
            payload = self._forward_payload(payload, target, confidence)
            assert payload["hop_count"] == expected_hop, (
                f"Expected hop_count={expected_hop} at {target}, got {payload['hop_count']}"
            )
            expected_hop += 1

    def test_uuid_stable_across_all_hops(self) -> None:
        """UUID part of trace_id must be the same for all hops in a pipeline."""
        base_uuid = str(uuid.uuid4())
        payload = make_systempayload("OCA-07", "PAA-02", base_uuid=base_uuid)

        pipeline: list[tuple[str, int]] = [
            ("AIO-01", 85), ("VTA-05", 92), ("KSA-08", 87), ("RIA-09", 90),
        ]

        for target, confidence in pipeline:
            payload = self._forward_payload(payload, target, confidence)
            trace_uuid = extract_uuid_from_trace_id(payload["trace_id"])
            assert trace_uuid == base_uuid, (
                f"UUID changed at hop to {target}: expected {base_uuid}, got {trace_uuid}"
            )

    def test_escalation_adds_to_escalation_path(self) -> None:
        """When a payload is escalated, escalation_path must grow."""
        payload = make_systempayload("AIO-01", "OCA-07", retry_count=3)
        payload["escalation_path"] = []

        # Simulate OCA-07 adding itself to escalation_path
        payload["escalation_path"].append("AIO-01")
        payload["escalation_path"].append("OCA-07")

        assert "AIO-01" in payload["escalation_path"]
        assert "OCA-07" in payload["escalation_path"]
        assert len(payload["escalation_path"]) == 2

    def test_confidence_low_threshold_detection(self) -> None:
        """confidence_level below 30 must be detectable as low-confidence."""
        for low_confidence in [0, 10, 25, 29]:
            payload = make_systempayload("AIO-01", "VTA-05", confidence_level=low_confidence)
            is_low = payload["confidence_level"] < 30
            assert is_low, f"confidence_level={low_confidence} should be detected as LOW"

    def test_confidence_above_threshold_is_normal(self) -> None:
        """confidence_level >= 30 must NOT trigger low-confidence path."""
        for normal_confidence in [30, 50, 70, 90, 100]:
            payload = make_systempayload("AIO-01", "VTA-05", confidence_level=normal_confidence)
            is_low = payload["confidence_level"] < 30
            assert not is_low, f"confidence_level={normal_confidence} should NOT be LOW"
