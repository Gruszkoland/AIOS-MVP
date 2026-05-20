"""Tests for mcp-servers/verify_mode.py — VerifyMode Self-Correction Engine.

Test coverage:
  TestDevilAdvocatePrompts  — 9 tests, one per ROPE agent persona
  TestEdgeCaseScenarios     — 5 tests, one per "co by bylo gdyby" scenario
  TestGuardianLawsMapping   — 9 tests covering all 9 Guardian Laws
  TestRiskScoring           — 5 tests for LOW/MEDIUM/HIGH/CRITICAL risk bands
  TestVerifyAgentOutput     — 6 tests for overall verify_agent_output behaviour

Total: 34 tests — all must pass with no mcp SDK dependency.

The conftest.py in this directory adds mcp-servers/ to sys.path.
"""

from __future__ import annotations

import pytest

from verify_mode import (
    KNOWN_AGENT_IDS,
    RISK_LEVELS,
    VerifyMode,
    _AGENT_SPECIFIC_CHALLENGES,
    _REQUIRED_OUTPUT_FIELDS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vm() -> VerifyMode:
    """Fresh VerifyMode instance for each test."""
    return VerifyMode()


def _minimal_output(
    agent: str = "AIO-01",
    confidence: int = 85,
    status: str = "completed",
    notes: str = "unit test run",
    genesis_write: bool = True,
) -> dict:
    """Build a minimal valid ROPE v3.0 output dict."""
    return {
        "agent": agent,
        "trace_id": "12345678-1234-4abc-89ab-123456789012.AIO-01.1716210000000",
        "session_id": "sess-001",
        "task_id": "task-001",
        "confidence_level": confidence,
        "status": status,
        "guardian_result": {"passed": True, "violations": [], "laws_checked": ["G4", "G8"]},
        "agent_output": {},
        "ebdi_state": {"pleasure": 0.7, "arousal": 0.2, "dominance": 0.8},
        "handoff": {"next_agent": "VTA-05", "scenario": "success", "reason": ""},
        "genesis_log": {"write_required": genesis_write, "event_type": "handoff", "summary": "Done"},
        "notes": notes,
    }


# ===========================================================================
# TestDevilAdvocatePrompts — 9 tests, one per agent
# ===========================================================================

class TestDevilAdvocatePrompts:
    """Devil's Advocate prompt is correctly generated for each of the 9 agents."""

    def _assert_prompt_basics(self, vm: VerifyMode, agent_id: str) -> str:
        """Helper: generate prompt and assert structural invariants."""
        prompt = vm.generate_devil_advocate_prompt(agent_id, f"sample task for {agent_id}")
        assert isinstance(prompt, str), "Prompt must be a string"
        assert len(prompt) > 100, "Prompt must be substantive (> 100 chars)"
        assert agent_id in prompt, f"Agent ID '{agent_id}' must appear in prompt"
        assert "CLAIM:" in prompt, "Prompt must contain CLAIM section"
        assert "CHALLENGE:" in prompt, "Prompt must contain CHALLENGE section"
        assert "EVIDENCE:" in prompt, "Prompt must contain EVIDENCE section"
        assert "VERDICT:" in prompt, "Prompt must contain VERDICT section"
        assert "E1:" in prompt, "Prompt must list edge case E1"
        assert "E5:" in prompt, "Prompt must list edge case E5"
        return prompt

    def test_aio01_prompt_contains_sql_check(self, vm: VerifyMode) -> None:
        prompt = self._assert_prompt_basics(vm, "AIO-01")
        assert "f-string SQL" in prompt or "circular import" in prompt.lower() or "type hints" in prompt

    def test_paa02_prompt_contains_adr_check(self, vm: VerifyMode) -> None:
        prompt = self._assert_prompt_basics(vm, "PAA-02")
        assert "ADR" in prompt

    def test_tdo03_prompt_contains_safety_check(self, vm: VerifyMode) -> None:
        prompt = self._assert_prompt_basics(vm, "TDO-03")
        assert "CVE" in prompt or "safety check" in prompt or "bandit" in prompt

    def test_aua04_prompt_contains_idempotent_check(self, vm: VerifyMode) -> None:
        prompt = self._assert_prompt_basics(vm, "AUA-04")
        assert "idempotent" in prompt or "dry-run" in prompt

    def test_vta05_prompt_contains_coverage_check(self, vm: VerifyMode) -> None:
        prompt = self._assert_prompt_basics(vm, "VTA-05")
        assert "coverage" in prompt or "PASS" in prompt or "edge case" in prompt

    def test_gra06_prompt_contains_owasp_check(self, vm: VerifyMode) -> None:
        prompt = self._assert_prompt_basics(vm, "GRA-06")
        assert "OWASP" in prompt

    def test_oca07_prompt_contains_hop_count_check(self, vm: VerifyMode) -> None:
        prompt = self._assert_prompt_basics(vm, "OCA-07")
        assert "hop_count" in prompt or "routing loop" in prompt

    def test_ksa08_prompt_contains_openapi_check(self, vm: VerifyMode) -> None:
        prompt = self._assert_prompt_basics(vm, "KSA-08")
        assert "OpenAPI" in prompt or "GUARDIAN_LAWS_CANONICAL" in prompt

    def test_ria09_prompt_contains_backup_check(self, vm: VerifyMode) -> None:
        prompt = self._assert_prompt_basics(vm, "RIA-09")
        assert "backup" in prompt or "VTA-05" in prompt

    def test_unknown_agent_uses_default_challenge(self, vm: VerifyMode) -> None:
        prompt = vm.generate_devil_advocate_prompt("UNKNOWN-99", "some task")
        assert "UNKNOWN-99" in prompt
        # DEFAULT challenge must apply
        assert "Guardian Laws" in prompt or "confidence_level" in prompt


# ===========================================================================
# TestEdgeCaseScenarios — 5 tests
# ===========================================================================

class TestEdgeCaseScenarios:
    """The 5 'co by bylo gdyby' edge cases are detected by verify_agent_output."""

    def test_e1_critical_guardian_violation_blocks_output(self, vm: VerifyMode) -> None:
        """E1: Guardian DENY from pre-existing violation makes output unsafe."""
        output = _minimal_output()
        output["guardian_result"] = {
            "passed": False,
            "violations": ["G7"],
            "laws_checked": ["G7", "G8"],
        }
        result = vm.verify_agent_output("AIO-01", output)
        assert result["is_safe"] is False
        assert result["risk_level"] in ("HIGH", "CRITICAL")
        assert any("G7" in c for c in result["concerns"])

    def test_e2_low_confidence_baseline_adds_concern(self, vm: VerifyMode) -> None:
        """E2: Low confidence_level triggers a concern (maps to invalid baseline risk)."""
        output = _minimal_output(confidence=15)
        result = vm.verify_agent_output("VTA-05", output)
        # Low confidence is penalised
        assert result["score"] < 100
        assert any("confidence" in c.lower() for c in result["concerns"])

    def test_e3_pii_email_triggers_g7_concern(self, vm: VerifyMode) -> None:
        """E3: A PII email address in output notes raises a G7 Privacy concern."""
        output = _minimal_output(notes="contact user@example.com for details")
        result = vm.verify_agent_output("KSA-08", output)
        assert any("email" in c.lower() or "G7" in c for c in result["concerns"])
        # PII makes output unsafe
        assert result["is_safe"] is False or result["score"] <= 60

    def test_e4_missing_trace_id_adds_concern(self, vm: VerifyMode) -> None:
        """E4: A malformed trace_id (simulating broken upstream) adds a concern."""
        output = _minimal_output()
        output["trace_id"] = "not-a-valid-trace-id"
        result = vm.verify_agent_output("AIO-01", output)
        assert any("trace_id" in c.lower() for c in result["concerns"])

    def test_e5_missing_required_fields_detected(self, vm: VerifyMode) -> None:
        """E5: An output missing required fields (e.g. from retry failure) is penalised."""
        incomplete = {
            "agent": "OCA-07",
            "status": "blocked",
            # missing: trace_id, confidence_level, guardian_result, handoff
        }
        result = vm.verify_agent_output("OCA-07", incomplete)
        missing_concerns = [c for c in result["concerns"] if "Missing required" in c]
        assert len(missing_concerns) >= 4  # 4 fields absent
        assert result["score"] < 100


# ===========================================================================
# TestGuardianLawsMapping — 9 tests
# ===========================================================================

class TestGuardianLawsMapping:
    """check_against_guardian_laws maps all 9 laws and detects violations."""

    def test_all_nine_laws_present_in_mapping(self, vm: VerifyMode) -> None:
        """All G1-G9 keys must appear in laws_mapping regardless of violations."""
        output = _minimal_output(notes="deploy reason")
        result = vm.check_against_guardian_laws(output)
        assert result["status"] == "ok"
        mapping = result["laws_mapping"]
        for i in range(1, 10):
            assert f"G{i}" in mapping, f"G{i} must be present in laws_mapping"

    def test_laws_mapping_contains_required_keys_per_law(self, vm: VerifyMode) -> None:
        """Each law entry must have name, severity, veto, violated, description."""
        output = _minimal_output()
        result = vm.check_against_guardian_laws(output)
        for law_id, details in result["laws_mapping"].items():
            assert "name" in details,        f"{law_id}: missing 'name'"
            assert "severity" in details,    f"{law_id}: missing 'severity'"
            assert "veto" in details,        f"{law_id}: missing 'veto'"
            assert "violated" in details,    f"{law_id}: missing 'violated'"
            assert "description" in details, f"{law_id}: missing 'description'"

    def test_veto_laws_g7_g8_have_veto_true(self, vm: VerifyMode) -> None:
        """G7 and G8 must be flagged as veto=True in the mapping."""
        output = _minimal_output()
        result = vm.check_against_guardian_laws(output)
        assert result["laws_mapping"]["G7"]["veto"] is True
        assert result["laws_mapping"]["G8"]["veto"] is True

    def test_non_veto_laws_have_veto_false(self, vm: VerifyMode) -> None:
        """G1-G6 and G9 must have veto=False."""
        output = _minimal_output()
        result = vm.check_against_guardian_laws(output)
        for law_id in ("G1", "G2", "G3", "G4", "G5", "G6", "G9"):
            assert result["laws_mapping"][law_id]["veto"] is False

    def test_g4_causality_violated_when_no_notes_or_task_id(self, vm: VerifyMode) -> None:
        """G4 (Causality) fires when output has no reason/notes/task_id.

        Note: a single G4 violation (HIGH weight=2) does NOT reach DENY_WEIGHTED_THRESHOLD=4
        so the verdict is still ALLOW — G4 is noted but not blocking on its own.
        """
        output = {
            "agent": "AIO-01",
            "trace_id": "12345678-1234-4abc-89ab-123456789012.AIO-01.111",
            "confidence_level": 80,
            "status": "completed",
            "guardian_result": {"passed": True, "violations": []},
            "handoff": {"next_agent": "VTA-05", "scenario": "success", "reason": ""},
            "genesis_log": {"write_required": True},
            "notes": "",         # empty notes
            "task_id": "",       # empty task_id -> no reason -> G4 fires
        }
        result = vm.check_against_guardian_laws(output)
        assert "G4" in result["violations"], "G4 must fire when reason is absent"
        assert result["laws_mapping"]["G4"]["violated"] is True

    def test_g5_transparency_violated_on_deploy_without_audit(self, vm: VerifyMode) -> None:
        """G5 (Transparency) fires for RIA-09 deploy without genesis_log.write_required."""
        output = _minimal_output(agent="RIA-09", status="completed", genesis_write=False)
        result = vm.check_against_guardian_laws(output)
        # RIA-09 completed -> inferred operation = deploy; audit_logged = False -> G5
        assert "G5" in result["violations"]

    def test_compliant_output_has_empty_violations(self, vm: VerifyMode) -> None:
        """A fully compliant output must produce zero violations."""
        output = _minimal_output(notes="deploy with reason", genesis_write=True)
        # Use a non-RIA-09 agent so operation is inferred as 'query' (safe)
        output["agent"] = "AIO-01"
        result = vm.check_against_guardian_laws(output)
        assert result["is_compliant"] is True
        assert result["violations"] == []
        assert result["verdict"] == "ALLOW"

    def test_verdict_allow_when_compliant(self, vm: VerifyMode) -> None:
        """verdict must be 'ALLOW' for a compliant output."""
        output = _minimal_output()
        result = vm.check_against_guardian_laws(output)
        assert result["verdict"] in ("ALLOW", "DENY")
        if result["is_compliant"]:
            assert result["verdict"] == "ALLOW"

    def test_verdict_deny_when_violation_present(self, vm: VerifyMode) -> None:
        """verdict must be 'DENY' when a CRITICAL (veto) law is violated.

        G8 (Nonmaleficence) is a CRITICAL veto law. Triggering it via a GRA-06
        agent that summarises a 'delete' operation with no backup_verified causes
        _infer_operation to return 'delete' and backup_exists=False, making
        evaluate_guardian_laws fire G8 -> instant DENY regardless of total score.
        """
        output = _minimal_output(agent="GRA-06", notes="security audit complete")
        # GRA-06 + "delete" in summary -> _infer_operation returns "delete"
        # backup_verified absent -> G8 Nonmaleficence fires (CRITICAL veto)
        output["genesis_log"]["summary"] = "delete old logs completed"
        output["agent_output"] = {}  # backup_verified not present -> False
        result = vm.check_against_guardian_laws(output)
        assert "G8" in result["violations"], "G8 must fire for delete without backup"
        assert result["verdict"] == "DENY"
        assert result["is_compliant"] is False


# ===========================================================================
# TestRiskScoring — 5 tests
# ===========================================================================

class TestRiskScoring:
    """Scoring matrix maps correctly to LOW/MEDIUM/HIGH/CRITICAL risk levels."""

    def test_clean_output_scores_low(self, vm: VerifyMode) -> None:
        """A fully valid output with no concerns must reach LOW risk (score >= 80)."""
        output = _minimal_output()
        result = vm.verify_agent_output("AIO-01", output)
        assert result["risk_level"] == "LOW"
        assert result["is_safe"] is True
        assert result["score"] >= 80

    def test_missing_one_field_scores_medium_or_below(self, vm: VerifyMode) -> None:
        """Removing one required field deducts 15 pts — stays in LOW or drops to MEDIUM."""
        output = _minimal_output()
        del output["handoff"]   # remove one of the 6 required fields
        result = vm.verify_agent_output("AIO-01", output)
        assert result["score"] <= 85  # 100 - 15 = 85

    def test_pii_in_output_scores_fifty_or_below(self, vm: VerifyMode) -> None:
        """PII detection deducts 50 pts — output drops to HIGH or CRITICAL."""
        output = _minimal_output(notes="Send results to admin@adrion.io")
        result = vm.verify_agent_output("GRA-06", output)
        assert result["score"] <= 50
        assert result["risk_level"] in ("HIGH", "CRITICAL")
        assert result["is_safe"] is False

    def test_critical_guardian_violation_scores_critical(self, vm: VerifyMode) -> None:
        """CRITICAL guardian violation deducts 60 pts — likely CRITICAL risk level."""
        output = _minimal_output()
        output["guardian_result"] = {
            "passed": False,
            "violations": ["G8"],
            "laws_checked": ["G8"],
        }
        result = vm.verify_agent_output("AIO-01", output)
        assert result["score"] <= 40
        assert result["risk_level"] in ("HIGH", "CRITICAL")
        assert result["is_safe"] is False

    def test_is_safe_false_for_high_and_critical(self, vm: VerifyMode) -> None:
        """is_safe must be False for both HIGH and CRITICAL risk levels."""
        # Force CRITICAL: PII + CRITICAL Guardian violation
        output = _minimal_output(notes="auth token: sk-abc123456789012345678901")
        output["guardian_result"] = {
            "passed": False,
            "violations": ["G7"],
            "laws_checked": ["G7"],
        }
        result = vm.verify_agent_output("RIA-09", output)
        assert result["is_safe"] is False


# ===========================================================================
# TestVerifyAgentOutput — 6 tests
# ===========================================================================

class TestVerifyAgentOutput:
    """Core behaviour of verify_agent_output across various scenarios."""

    def test_returns_all_required_keys(self, vm: VerifyMode) -> None:
        """Result dict must always contain the 7 required keys."""
        result = vm.verify_agent_output("PAA-02", _minimal_output("PAA-02"))
        for key in ("status", "agent_id", "is_safe", "risk_level", "score", "concerns", "recommendations", "timestamp"):
            assert key in result, f"Missing key '{key}' in verify result"

    def test_agent_id_is_echoed_in_result(self, vm: VerifyMode) -> None:
        """The agent_id passed in must be returned in the result."""
        result = vm.verify_agent_output("VTA-05", _minimal_output("VTA-05"))
        assert result["agent_id"] == "VTA-05"

    def test_unknown_agent_is_handled_without_exception(self, vm: VerifyMode) -> None:
        """An unrecognised agent_id must not raise — falls back to AIO-01 checks."""
        result = vm.verify_agent_output("XYZ-99", _minimal_output())
        assert result["status"] == "ok"
        assert result["risk_level"] in RISK_LEVELS

    def test_concerns_populated_on_issues(self, vm: VerifyMode) -> None:
        """When issues are found, concerns list must be non-empty."""
        output = _minimal_output(confidence=10)  # low confidence -> concern
        result = vm.verify_agent_output("TDO-03", output)
        assert len(result["concerns"]) >= 1

    def test_recommendations_populated_when_concerns_exist(self, vm: VerifyMode) -> None:
        """Recommendations list must be non-empty when concerns exist."""
        output = _minimal_output()
        del output["trace_id"]   # malformed/absent trace_id -> concern
        result = vm.verify_agent_output("OCA-07", output)
        # At least the missing-field concern adds a recommendation
        assert len(result["recommendations"]) >= 1

    def test_clean_output_has_empty_concerns(self, vm: VerifyMode) -> None:
        """A completely valid output must produce no concerns."""
        output = _minimal_output()
        result = vm.verify_agent_output("AIO-01", output)
        assert result["concerns"] == []
        assert result["recommendations"] == []
        assert result["is_safe"] is True


# ===========================================================================
# TestKnownAgentIds — sanity checks on module constants
# ===========================================================================

class TestModuleConstants:
    """Verify module-level constants are correct."""

    def test_nine_known_agent_ids(self) -> None:
        assert len(KNOWN_AGENT_IDS) == 9

    def test_all_agent_ids_in_known_set(self) -> None:
        expected = {"AIO-01", "PAA-02", "TDO-03", "AUA-04", "VTA-05",
                    "GRA-06", "OCA-07", "KSA-08", "RIA-09"}
        assert KNOWN_AGENT_IDS == expected

    def test_risk_levels_ordered(self) -> None:
        assert RISK_LEVELS == ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_required_output_fields_count(self) -> None:
        assert len(_REQUIRED_OUTPUT_FIELDS) == 6

    def test_all_nine_agents_have_specific_challenges(self) -> None:
        for agent_id in KNOWN_AGENT_IDS:
            assert agent_id in _AGENT_SPECIFIC_CHALLENGES, (
                f"{agent_id} must have a specific Devil's Advocate challenge"
            )

    def test_default_challenge_exists(self) -> None:
        assert "DEFAULT" in _AGENT_SPECIFIC_CHALLENGES
