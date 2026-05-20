"""Integration tests for ADRION 369 MCP Servers.

Tests cover:
  - Shared utilities (guardian laws, digital root, EBDI, trust score)
  - RouterLogic   — discover_agents, route_task, validate_tool_schema, health_check
  - VortexLogic   — EBDI state, digital root, pulse, state estimation
  - GuardianLogic — law evaluation, consent, harm risk, audit
  - OracleLogic   — confidence scoring, prediction, risk analysis, token estimation
  - GenesisLogic  — record creation, retrieval, hash chain, integrity
  - HealerLogic   — diagnosis, fix suggestions, optimisation, health report

All tests run WITHOUT the mcp SDK — only business logic is exercised.
The `conftest.py` in this directory adds mcp-servers/ to sys.path.
"""

from __future__ import annotations

import pytest

# Shared utilities
from shared import (
    DENY_WEIGHTED_THRESHOLD,
    GUARDIAN_LAWS,
    GUARDIAN_LAWS_BY_ID,
    EBDIState,
    TrustScore,
    digital_root,
    evaluate_guardian_laws,
    load_guardian_laws_json,
    sha256_hex,
    utc_now,
)

# Server logic classes (no mcp SDK required)
from router.server import RouterLogic
from vortex.server import VortexLogic
from guardian.server import GuardianLogic
from oracle.server import OracleLogic
from genesis.server import GenesisLogic
from healer.server import HealerLogic


# ===========================================================================
# Shared utilities
# ===========================================================================

class TestGuardianLawsCanonical:
    def test_nine_laws_present(self) -> None:
        assert len(GUARDIAN_LAWS) == 9

    def test_law_ids_g1_to_g9(self) -> None:
        ids = [law["id"] for law in GUARDIAN_LAWS]
        assert ids == ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9"]

    def test_law_names_match_canonical(self) -> None:
        names = {law["id"]: law["name"] for law in GUARDIAN_LAWS}
        assert names["G7"] == "Privacy"
        assert names["G8"] == "Nonmaleficence"
        assert names["G1"] == "Unity"
        assert names["G2"] == "Harmony"

    def test_critical_laws_have_veto(self) -> None:
        for law in GUARDIAN_LAWS:
            if law["severity"] == "CRITICAL":
                assert law["veto"] == "true", f"{law['id']} must have veto=true"

    def test_non_critical_laws_no_veto(self) -> None:
        for law in GUARDIAN_LAWS:
            if law["severity"] != "CRITICAL":
                assert law["veto"] == "false", f"{law['id']} must have veto=false"

    def test_by_id_lookup(self) -> None:
        assert GUARDIAN_LAWS_BY_ID["G7"]["name"] == "Privacy"
        assert GUARDIAN_LAWS_BY_ID["G9"]["severity"] == "HIGH"

    def test_deny_threshold_is_positive(self) -> None:
        assert DENY_WEIGHTED_THRESHOLD > 0


class TestDigitalRoot:
    def test_zero_returns_zero(self) -> None:
        assert digital_root(0) == 0

    def test_single_digits_unchanged(self) -> None:
        for i in range(1, 10):
            assert digital_root(i) == i, f"digital_root({i}) should be {i}"

    def test_two_digit_reduction(self) -> None:
        assert digital_root(10) == 1
        assert digital_root(11) == 2
        assert digital_root(18) == 9
        assert digital_root(19) == 1
        assert digital_root(27) == 9

    def test_tesla_numbers_reduce_to_3_6_9(self) -> None:
        assert digital_root(3)   == 3
        assert digital_root(6)   == 6
        assert digital_root(9)   == 9
        assert digital_root(36)  == 9
        assert digital_root(369) == 9  # Master number

    def test_negative_input_handled(self) -> None:
        assert digital_root(-9) == 9
        assert digital_root(-18) == 9

    def test_large_number(self) -> None:
        # 999 = 9+9+9 = 27 → 2+7 = 9
        assert digital_root(999) == 9


class TestEvaluateGuardianLaws:
    def test_fully_compliant(self) -> None:
        ok, violations, score = evaluate_guardian_laws(
            "query", {"reason": "unit test", "audit_logged": True}
        )
        assert ok is True
        assert violations == []
        assert score == 0

    def test_g7_privacy_veto(self) -> None:
        ok, violations, _ = evaluate_guardian_laws(
            "export", {"scope": "global", "reason": "test", "audit_logged": True}
        )
        assert ok is False
        assert "G7" in violations

    def test_g8_nonmaleficence_veto(self) -> None:
        ok, violations, _ = evaluate_guardian_laws(
            "delete", {"backup_exists": False, "reason": "test", "audit_logged": True}
        )
        assert ok is False
        assert "G8" in violations

    def test_g4_causality_no_reason(self) -> None:
        _, violations, _ = evaluate_guardian_laws("query", {})
        assert "G4" in violations

    def test_g5_transparency_critical_op_no_audit(self) -> None:
        _, violations, _ = evaluate_guardian_laws(
            "deploy", {"reason": "release", "audit_logged": False}
        )
        assert "G5" in violations

    def test_g9_sustainability_high_cost(self) -> None:
        _, violations, _ = evaluate_guardian_laws(
            "analyze", {"reason": "batch", "resource_cost": 1500}
        )
        assert "G9" in violations

    def test_single_critical_veto_denies_regardless_of_score(self) -> None:
        # Even with a small total score, G7 veto must deny
        ok, violations, score = evaluate_guardian_laws(
            "export", {"scope": "global", "reason": "test", "audit_logged": True}
        )
        assert ok is False
        assert score >= 10  # CRITICAL weight


class TestSha256Hex:
    def test_deterministic(self) -> None:
        assert sha256_hex("hello") == sha256_hex("hello")

    def test_different_inputs_differ(self) -> None:
        assert sha256_hex("hello") != sha256_hex("world")

    def test_output_length_is_64(self) -> None:
        assert len(sha256_hex("test")) == 64

    def test_empty_string(self) -> None:
        result = sha256_hex("")
        assert len(result) == 64


class TestEBDIState:
    def test_default_values_in_range(self) -> None:
        state = EBDIState()
        assert 0.0 <= state.pleasure  <= 1.0
        assert 0.0 <= state.arousal   <= 1.0
        assert 0.0 <= state.dominance <= 1.0

    def test_crisis_false_by_default(self) -> None:
        state = EBDIState()
        assert state.is_crisis is False

    def test_crisis_triggers_above_07(self) -> None:
        state = EBDIState(arousal=0.71)
        assert state.is_crisis is True

    def test_update_clamps_above_one(self) -> None:
        state = EBDIState()
        state.update(arousal=1.5)
        assert state.arousal == 1.0

    def test_update_clamps_below_zero(self) -> None:
        state = EBDIState()
        state.update(pleasure=-0.5)
        assert state.pleasure == 0.0

    def test_to_dict_contains_keys(self) -> None:
        d = EBDIState().to_dict()
        assert "pleasure" in d and "arousal" in d and "dominance" in d


class TestTrustScore:
    def test_initial_score_is_high(self) -> None:
        ts = TrustScore(agent="test")
        assert ts.score == 0.85
        assert ts.is_blocked is False

    def test_success_increases_score(self) -> None:
        ts = TrustScore(agent="test")
        ts.update(True)
        assert ts.score > 0.85
        assert ts.successes == 1

    def test_failure_decreases_score(self) -> None:
        ts = TrustScore(agent="test")
        ts.update(False)
        assert ts.score < 0.85
        assert ts.failures == 1

    def test_blocked_when_score_below_06(self) -> None:
        ts = TrustScore(agent="test", score=0.55)
        assert ts.is_blocked is True

    def test_score_capped_at_one(self) -> None:
        ts = TrustScore(agent="test", score=0.99)
        ts.update(True)
        assert ts.score <= 1.0

    def test_score_floored_at_zero(self) -> None:
        ts = TrustScore(agent="test", score=0.1)
        ts.update(False)
        assert ts.score >= 0.0


# ===========================================================================
# Router
# ===========================================================================

class TestRouterLogic:
    @pytest.fixture
    def router(self) -> RouterLogic:
        return RouterLogic()

    def test_discover_agents_returns_all(self, router: RouterLogic) -> None:
        result = router.discover_agents()
        assert result["status"] == "ok"
        assert result["total"] >= 9
        assert "agents" in result

    def test_route_task_returns_agent_id(self, router: RouterLogic) -> None:
        result = router.route_task("I need help with unit testing")
        assert result["status"] == "ok"
        assert "agent_id" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_route_task_domain_match_gives_high_confidence(self, router: RouterLogic) -> None:
        result = router.route_task("architecture review", domain="process_architecture")
        assert result["agent_id"] == "02"  # PAA
        assert result["confidence"] == 1.0

    def test_route_task_unknown_domain_uses_fallback(self, router: RouterLogic) -> None:
        result = router.route_task("something completely unrelated xyz")
        assert result["status"] == "ok"
        assert result["agent_id"]  # any non-empty agent ID

    def test_get_capabilities_non_empty(self, router: RouterLogic) -> None:
        result = router.get_capabilities()
        assert result["status"] == "ok"
        assert result["total_unique"] > 0
        assert "capabilities" in result

    def test_validate_tool_schema_valid(self, router: RouterLogic) -> None:
        spec = {
            "name": "my_tool",
            "description": "Does something",
            "inputSchema": {"type": "object", "properties": {}, "required": []},
        }
        result = router.validate_tool_schema(spec)
        assert result["status"] == "valid"
        assert result["missing_fields"] == []

    def test_validate_tool_schema_missing_description(self, router: RouterLogic) -> None:
        result = router.validate_tool_schema({"name": "partial"})
        assert result["status"] == "invalid"
        assert "description" in result["missing_fields"]

    def test_validate_tool_schema_missing_input_schema(self, router: RouterLogic) -> None:
        result = router.validate_tool_schema({"name": "x", "description": "d"})
        assert "inputSchema" in result["missing_fields"]

    def test_health_check_returns_ok(self, router: RouterLogic) -> None:
        result = router.health_check()
        assert result["status"] in ("ok", "degraded")
        assert "downstream" in result
        assert "vortex" in result["downstream"]


# ===========================================================================
# Vortex
# ===========================================================================

class TestVortexLogic:
    @pytest.fixture
    def vortex(self) -> VortexLogic:
        return VortexLogic()

    def test_get_ebdi_state_values_in_range(self, vortex: VortexLogic) -> None:
        result = vortex.get_ebdi_state()
        assert result["status"] == "ok"
        assert 0.0 <= result["pleasure"]  <= 1.0
        assert 0.0 <= result["arousal"]   <= 1.0
        assert 0.0 <= result["dominance"] <= 1.0

    def test_update_ebdi_sets_pleasure(self, vortex: VortexLogic) -> None:
        result = vortex.update_ebdi_state(pleasure=0.9)
        assert result["status"] == "ok"
        assert result["pleasure"] == 0.9
        assert "pleasure" in result["updated_fields"]

    def test_update_ebdi_crisis_warning(self, vortex: VortexLogic) -> None:
        result = vortex.update_ebdi_state(arousal=0.8)
        assert result["is_crisis"] is True
        assert "warning" in result

    def test_calculate_digital_root_369(self, vortex: VortexLogic) -> None:
        result = vortex.calculate_digital_root(369)
        assert result["digital_root"] == 9
        assert result["is_tesla_number"] is True

    def test_calculate_digital_root_non_tesla(self, vortex: VortexLogic) -> None:
        result = vortex.calculate_digital_root(2)
        assert result["is_tesla_number"] is False

    def test_pulse_heartbeat_correct_frequency(self, vortex: VortexLogic) -> None:
        result = vortex.pulse_heartbeat()
        assert result["status"] == "ok"
        assert result["frequency_hz"] == 174.0

    def test_pulse_heartbeat_appends_to_log(self, vortex: VortexLogic) -> None:
        vortex.pulse_heartbeat()
        vortex.pulse_heartbeat()
        assert len(vortex._pulse_log) == 2

    def test_estimate_next_state_calm_lowers_arousal(self, vortex: VortexLogic) -> None:
        vortex.update_ebdi_state(arousal=0.5)
        result = vortex.estimate_next_state("calm", 1.0)
        assert result["status"] == "ok"
        assert result["predicted_arousal"] < 0.5

    def test_estimate_next_state_excite_raises_arousal(self, vortex: VortexLogic) -> None:
        vortex.update_ebdi_state(arousal=0.3)
        result = vortex.estimate_next_state("excite", 1.0)
        assert result["predicted_arousal"] > 0.3

    def test_estimate_next_state_unknown_direction(self, vortex: VortexLogic) -> None:
        result = vortex.estimate_next_state("unknown_dir", 0.5)
        assert result["status"] == "ok"


# ===========================================================================
# Guardian
# ===========================================================================

class TestGuardianLogic:
    @pytest.fixture
    def guardian(self) -> GuardianLogic:
        return GuardianLogic()

    def test_evaluate_laws_allow_compliant(self, guardian: GuardianLogic) -> None:
        result = guardian.evaluate_laws("query", {"reason": "testing"})
        assert result["status"] == "ok"
        assert result["verdict"] == "ALLOW"
        assert result["violations"] == []

    def test_evaluate_laws_deny_g7(self, guardian: GuardianLogic) -> None:
        result = guardian.evaluate_laws("export", {"scope": "global", "reason": "t", "audit_logged": True})
        assert result["verdict"] == "DENY"
        assert "G7" in result["violations"]

    def test_evaluate_laws_deny_g8(self, guardian: GuardianLogic) -> None:
        result = guardian.evaluate_laws("delete", {"backup_exists": False, "reason": "clean"})
        assert result["verdict"] == "DENY"
        assert "G8" in result["violations"]

    def test_evaluate_laws_records_violation(self, guardian: GuardianLogic) -> None:
        guardian.evaluate_laws("export", {"scope": "global", "reason": "x", "audit_logged": True})
        assert len(guardian._violations_log) == 1

    def test_check_critical_violations_g7(self, guardian: GuardianLogic) -> None:
        result = guardian.check_critical_violations("export", {"scope": "global", "reason": "x"})
        assert result["allow"] is False
        assert "G7" in result["critical_violations"]

    def test_check_critical_violations_safe(self, guardian: GuardianLogic) -> None:
        result = guardian.check_critical_violations("query", {"reason": "safe op"})
        assert result["allow"] is True
        assert result["critical_violations"] == []

    def test_audit_decision_creates_entry(self, guardian: GuardianLogic) -> None:
        result = guardian.audit_decision("D001", "deploy", {"env": "staging"}, "ALLOW")
        assert result["status"] == "ok"
        assert result["audit_id"].startswith("AUD-")
        assert len(guardian._audit_log) == 1

    def test_get_law_details_g7(self, guardian: GuardianLogic) -> None:
        result = guardian.get_law_details("G7")
        assert result["status"] == "ok"
        assert result["id"] == "G7"
        assert result["name"] == "Privacy"
        assert result["severity"] == "CRITICAL"

    def test_get_law_details_not_found(self, guardian: GuardianLogic) -> None:
        result = guardian.get_law_details("G99")
        assert result["status"] == "not_found"

    def test_validate_consent_local_scope(self, guardian: GuardianLogic) -> None:
        result = guardian.validate_consent("project_data", "local", "agent_MPG")
        assert result["status"] == "ok"
        assert result["g7_compliant"] is True
        assert result["verdict"] == "ALLOW"

    def test_validate_consent_sensitive_global(self, guardian: GuardianLogic) -> None:
        result = guardian.validate_consent("user_email", "global", "agent_X")
        assert result["g7_compliant"] is False
        assert "DENY" in result["verdict"]

    def test_check_harm_risk_critical_denied(self, guardian: GuardianLogic) -> None:
        result = guardian.check_harm_risk("drop_table", "critical")
        assert result["allow"] is False
        assert result["risk_score"] == 10

    def test_check_harm_risk_low_allowed(self, guardian: GuardianLogic) -> None:
        result = guardian.check_harm_risk("read_log", "low")
        assert result["allow"] is True


# ===========================================================================
# Oracle
# ===========================================================================

class TestOracleLogic:
    @pytest.fixture
    def oracle(self) -> OracleLogic:
        return OracleLogic()

    def test_score_in_range(self, oracle: OracleLogic) -> None:
        result = oracle.score_task_confidence("write tests", ["pytest", "coverage"], {})
        assert result["status"] == "ok"
        assert 0 <= result["confidence"] <= 100

    def test_more_tools_higher_confidence(self, oracle: OracleLogic) -> None:
        few = oracle.score_task_confidence("task", [], {})["confidence"]
        many = oracle.score_task_confidence("task", ["a", "b", "c", "d", "e"], {})["confidence"]
        assert many > few

    def test_prior_success_bonus_applied(self, oracle: OracleLogic) -> None:
        without = oracle.score_task_confidence("task", [], {})["confidence"]
        with_ctx = oracle.score_task_confidence("task", [], {"prior_success": True})["confidence"]
        assert with_ctx > without

    def test_complex_task_gets_penalty(self, oracle: OracleLogic) -> None:
        simple  = oracle.score_task_confidence("read file", [], {})["confidence"]
        complex_ = oracle.score_task_confidence("refactor entire codebase", [], {})["confidence"]
        assert complex_ < simple

    def test_predict_outcome_has_required_fields(self, oracle: OracleLogic) -> None:
        result = oracle.predict_outcome("deploy", {"service": "api", "version": "1.2.0"})
        assert result["status"] == "ok"
        assert "outcome" in result
        assert 0.0 <= result["success_probability"] <= 1.0

    def test_analyze_risks_score_in_range(self, oracle: OracleLogic) -> None:
        result = oracle.analyze_risks("delete", "database", ["auth", "cache"])
        assert result["status"] == "ok"
        assert 0 <= result["risk_score"] <= 10
        assert result["risk_band"] in ("low", "medium", "high", "critical")
        assert "mitigations" in result

    def test_production_scope_high_risk(self, oracle: OracleLogic) -> None:
        result = oracle.analyze_risks("deploy", "production", [])
        assert result["risk_score"] >= 6

    def test_estimate_tokens_positive(self, oracle: OracleLogic) -> None:
        result = oracle.estimate_tokens("Hello, world!", "gpt-4o", 100)
        assert result["status"] == "ok"
        assert result["estimated_input_tokens"] >= 1
        assert result["estimated_total_tokens"] == result["estimated_input_tokens"] + 100

    def test_recommend_next_step_returns_recommendation(self, oracle: OracleLogic) -> None:
        result = oracle.recommend_next_step("testing", "deployment", [])
        assert result["status"] == "ok"
        assert result["recommendation"]

    def test_recommend_next_step_applies_constraints(self, oracle: OracleLogic) -> None:
        # Constraint filters out steps containing the keyword
        result = oracle.recommend_next_step("testing", "deployment", ["linter"])
        for alt in result["alternatives"]:
            assert "linter" not in alt


# ===========================================================================
# Genesis
# ===========================================================================

class TestGenesisLogic:
    @pytest.fixture
    def genesis(self) -> GenesisLogic:
        return GenesisLogic()

    def test_create_record_returns_id_and_hash(self, genesis: GenesisLogic) -> None:
        result = genesis.create_record("session", {"title": "test session"}, "agent_MPG")
        assert result["status"] == "ok"
        assert "record_id" in result
        assert len(result["hash"]) == 64  # SHA-256 hex

    def test_chain_grows_with_records(self, genesis: GenesisLogic) -> None:
        genesis.create_record("session", {"a": 1}, "tester")
        genesis.create_record("audit",   {"b": 2}, "tester")
        assert genesis._chain[-1]["prev_hash"] == genesis._chain[-2]["hash"]

    def test_get_record_found(self, genesis: GenesisLogic) -> None:
        created = genesis.create_record("report", {"content": "x"}, "oracle")
        rid = created["record_id"]
        result = genesis.get_record(rid)
        assert result["status"] == "ok"
        assert result["record_id"] == rid
        assert result["integrity_ok"] is True

    def test_get_record_not_found(self, genesis: GenesisLogic) -> None:
        result = genesis.get_record("nonexistent-uuid")
        assert result["status"] == "not_found"

    def test_verify_integrity_valid(self, genesis: GenesisLogic) -> None:
        created = genesis.create_record("decision", {"choice": "A"}, "guardian")
        rid = created["record_id"]
        verify = genesis.verify_integrity(rid)
        assert verify["valid"] is True
        assert verify["tamper_detected"] is False

    def test_verify_integrity_detects_tampering(self, genesis: GenesisLogic) -> None:
        created = genesis.create_record("session", {"data": "original"}, "test")
        rid = created["record_id"]
        # Simulate tampering by mutating data directly
        genesis._records[rid]["data"] = {"data": "tampered"}
        verify = genesis.verify_integrity(rid)
        assert verify["valid"] is False
        assert verify["tamper_detected"] is True

    def test_audit_chain_empty_prefix(self, genesis: GenesisLogic) -> None:
        genesis.create_record("session", {}, "test")
        result = genesis.audit_chain("")
        assert result["status"] == "ok"
        assert len(result["chain"]) >= 1  # empty prefix matches all

    def test_export_archive_returns_records(self, genesis: GenesisLogic) -> None:
        genesis.create_record("session", {"n": 1}, "tester")
        genesis.create_record("session", {"n": 2}, "tester")
        genesis.create_record("audit",   {"n": 3}, "tester")
        result = genesis.export_archive("session")
        assert result["status"] == "ok"
        assert result["count"] == 2
        assert len(result["archive_hash"]) == 64

    def test_export_archive_empty_type(self, genesis: GenesisLogic) -> None:
        result = genesis.export_archive("nonexistent_type")
        assert result["count"] == 0
        assert result["archive_hash"]  # still returns a hash (of empty)


# ===========================================================================
# Healer
# ===========================================================================

class TestHealerLogic:
    @pytest.fixture
    def healer(self) -> HealerLogic:
        return HealerLogic()

    def test_diagnose_issue_known_symptom(self, healer: HealerLogic) -> None:
        result = healer.diagnose_issue(["high_latency", "timeout"], "api")
        assert result["status"] == "ok"
        assert "issue_id" in result
        assert result["severity"] in ("low", "medium", "high", "critical", "unknown")

    def test_diagnose_issue_records_history(self, healer: HealerLogic) -> None:
        healer.diagnose_issue(["memory_leak"], "backend")
        assert len(healer._repair_history) == 1

    def test_suggest_fix_known_issue(self, healer: HealerLogic) -> None:
        result = healer.suggest_fix("high_latency", "medium")
        assert result["status"] == "ok"
        assert len(result["actions"]) > 0
        assert result["primary_action"]

    def test_suggest_fix_unknown_issue_uses_fallback(self, healer: HealerLogic) -> None:
        result = healer.suggest_fix("alien_bug", "critical")
        assert result["status"] == "ok"
        assert result["actions"]

    def test_optimize_query_db_caps_limit(self, healer: HealerLogic) -> None:
        result = healer.optimize_query("db_query", {"limit": 9999, "offset": 0})
        assert result["status"] == "ok"
        assert result["optimized_params"]["limit"] <= 100

    def test_optimize_query_unsupported_type(self, healer: HealerLogic) -> None:
        result = healer.optimize_query("sql_legacy", {})
        assert result["status"] == "unsupported_type"
        assert "available_types" in result

    def test_cleanup_state_soft_strategy(self, healer: HealerLogic) -> None:
        result = healer.cleanup_state("cache", "soft")
        assert result["status"] == "ok"
        assert result["clean"] is True
        assert len(result["actions_executed"]) >= 2

    def test_cleanup_state_hard_strategy(self, healer: HealerLogic) -> None:
        result = healer.cleanup_state("api", "hard")
        assert result["status"] == "ok"
        assert len(result["actions_executed"]) == 3

    def test_cleanup_state_invalid_strategy(self, healer: HealerLogic) -> None:
        result = healer.cleanup_state("api", "nuclear")
        assert result["status"] == "invalid_strategy"

    def test_health_report_structure(self, healer: HealerLogic) -> None:
        result = healer.health_report()
        assert result["status"] == "ok"
        assert result["overall_health"] in ("healthy", "degraded")
        assert "components" in result
        assert "api" in result["components"]

    def test_health_report_all_healthy_by_default(self, healer: HealerLogic) -> None:
        result = healer.health_report()
        # Default fixture has all healthy
        assert result["degraded_components"] == []
        assert result["overall_health"] == "healthy"


# ===========================================================================
# Cross-server integration smoke tests
# ===========================================================================

class TestCrossServerIntegration:
    """End-to-end scenarios exercising multiple servers together."""

    def test_guardian_rejects_oracle_prediction_export(self) -> None:
        """Oracle predicts global export; Guardian rejects it."""
        oracle = OracleLogic()
        guardian = GuardianLogic()

        prediction = oracle.predict_outcome("export", {"scope": "global"})
        assert prediction["status"] == "ok"

        check = guardian.check_critical_violations(
            "export", {"scope": "global", "reason": "predicted export"}
        )
        assert check["allow"] is False

    def test_genesis_records_guardian_decision(self) -> None:
        """Guardian evaluates a decision; Genesis records the outcome."""
        guardian = GuardianLogic()
        genesis = GenesisLogic()

        verdict = guardian.evaluate_laws("deploy", {"reason": "release v2", "audit_logged": True})
        record = genesis.create_record(
            record_type="decision",
            data={"verdict": verdict["verdict"], "operation": "deploy"},
            author="guardian",
        )
        assert record["status"] == "ok"
        verify = genesis.verify_integrity(record["record_id"])
        assert verify["valid"] is True

    def test_vortex_crisis_triggers_healer(self) -> None:
        """Vortex enters crisis; Healer provides a fix."""
        vortex = VortexLogic()
        healer = HealerLogic()

        vortex.update_ebdi_state(arousal=0.85)
        state = vortex.get_ebdi_state()
        assert state["is_crisis"] is True

        fix = healer.suggest_fix("error_rate_spike", "critical")
        assert fix["status"] == "ok"
        assert "rollback_deployment" in fix["actions"] or fix["primary_action"]

    def test_router_routes_to_right_agent_for_security_task(self) -> None:
        """Router should prefer GRA (governance/risk) for security tasks."""
        router = RouterLogic()
        result = router.route_task("security compliance audit", domain="governance_risk")
        assert result["agent_id"] == "06"  # GRA
        assert result["confidence"] == 1.0
