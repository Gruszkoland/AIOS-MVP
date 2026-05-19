"""
MCP Deployment Configuration

Configuration for Phase 3 testing and canary deployment
"""

import json
from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class CanaryStage(Enum):
    """Canary deployment stages"""
    SMOKE_TEST = "smoke_test"
    KPI_VALIDATION = "kpi_validation"
    CANARY_5 = "canary_5"
    CANARY_50 = "canary_50"
    CANARY_100 = "canary_100"
    ROLLBACK = "rollback"


@dataclass
class MCPServerConfig:
    """MCP Server configuration"""
    name: str
    port: int
    role: str
    health_check_endpoint: str = "/health"
    health_check_interval: int = 10
    health_check_timeout: int = 5
    critical: bool = True


@dataclass
class KPIThreshold:
    """KPI threshold definition"""
    metric_name: str
    target_value: float
    operator: str  # "gte", "lte", "eq"
    severity: str  # "critical", "warning"


# ════════════════════════════════════════════════════════════════════════════
# MCP SERVER CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

MCP_SERVERS = {
    "MCP-ROUTER": MCPServerConfig(
        name="MCP-ROUTER",
        port=9000,
        role="Central Orchestration",
        critical=True
    ),
    "VORTEX-MCP": MCPServerConfig(
        name="VORTEX-MCP",
        port=9001,
        role="Harmonic Orchestration @ 174Hz",
        critical=True
    ),
    "GUARDIAN-MCP": MCPServerConfig(
        name="GUARDIAN-MCP",
        port=9002,
        role="Security & Compliance (9 Laws)",
        critical=True
    ),
    "ORACLE-MCP": MCPServerConfig(
        name="ORACLE-MCP",
        port=9003,
        role="162D Decision Routing",
        critical=True
    ),
    "GENESIS-MCP": MCPServerConfig(
        name="GENESIS-MCP",
        port=9004,
        role="State Management & RAG",
        critical=True
    ),
    "HEALER-MCP": MCPServerConfig(
        name="HEALER-MCP",
        port=9005,
        role="Recovery & Monitoring",
        critical=False
    ),
}

# ════════════════════════════════════════════════════════════════════════════
# KPI THRESHOLDS FOR GATE
# ════════════════════════════════════════════════════════════════════════════

KPI_THRESHOLDS = [
    KPIThreshold(
        metric_name="routing_success_rate",
        target_value=0.95,
        operator="gte",
        severity="critical"
    ),
    KPIThreshold(
        metric_name="routing_error_rate",
        target_value=0.05,
        operator="lte",
        severity="critical"
    ),
    KPIThreshold(
        metric_name="routing_latency_p99_ms",
        target_value=500.0,
        operator="lte",
        severity="warning"
    ),
    KPIThreshold(
        metric_name="trust_score_average",
        target_value=0.75,
        operator="gte",
        severity="warning"
    ),
    KPIThreshold(
        metric_name="health_check_success_rate",
        target_value=1.0,
        operator="gte",
        severity="critical"
    ),
    KPIThreshold(
        metric_name="compliance_pass_rate",
        target_value=0.98,
        operator="gte",
        severity="critical"
    ),
]

# ════════════════════════════════════════════════════════════════════════════
# CANARY DEPLOYMENT STAGES
# ════════════════════════════════════════════════════════════════════════════

CANARY_STAGES = {
    CanaryStage.SMOKE_TEST: {
        "description": "Quick health check on all 6 MCP servers",
        "duration_seconds": 30,
        "traffic_percent": 0,
        "fail_fast": True,
        "script": "scripts/mcp-testing/smoke-test.ps1"
    },
    CanaryStage.KPI_VALIDATION: {
        "description": "Validate MCP metrics against KPI thresholds",
        "duration_seconds": 120,
        "traffic_percent": 0,
        "fail_fast": True,
        "script": "scripts/mcp-testing/kpi-gate-validation.ps1"
    },
    CanaryStage.CANARY_5: {
        "description": "Route 5% traffic to new MCP tier",
        "duration_seconds": 600,
        "traffic_percent": 5,
        "fail_fast": False,
        "success_criteria": "error_rate <= 2%",
        "rollback_condition": "error_rate > 5% for 2 minutes"
    },
    CanaryStage.CANARY_50: {
        "description": "Route 50% traffic to new MCP tier",
        "duration_seconds": 600,
        "traffic_percent": 50,
        "fail_fast": False,
        "success_criteria": "error_rate <= 1.5%",
        "rollback_condition": "error_rate > 3% for 2 minutes"
    },
    CanaryStage.CANARY_100: {
        "description": "Route 100% traffic to new MCP tier (full rollout)",
        "duration_seconds": 300,
        "traffic_percent": 100,
        "fail_fast": False,
        "success_criteria": "success_rate >= 95%"
    },
}

# ════════════════════════════════════════════════════════════════════════════
# TEST SCENARIOS
# ════════════════════════════════════════════════════════════════════════════

TEST_SCENARIOS = [
    {
        "name": "Simple Fix Query",
        "query": "fix the bug in payment service",
        "context": {
            "audit_logged": True,
            "backup_exists": True,
            "arousal": 0.3
        },
        "expected_intent": "fix",
        "expected_agent": ["HEALER", "AUDITOR", "ARCHITECT"],
        "expected_compliance": "PASS"
    },
    {
        "name": "Feature Implementation",
        "query": "add new dashboard widget",
        "context": {
            "audit_logged": True,
            "backup_exists": True,
            "arousal": 0.4
        },
        "expected_intent": "feature",
        "expected_agent": ["ARCHITECT", "SAP", "ORACLE"],
        "expected_compliance": "PASS"
    },
    {
        "name": "Security Violation — Export",
        "query": "export all user data to cloud",
        "context": {
            "export_scope": "global",
            "audit_logged": True
        },
        "expected_intent": "export",
        "expected_compliance": "FAIL",
        "expected_violation": "G7_Privacy"
    },
    {
        "name": "Crisis Mode — High Arousal",
        "query": "deploy to production NOW",
        "context": {
            "audit_logged": True,
            "backup_exists": True,
            "arousal": 0.8
        },
        "expected_agent": "HEALER",
        "expected_behavior": "escalate"
    },
    {
        "name": "Low Trust Score Agent",
        "query": "execute critical operation",
        "context": {
            "agent_ts": 0.55,
            "audit_logged": True
        },
        "expected_behavior": "escalate_or_block"
    },
]

# ════════════════════════════════════════════════════════════════════════════
# DEPLOYMENT CHECKLIST
# ════════════════════════════════════════════════════════════════════════════

DEPLOYMENT_CHECKLIST = [
    {
        "item": "Docker MCP tier deployment",
        "command": "docker-compose -f docker-compose.mcp-tier.yml up -d",
        "verification": "All 6 containers running health checks GREEN"
    },
    {
        "item": "Smoke test (quick health check)",
        "command": "powershell scripts/mcp-testing/smoke-test.ps1",
        "verification": "All 6 servers respond to /health endpoint"
    },
    {
        "item": "Full cluster validation",
        "command": "powershell scripts/mcp-testing/validate-mcp-cluster.ps1",
        "verification": "Health + Integration + Compliance tests PASS"
    },
    {
        "item": "KPI gate validation",
        "command": "powershell scripts/mcp-testing/kpi-gate-validation.ps1",
        "verification": "All KPI thresholds met or exceeded"
    },
    {
        "item": "Unit tests",
        "command": "pytest tests/mcp/test_mcp_signatures.py -v",
        "verification": "All signature validation tests PASS"
    },
    {
        "item": "E2E integration tests",
        "command": "pytest tests/mcp/test_mcp_e2e.py -v",
        "verification": "All routing + compliance + recovery tests PASS"
    },
    {
        "item": "Canary 5% deployment",
        "command": "Manual: Route 5% to MCP tier",
        "verification": "Error rate <= 2% for 10 minutes"
    },
    {
        "item": "Canary 50% deployment",
        "command": "Manual: Route 50% to MCP tier",
        "verification": "Error rate <= 1.5% for 10 minutes"
    },
    {
        "item": "Full rollout (100%)",
        "command": "Manual: Route 100% to MCP tier",
        "verification": "Success rate >= 95%, all agents healthy"
    },
    {
        "item": "Post-deployment monitoring",
        "command": "Monitor: Genesis Record + KPI dashboard",
        "verification": "Stable operation for 24 hours"
    },
]

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION EXPORT
# ════════════════════════════════════════════════════════════════════════════

def get_config_json() -> str:
    """Export all config to JSON"""
    config = {
        "mcp_servers": {k: v.__dict__ for k, v in MCP_SERVERS.items()},
        "kpi_thresholds": [t.__dict__ for t in KPI_THRESHOLDS],
        "canary_stages": {k.name: v for k, v in CANARY_STAGES.items()},
        "test_scenarios": TEST_SCENARIOS,
        "deployment_checklist": DEPLOYMENT_CHECKLIST
    }
    return json.dumps(config, indent=2, default=str)


if __name__ == "__main__":
    print(get_config_json())
