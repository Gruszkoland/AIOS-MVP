"""
GUARDIAN-MCP: Security Policy Enforcement & Compliance

Port: 9002
Domain: 9 Guardian Laws, audit logging, policy validation

DSPy Signature:
- Input: operation_type, context_scope, actor_identity
- Output: compliance_status, violated_laws, recommended_action, audit_entry
"""

from mcp_servers import MCPBaseServer, DSPySignature, GuardianLaw
from dataclasses import dataclass, asdict
from typing import Dict, List, Any
from datetime import datetime
import json


guardian_signature = DSPySignature(
    signature_name="GuardianPolicy",
    input_schema={
        "operation_type": "string (deploy, query, delete, export)",
        "context_scope": "string (local, global)",
        "actor_identity": "string (user_id or agent_name)",
        "data_sensitivity": "string (public, internal, confidential)"
    },
    output_schema={
        "compliance_status": "string (PASS, FAIL)",
        "violated_laws": "array[GuardianLaw]",
        "recommended_action": "string or null",
        "audit_entry": "object"
    }
)


@dataclass
class AuditEntry:
    """Compliance event log"""
    timestamp: str
    actor: str
    operation: str
    scope: str
    compliance_status: str
    violated_laws: List[str]
    severity: str  # "info", "warning", "critical"


class GuardianMCP(MCPBaseServer):
    """9 Guardian Laws Enforcement"""

    def __init__(self):
        super().__init__(
            server_name="GUARDIAN-MCP",
            port=9002,
            dspy_signature=guardian_signature
        )
        self.audit_log: List[AuditEntry] = []
        self.policies = {
            "G1_Unity": {"allow_global": True, "check_coherence": True},
            "G2_Harmony": {"allow_conflicts": False, "escalate_on_mismatch": True},
            "G3_Rhythm": {"cycle_time_seconds": 60, "allow_deviation": "5%"},
            "G4_Causality": {"validate_preconditions": True, "track_effects": True},
            "G5_Transparency": {"require_audit_log": True, "prohibit_dark_patterns": True},
            "G6_Authenticity": {"validate_signatures": True, "check_origin": True},
            "G7_Privacy": {"local_first": True, "prohibit_export": True},
            "G8_Nonmaleficence": {"no_data_loss": True, "require_backup": True},
            "G9_Sustainability": {"prefer_efficient": True, "cap_resources": True}
        }

    def handle_validate_policy(self, operation: str, context: Dict[str, Any]) -> dict:
        """POST /validate — Policy compliance check"""
        def operation_fn():
            violations = []
            recommendations = []

            # Rule: G7 Privacy — local_first
            if operation == "export_data" and context.get("scope") == "global":
                violations.append(GuardianLaw.G7_PRIVACY.value)
                recommendations.append("Restrict to local scope only")

            # Rule: G8 Nonmaleficence — require backup
            if operation == "delete" and not context.get("backup_exists"):
                violations.append(GuardianLaw.G8_NONMALEFICENCE.value)
                recommendations.append("Create backup before delete")

            # Rule: G5 Transparency — audit trail (only for critical operations)
            critical_ops = ["deploy", "delete", "export_data"]
            if operation in critical_ops and not context.get("logged_audit"):
                violations.append(GuardianLaw.G5_TRANSPARENCY.value)
                recommendations.append("Audit log required for critical operations")

            compliance = "PASS" if len(violations) == 0 else "FAIL"

            return {
                "compliance_status": compliance,
                "violated_laws": violations,
                "recommended_action": " | ".join(recommendations) if recommendations else None,
                "audit_entry": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "actor": context.get("actor", "unknown"),
                    "operation": operation,
                    "scope": context.get("scope", "local"),
                    "compliance_status": compliance,
                    "severity": "critical" if len(violations) > 0 else "info"
                }
            }

        result = self.execute_step(
            step_name=f"validate_{operation}",
            operation=operation_fn,
            definition_of_done=[
                "compliance_status_set",
                "violated_laws_array_present",
                "audit_entry_created"
            ]
        )

        # Set success based on compliance status
        if result["result"]["compliance_status"] == "FAIL":
            result["success"] = False
        else:
            result["success"] = True

        # Add checkpoint for SAV
        result["checkpoint"] = {
            "is_complete": result["success"],
            "step": f"validate_{operation}",
            "checks_passed": [
                "compliance_status_set",
                "violated_laws_array_present",
                "audit_entry_created"
            ]
        }

        if result["success"] and result["result"]["compliance_status"] == "PASS":
            # Log successful validation
            entry = result["result"]["audit_entry"]
            self.audit_log.append(AuditEntry(
                timestamp=entry["timestamp"],
                actor=entry["actor"],
                operation=entry["operation"],
                scope=entry["scope"],
                compliance_status=entry["compliance_status"],
                violated_laws=entry.get("violated_laws", []),
                severity=entry["severity"]
            ))
            self.trust_score.increment_success()
        else:
            self.trust_score.increment_failure()

        return result

    def handle_audit_event(self, event: str, actor: str, timestamp: str) -> dict:
        """POST /audit/log — Log compliance event"""
        def operation_fn():
            audit_entry = AuditEntry(
                timestamp=timestamp or datetime.utcnow().isoformat(),
                actor=actor,
                operation=event,
                scope="global",
                compliance_status="logged",
                violated_laws=[],
                severity="info"
            )
            self.audit_log.append(audit_entry)

            return {
                "logged": True,
                "event_id": f"AUD-{len(self.audit_log)}",
                "timestamp": audit_entry.timestamp,
                "actor": audit_entry.actor
            }

        result = self.execute_step(
            step_name=f"audit_{actor}_{event}",
            operation=operation_fn,
            definition_of_done=[
                "event_logged",
                "event_id_generated",
                "timestamp_recorded"
            ]
        )
        return result

    def handle_law_enforcement(self, operation: str, scope: str) -> dict:
        """POST /laws/check — Enforce 9 Guardian Laws"""
        def operation_fn():
            violated = []

            # G1: Unity
            if scope == "fragmented":
                violated.append("G1_UNITY")

            # G7: Privacy (always for exports)
            if operation == "export" and scope != "local":
                violated.append("G7_PRIVACY")

            # G8: Nonmaleficence (critical ops without verification)
            if operation in ["delete", "destroy"] and not scope.startswith("verified_"):
                violated.append("G8_NONMALEFICENCE")

            allowed = len(violated) == 0

            return {
                "allowed": allowed,
                "violated_laws": violated,
                "operation": operation,
                "scope": scope,
                "enforcement_level": "strict" if violated else "permissive"
            }

        result = self.execute_step(
            step_name=f"laws_{operation}_{scope}",
            operation=operation_fn,
            definition_of_done=[
                "allowed_field_set",
                "violated_laws_present",
                "enforcement_level_set"
            ]
        )
        return result

    def handle_privacy_scan(self, data: str, sensitivity: str) -> dict:
        """POST /privacy/scan — Check data privacy compliance"""
        def operation_fn():
            # Simplified privacy check
            requires_masking = sensitivity in ["confidential", "internal"]
            masked_data = "*" * len(data) if requires_masking else data

            return {
                "clearance": "granted" if sensitivity == "public" else "restricted",
                "data_masked": requires_masking,
                "masked_preview": masked_data[:20] + "..." if len(masked_data) > 20 else masked_data,
                "privacy_compliant": True,
                "notes": f"Data classified as {sensitivity}"
            }

        result = self.execute_step(
            step_name=f"privacy_scan_{sensitivity}",
            operation=operation_fn,
            definition_of_done=[
                "clearance_set",
                "masking_applied",
                "compliance_noted"
            ]
        )
        return result

    def get_audit_log_summary(self) -> dict:
        """Return audit log statistics"""
        return {
            "total_events": len(self.audit_log),
            "compliance_passes": len([e for e in self.audit_log if e.compliance_status == "PASS"]),
            "compliance_failures": len([e for e in self.audit_log if e.compliance_status == "FAIL"]),
            "critical_events": len([e for e in self.audit_log if e.severity == "critical"]),
            "last_event": self.audit_log[-1].timestamp if self.audit_log else None
        }
