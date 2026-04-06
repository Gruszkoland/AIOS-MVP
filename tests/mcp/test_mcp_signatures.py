"""
Test: MCP DSPy Signatures Validation (DSV)

Tests that all MCP servers implement correct Input -> Output contracts.
"""

import pytest
from mcp_servers import (
    MCPBaseServer, DSPySignature, TrustScore, EBDIState,
    GuardianLaw
)
from mcp_servers.vortex_mcp import VortexMCP, vortex_signature
from mcp_servers.guardian_mcp import GuardianMCP, guardian_signature
from mcp_servers.oracle_mcp import OracleMCP, oracle_signature
from mcp_servers.genesis_mcp import GenesisMCP, genesis_signature
from mcp_servers.healer_mcp import HealerMCP, healer_signature


class TestDSPySignatures:
    """Test DSPy signature validation"""

    def test_vortex_signature_valid(self):
        """VORTEX signature should have required fields"""
        assert vortex_signature.signature_name == "VortexOrchestration"
        assert "orchestration_context" in vortex_signature.input_schema
        assert "deployment_plan" in vortex_signature.output_schema
        assert "monitoring_hooks" in vortex_signature.output_schema

    def test_guardian_signature_valid(self):
        """GUARDIAN signature should have required fields"""
        assert guardian_signature.signature_name == "GuardianPolicy"
        assert "operation_type" in guardian_signature.input_schema
        assert "compliance_status" in guardian_signature.output_schema
        assert "violated_laws" in guardian_signature.output_schema

    def test_oracle_signature_valid(self):
        """ORACLE signature should have required fields"""
        assert oracle_signature.signature_name == "OracleRouting"
        assert "user_query" in oracle_signature.input_schema
        assert "decision_classification" in oracle_signature.output_schema
        assert "confidence" in oracle_signature.output_schema

    def test_genesis_signature_valid(self):
        """GENESIS signature should have required fields"""
        assert genesis_signature.signature_name == "GenesisMemory"
        assert "memory_query" in genesis_signature.input_schema
        assert "retrieved_context" in genesis_signature.output_schema
        assert "session_continuity" in genesis_signature.output_schema

    def test_healer_signature_valid(self):
        """HEALER signature should have required fields"""
        assert healer_signature.signature_name == "HealerRecovery"
        assert "health_telemetry" in healer_signature.input_schema
        assert "recovery_action" in healer_signature.output_schema


class TestSignatureValidation:
    """Test input/output validation"""

    def test_vortex_input_validation(self):
        """VORTEX should validate input schema"""
        valid_input = {
            "orchestration_context": {"state": "ready"},
            "deployment_target": "service:v1.0",
            "canary_percent": 5,
            "guardian_constraint": ["G1", "G7"]
        }
        assert vortex_signature.validate_input(valid_input)

    def test_guardian_input_validation(self):
        """GUARDIAN should validate input"""
        valid_input = {
            "operation_type": "export",
            "context_scope": "local",
            "actor_identity": "user123",
            "data_sensitivity": "confidential"
        }
        assert guardian_signature.validate_input(valid_input)

    def test_oracle_input_validation(self):
        """ORACLE should validate input"""
        valid_input = {
            "user_query": "fix the bug in payment service",
            "current_state": {"agent": "AUDITOR", "step": 5},
            "available_agents": [{"name": "VORTEX", "trust_score": 0.85}]
        }
        assert oracle_signature.validate_input(valid_input)


class TestServerInstantiation:
    """Test MCP server creation"""

    def test_vortex_instantiation(self):
        """VORTEX-MCP should initialize correctly"""
        server = VortexMCP()
        assert server.server_name == "VORTEX-MCP"
        assert server.port == 9001
        assert isinstance(server.ebdi_state, EBDIState)
        assert isinstance(server.trust_score, TrustScore)

    def test_guardian_instantiation(self):
        """GUARDIAN-MCP should initialize"""
        server = GuardianMCP()
        assert server.server_name == "GUARDIAN-MCP"
        assert server.port == 9002
        assert len(server.audit_log) == 0

    def test_oracle_instantiation(self):
        """ORACLE-MCP should initialize"""
        server = OracleMCP()
        assert server.server_name == "ORACLE-MCP"
        assert server.port == 9003
        assert "fix" in server.intent_patterns

    def test_genesis_instantiation(self):
        """GENESIS-MCP should initialize"""
        server = GenesisMCP()
        assert server.server_name == "GENESIS-MCP"
        assert server.port == 9004
        assert len(server.sessions) == 0

    def test_healer_instantiation(self):
        """HEALER-MCP should initialize"""
        server = HealerMCP()
        assert server.server_name == "HEALER-MCP"
        assert server.port == 9005
        assert len(server.alerts) == 0


class TestTrustScore:
    """Test Trust Score management"""

    def test_trust_score_increment_success(self):
        """TS should increase by 0.05 on success"""
        ts = TrustScore(agent_name="TEST")
        initial = ts.score
        ts.increment_success()
        assert ts.score == initial + 0.05
        assert ts.successes == 1

    def test_trust_score_increment_failure(self):
        """TS should decrease by 0.20 on failure"""
        ts = TrustScore(agent_name="TEST", score=0.8)
        initial = ts.score
        ts.increment_failure()
        assert ts.score == initial - 0.20
        assert ts.failures == 1

    def test_trust_score_blocked_threshold(self):
        """Agent should be blocked if TS < 0.6"""
        ts = TrustScore(agent_name="TEST", score=0.55)
        assert ts.is_blocked is True

        ts.score = 0.60
        assert ts.is_blocked is False

    def test_trust_score_capped_at_bounds(self):
        """TS should be capped at [0.0, 1.0]"""
        ts = TrustScore(agent_name="TEST", score=1.0)
        ts.increment_success()
        assert ts.score == 1.0

        ts.score = 0.0
        ts.increment_failure()
        assert ts.score == 0.0


class TestEBDIState:
    """Test EBDI vector management"""

    def test_ebdi_initialization(self):
        """EBDI should initialize to default values"""
        ebdi = EBDIState()
        assert ebdi.pleasure == 0.5
        assert ebdi.arousal == 0.3
        assert ebdi.dominance == 0.5

    def test_ebdi_crisis_mode(self):
        """Crisis mode should trigger at Arousal > 0.7"""
        ebdi = EBDIState(arousal=0.65)
        assert ebdi.is_crisis_mode is False

        ebdi.arousal = 0.75
        assert ebdi.is_crisis_mode is True

    def test_ebdi_to_dict(self):
        """EBDI should serialize to dict"""
        ebdi = EBDIState(pleasure=0.8, arousal=0.4, dominance=0.6)
        data = ebdi.to_dict()
        assert data["pleasure"] == 0.8
        assert data["arousal"] == 0.4
        assert data["dominance"] == 0.6


class TestGuardianLaws:
    """Test Guardian Laws enforcement"""

    def test_guardian_laws_enum(self):
        """All 9 Guardian Laws should exist"""
        laws = [
            GuardianLaw.G1_UNITY,
            GuardianLaw.G2_HARMONY,
            GuardianLaw.G3_RHYTHM,
            GuardianLaw.G4_CAUSALITY,
            GuardianLaw.G5_TRANSPARENCY,
            GuardianLaw.G6_AUTHENTICITY,
            GuardianLaw.G7_PRIVACY,
            GuardianLaw.G8_NONMALEFICENCE,
            GuardianLaw.G9_SUSTAINABILITY
        ]
        assert len(laws) == 9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
