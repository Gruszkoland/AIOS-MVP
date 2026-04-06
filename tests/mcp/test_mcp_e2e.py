"""
Test: MCP End-to-End (E2E) Integration

Tests complete routing workflow: Query -> Intent -> Compliance -> Execution -> Logging
"""

import pytest
import asyncio
from mcp_servers.router import MCPRouter, RoutingDecision
from mcp_servers.vortex_mcp import VortexMCP
from mcp_servers.guardian_mcp import GuardianMCP
from mcp_servers.oracle_mcp import OracleMCP
from mcp_servers.genesis_mcp import GenesisMCP
from mcp_servers.healer_mcp import HealerMCP


class TestMCPE2E:
    """End-to-end MCP workflow tests"""

    @pytest.fixture
    def router(self):
        """Create router instance"""
        return MCPRouter()

    @pytest.fixture
    def vortex(self):
        """Create VORTEX server"""
        return VortexMCP()

    @pytest.fixture
    def guardian(self):
        """Create GUARDIAN server"""
        return GuardianMCP()

    @pytest.fixture
    def oracle(self):
        """Create ORACLE server"""
        return OracleMCP()

    @pytest.fixture
    def genesis(self):
        """Create GENESIS server"""
        return GenesisMCP()

    @pytest.fixture
    def healer(self):
        """Create HEALER server"""
        return HealerMCP()

    def test_router_basic_flow(self, router):
        """Router should handle basic query"""
        query = "fix the bug in payment service"
        context = {"audit_logged": True, "backup_exists": True, "arousal": 0.3}

        result = asyncio.run(router.route_query(query, context))

        assert result is not None
        assert "decision" in result
        assert "agent" in result or result["decision"] == "blocked"

    def test_router_intent_classification(self, router):
        """Router should classify intents correctly"""
        test_cases = [
            ("fix the bug", "fix"),
            ("add new feature", "feature"),
            ("optimize code", "refactor"),
            ("deploy to prod", "deploy")
        ]

        for query, expected_intent in test_cases:
            intent, _ = router._classify_intent(query)
            assert intent == expected_intent

    def test_guardian_compliance_check(self, guardian):
        """GUARDIAN should catch violations"""
        result = guardian.handle_validate_policy(
            operation="export_data",
            context={"scope": "global"}  # G7 violation
        )
        assert result["success"] is False
        assert "G7" in str(result["result"]["violated_laws"]) or result["result"]["compliance_status"] == "FAIL"

    def test_vortex_health_check(self, vortex):
        """VORTEX health check should pass"""
        result = vortex.handle_health_check()
        assert result["success"]
        assert result["result"]["status"] in ["healthy", "degraded"]

    def test_vortex_canary_deploy(self, vortex):
        """VORTEX should execute canary deploy safely"""
        result = vortex.handle_canary_deploy(
            backend="payment-service",
            percent=5,
            constraints=["G1", "G7"]
        )
        assert result["success"]
        assert result["result"]["safe_to_deploy"]
        assert len(result["result"]["deployment_plan"]) == 5

    def test_oracle_classify_intent(self, oracle):
        """ORACLE should classify user intents"""
        result = oracle.handle_classify_intent(
            query="fix the crash in database",
            context={}
        )
        assert result["success"]
        assert result["result"]["intent"] in ["fix", "unknown"]

    def test_oracle_route_decision(self, oracle):
        """ORACLE should route to appropriate agent"""
        result = oracle.handle_route_decision(
            intent="fix",
            state={},
            available_agents=[
                {"name": "Auditor", "trust_score": 0.85},
                {"name": "Healer", "trust_score": 0.80}
            ]
        )
        assert result["success"]
        assert result["result"]["agent"] in ["Auditor", "Healer"]

    def test_genesis_session_save_recall(self, genesis):
        """GENESIS should save and recall sessions"""
        # Save
        save_result = genesis.handle_save_session(
            session_id="session-001",
            state={"user": "alice", "action": "deploy"}
        )
        assert save_result["success"]

        # Recall
        recall_result = genesis.handle_recall_memory(
            query="alice",
            scope="local"
        )
        assert recall_result["success"]
        assert len(recall_result["result"]["results"]) > 0

    def test_genesis_logging(self, genesis):
        """GENESIS should log events"""
        result = genesis.handle_log_event(
            event="User initiated deployment",
            level="info"
        )
        assert result["success"]
        assert "entry_id" in result["result"]

    def test_healer_health_report(self, healer):
        """HEALER should generate health report"""
        result = healer.handle_health_report()
        assert result["success"]
        assert "alert_level" in result["result"]
        assert result["result"]["alert_level"] in ["healthy", "warning", "critical"]

    def test_healer_auto_heal(self, healer):
        """HEALER should auto-heal anomalies"""
        result = healer.handle_self_heal(anomaly_type="high_arousal")
        assert result["success"]
        assert result["result"]["healed"] is True
        assert len(result["result"]["healing_steps"]) > 0

    def test_control_flow_compliance_blocked(self, router):
        """Router should block non-compliant operations"""
        query = "export all user data to cloud"
        context = {
            "export_scope": "global",  # Violates G7 Privacy
            "audit_logged": True
        }

        result = asyncio.run(router.route_query(query, context))

        # Should be blocked or escalated
        assert result["decision"] in [
            RoutingDecision.BLOCKED.value,
            RoutingDecision.ESCALATED.value
        ]

    def test_control_flow_crisis_mode(self, router):
        """Router should escalate to HEALER in crisis"""
        query = "deploy new version"
        context = {
            "arousal": 0.75,  # Crisis threshold > 0.7
            "audit_logged": True,
            "backup_exists": True
        }

        result = asyncio.run(router.route_query(query, context))

        assert result["decision"] == RoutingDecision.CRISIS.value
        assert result["agent"] == "HEALER"

    def test_control_flow_ts_blocked(self, router):
        """Router should block agents with TS < 0.6"""
        # Manually set low TS
        router.agents["VORTEX"]["trust_score"] = 0.55

        query = "deploy to production"
        context = {"audit_logged": True, "backup_exists": True}

        result = asyncio.run(router.route_query(query, context))

        # Should be escalated due to low TS
        if result.get("agent") == "VORTEX":
            assert result["decision"] == RoutingDecision.ESCALATED.value


class TestMCPMetrics:
    """Test metrics and statistics"""

    def test_router_stats(self):
        """Router should track statistics"""
        router = MCPRouter()
        stats = router.get_routing_stats()

        assert "total_queries" in stats
        assert "approved" in stats
        assert "blocked" in stats
        assert "success_rate" in stats

    def test_router_agent_health(self):
        """Router should report agent health"""
        router = MCPRouter()
        health = router.get_agent_health()

        assert "agents" in health
        assert "all_healthy" in health
        assert len(health["agents"]) == 5

    def test_guardian_audit_summary(self):
        """GUARDIAN should summarize audit log"""
        guardian = GuardianMCP()
        summary = guardian.get_audit_log_summary()

        assert "total_events" in summary
        assert "compliance_passes" in summary
        assert "compliance_failures" in summary

    def test_genesis_memory_stats(self):
        """GENESIS should report memory statistics"""
        genesis = GenesisMCP()
        stats = genesis.get_memory_stats()

        assert "total_sessions" in stats
        assert "total_log_entries" in stats
        assert "memory_used_mb" in stats

    def test_healer_recovery_stats(self):
        """HEALER should report recovery statistics"""
        healer = HealerMCP()
        stats = healer.get_recovery_stats()

        assert "total_alerts" in stats
        assert "current_health" in stats
        assert "detected_anomalies" in stats


class TestSAV:
    """Test Step Auto-Verification"""

    def test_vortex_sav_on_health_check(self):
        """VORTEX SAV should verify health check"""
        server = VortexMCP()
        result = server.handle_health_check()

        assert result["success"]
        assert result["checkpoint"]["is_complete"] is True

    def test_guardian_sav_on_policy_validation(self):
        """GUARDIAN SAV should verify policy"""
        server = GuardianMCP()
        result = server.handle_validate_policy(
            operation="export",
            context={"scope": "local"}  # Compliant
        )

        assert result["success"]
        assert len(result["checkpoint"]["checks_passed"]) > 0

    def test_genesis_sav_on_session_save(self):
        """GENESIS SAV should verify save"""
        server = GenesisMCP()
        result = server.handle_save_session(
            session_id="test-001",
            state={"data": "test"}
        )

        assert result["success"]
        assert result["checkpoint"]["is_complete"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
