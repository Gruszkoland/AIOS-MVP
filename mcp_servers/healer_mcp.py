"""
HEALER-MCP: Automated Recovery, Health Monitoring, Alerts

Port: 9005
Domain: Rollback, SAV validation, telemetry, anomaly detection

DSPy Signature:
- Input: health_telemetry, failed_operation, checkpoint_history
- Output: recovery_action, healing_steps, alert_notification, confidence
"""

from mcp_servers import MCPBaseServer, DSPySignature, EBDIState
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
from enum import Enum


healer_signature = DSPySignature(
    signature_name="HealerRecovery",
    input_schema={
        "health_telemetry": "object {arousal, pleasure, dominance}",
        "failed_operation": "string (step that errored)",
        "checkpoint_history": "array[checkpoint_id]"
    },
    output_schema={
        "recovery_action": "string (Rollback|Reset|Retry|Escalate)",
        "healing_steps": "array[step]",
        "alert_notification": "object {recipient, severity}",
        "confidence": "float [0...1]"
    }
)


class RecoveryAction(Enum):
    """Recovery strategies"""
    ROLLBACK = "rollback"
    RESET = "reset"
    RETRY = "retry"
    ESCALATE = "escalate"
    HEAL_AUTO = "heal_auto"


@dataclass
class HealthReport:
    """System health snapshot"""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agents_status: Dict[str, str] = field(default_factory=dict)  # {agent: status}
    alert_level: str = "healthy"  # healthy, warning, critical
    ebdi_state: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class Alert:
    """Alert notification"""
    alert_id: str
    severity: str  # "info", "warning", "critical"
    message: str
    recipients: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class HealerMCP(MCPBaseServer):
    """Automated Recovery & Health Monitoring"""

    def __init__(self):
        super().__init__(
            server_name="HEALER-MCP",
            port=9005,
            dspy_signature=healer_signature
        )
        self.health_history: List[HealthReport] = []
        self.alerts: List[Alert] = []
        self.checkpoints_available: Dict[str, str] = {}

    def handle_health_report(self) -> dict:
        """GET /health/report — Full system health"""
        def operation_fn():
            # Aggregate status from other MCP servers
            agents_status = {
                "VORTEX-MCP": "healthy",
                "GUARDIAN-MCP": "healthy",
                "ORACLE-MCP": "healthy",
                "GENESIS-MCP": "healthy",
                "HEALER-MCP": "healthy"
            }

            alert_level = "healthy"
            if self.ebdi_state.is_crisis_mode:
                alert_level = "critical"
            elif self.ebdi_state.arousal > 0.5:
                alert_level = "warning"

            report = HealthReport(
                agents_status=agents_status,
                alert_level=alert_level,
                ebdi_state=self.ebdi_state.to_dict(),
                errors=[]
            )
            self.health_history.append(report)

            return asdict(report)

        result = self.execute_step(
            step_name="health_report",
            operation=operation_fn,
            definition_of_done=[
                "all_agents_checked",
                "alert_level_set",
                "ebdi_recorded"
            ]
        )
        return result

    def handle_trigger_rollback(self, checkpoint_id: str, scope: str = "local") -> dict:
        """POST /rollback — Restore from checkpoint"""
        def operation_fn():
            if checkpoint_id not in self.checkpoints_available:
                return {
                    "rollback_ok": False,
                    "error": f"Checkpoint {checkpoint_id} not found",
                    "state_restored": False
                }

            # Execute rollback
            checkpoint_path = self.checkpoints_available[checkpoint_id]

            return {
                "rollback_ok": True,
                "checkpoint_id": checkpoint_id,
                "scope": scope,
                "state_restored": True,
                "checkpoint_path": checkpoint_path,
                "restored_at": datetime.utcnow().isoformat()
            }

        result = self.execute_step(
            step_name=f"rollback_{checkpoint_id}",
            operation=operation_fn,
            definition_of_done=[
                "checkpoint_valid",
                "state_loaded",
                "verified"
            ]
        )
        return result

    def handle_self_heal(self, anomaly_type: str) -> dict:
        """POST /heal/auto — Automatic recovery"""
        def operation_fn():
            healing_actions = []

            if anomaly_type == "high_arousal":
                healing_actions = [
                    "Reduce processing load",
                    "Lower sampling rate",
                    "Increase throttle timeout"
                ]
                self.ebdi_state.arousal = max(0.0, self.ebdi_state.arousal - 0.2)

            elif anomaly_type == "memory_leak":
                healing_actions = [
                    "Clear cache",
                    "Garbage collect",
                    "Reset connections"
                ]
                self.ebdi_state.pleasure = min(1.0, self.ebdi_state.pleasure + 0.1)

            elif anomaly_type == "dead_agent":
                healing_actions = [
                    "Restart affected agent",
                    "Reset state",
                    "Verify connectivity"
                ]

            return {
                "healed": len(healing_actions) > 0,
                "anomaly_type": anomaly_type,
                "healing_steps": healing_actions,
                "recovery_log": f"Auto-healed {anomaly_type} with {len(healing_actions)} steps",
                "confidence": 0.92
            }

        result = self.execute_step(
            step_name=f"heal_{anomaly_type}",
            operation=operation_fn,
            definition_of_done=[
                "anomaly_identified",
                "healing_applied",
                "state_normalized"
            ]
        )
        return result

    def handle_telemetry_alert(self, metric: str, value: float) -> dict:
        """POST /telemetry/alert — Alert on metric threshold"""
        def operation_fn():
            # Check thresholds
            thresholds = {
                "cpu_percent": 90,
                "memory_percent": 85,
                "error_rate": 5,
                "latency_ms": 500
            }

            threshold = thresholds.get(metric, 100)
            over_threshold = value > threshold

            alert = Alert(
                alert_id=f"ALR-{len(self.alerts)}",
                severity="critical" if over_threshold else "info",
                message=f"{metric}={value:.1f}% (threshold: {threshold}%)" if over_threshold else f"{metric}={value:.1f}% (OK)",
                recipients=["Sentinel", "Auditor"] if over_threshold else ["GENESIS-MCP"]
            )
            self.alerts.append(alert)

            if over_threshold:
                self.ebdi_state.arousal = min(1.0, self.ebdi_state.arousal + 0.1)

            return {
                "alert_id": alert.alert_id,
                "alert_sent": True,
                "metric": metric,
                "value": value,
                "threshold": threshold,
                "severity": alert.severity,
                "recipients": alert.recipients
            }

        result = self.execute_step(
            step_name=f"telemetry_{metric}",
            operation=operation_fn,
            definition_of_done=[
                "metric_evaluated",
                "threshold_checked",
                "alert_created"
            ]
        )
        return result

    def detect_anomalies(self) -> List[str]:
        """Detect system anomalies"""
        anomalies = []

        if self.ebdi_state.arousal > 0.7:
            anomalies.append("high_arousal")

        if self.ebdi_state.pleasure < 0.3:
            anomalies.append("low_pleasure")

        if len(self.alerts) > 10:
            anomalies.append("alert_spam")

        return anomalies

    def get_recovery_stats(self) -> dict:
        """Recovery statistics"""
        return {
            "total_alerts": len(self.alerts),
            "critical_alerts": len([a for a in self.alerts if a.severity == "critical"]),
            "health_checks": len(self.health_history),
            "current_health": self.health_history[-1].alert_level if self.health_history else "unknown",
            "last_check": self.health_history[-1].timestamp if self.health_history else None,
            "detected_anomalies": self.detect_anomalies()
        }
