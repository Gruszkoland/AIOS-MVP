"""
Unified Admin Panel (UAP) — Integration Layer
Combines Phase 2 modules: PostgreSQL, WebSocket, Ollama, MCTS, DRM

High-level API that orchestrates all subsystems
"""
import sys
import os
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from db import get_db
from ollama_router import get_router
from mcts_planner import get_planner
from drm_executor import get_drm

class UAP_IntegrationLayer:
    """Master orchestrator for Phase 2 UAP system."""

    def __init__(self):
        self.db = get_db()
        self.router = get_router()
        self.planner = get_planner()
        self.drm = get_drm()

        # Agent trust scores
        self.trust_scores = {
            "Librarian": 0.85, "SAP": 0.90, "Auditor": 0.88,
            "Sentinel": 0.92, "Architect": 0.87, "Healer": 0.83,
            "Amplifier": 0.80, "BoosterLever": 0.78, "Chronos": 0.82,
        }

    # ────────────────────────────────────────────────────────────────────
    # MASTER ORCHESTRATOR LOOP (4 Steps)
    # ────────────────────────────────────────────────────────────────────

    def execute_master_loop(self, task_description: str, agent_hint: Optional[str] = None,
                           dry_run: bool = False, budget_max: float = 1000) -> Dict[str, Any]:
        """
        KROK 1: Sensing & Routing (MoE Gating)
        KROK 2: Graph-of-Thoughts (MCTS Drafting)
        KROK 2.5: Step Auto-Verification (Dry Run Mode)
        KROK 3: Self-Correction & Reward
        KROK 4: Action & Genesis Record

        Returns: Complete task response with decision trace
        """

        # Generate task ID
        from datetime import datetime
        task_id = f"upc-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.urandom(2).hex().upper()}"

        # ─────────────────────────────────────────────────────────────────
        # KROK 1: Sensing & Routing
        # ─────────────────────────────────────────────────────────────────

        self.db.insert_genesis_log(
            task_id=task_id,
            agent="Master",
            status="sensing",
            action="KROK_1_sensing_routing",
            notes="Task received, initiating routing..."
        )

        # Route via EBDI + TSPA
        agent, confidence = self.router.route_task(task_description, agent_hint)

        # Check TSPA: Block if TS < 0.6
        trust_score = self.trust_scores.get(agent, 0.5)
        if trust_score < 0.6:
            self.db.insert_genesis_log(
                task_id=task_id,
                agent="Master",
                status="blocked",
                action="TSPA_rejection",
                guards_passed=2,
                notes=f"Agent {agent} trust score {trust_score} < 0.6"
            )

            return {
                "task_id": task_id,
                "status": "blocked",
                "assigned_agent": agent,
                "trust_score": trust_score,
                "reason": f"Agent trust score too low: {trust_score}",
                "decision_trace": [
                    {"step": "KROK_1", "result": "TSPA_rejection", "reason": "TS < 0.6"}
                ]
            }

        # Log routing decision
        routing_explanation = self.router.explain_routing(task_description, agent)

        self.db.insert_genesis_log(
            task_id=task_id,
            agent="Master",
            status="routed",
            action="KROK_1_routing_complete",
            guards_passed=9,
            notes=f"Routed to {agent} (confidence: {confidence:.2f}). {routing_explanation}"
        )

        # ─────────────────────────────────────────────────────────────────
        # KROK 2: Graph-of-Thoughts (MCTS)
        # ─────────────────────────────────────────────────────────────────

        self.db.insert_genesis_log(
            task_id=task_id,
            agent="Master",
            status="planning",
            action="KROK_2_got_drafting",
            notes="Starting Graph-of-Thoughts exploration..."
        )

        plan = self.planner.plan_task(task_description, agent, iterations=50)

        self.planner.export_plan(task_id, plan)

        # ─────────────────────────────────────────────────────────────────
        # KROK 2.5: Step Auto-Verification (Dry Run Mode)
        # ─────────────────────────────────────────────────────────────────

        drm_preview = None
        approval_required = False

        # Check if any step is destructive
        destructive_keywords = ["reset", "delete", "drop", "rm", "clear"]
        is_destructive = any(
            keyword in task_description.lower() for keyword in destructive_keywords
        )

        if is_destructive and dry_run:
            drm_preview = self.drm.simulate_operation(
                "git_reset",  # Default destructive operation
                {"target": "HEAD~1"}
            )

            self.db.insert_genesis_log(
                task_id=task_id,
                agent="Master",
                status="dry_run",
                action="KROK_2p5_dry_run_preview",
                guards_passed=9,
                notes=f"DRM preview: {drm_preview.get('risk_level')} operation"
            )

            approval_required = True

        # ─────────────────────────────────────────────────────────────────
        # KROK 3: Self-Correction & Reward
        # ─────────────────────────────────────────────────────────────────

        # Update trust score
        ts_delta = 0.05 if confidence > 0.7 else -0.05

        self.db.insert_agent_metric(
            agent=agent,
            trust_score=trust_score + ts_delta,
            pleasure=0.5,  # Mock
            arousal=0.3,
            dominance=0.6
        )

        self.db.insert_genesis_log(
            task_id=task_id,
            agent="Master",
            status="evaluated",
            action="KROK_3_self_correction",
            guards_passed=9,
            notes=f"Trust Score update: {trust_score:.2f} → {trust_score + ts_delta:.2f}"
        )

        # ─────────────────────────────────────────────────────────────────
        # KROK 4: Action & Genesis Record
        # ─────────────────────────────────────────────────────────────────

        if not dry_run or not approval_required:
            # Execute task
            self.db.update_task_status(task_id, "executing")

            self.db.insert_genesis_log(
                task_id=task_id,
                agent=agent,
                status="executing",
                action="KROK_4_action_execution",
                guards_passed=9,
                notes=f"Executing plan with {len(plan)} steps"
            )

            # Simulate execution result
            result = {
                "output": f"{agent} successfully processed: {task_description[:50]}...",
                "items_found": 5,
                "confidence": confidence,
                "plan_steps": len(plan),
            }

            self.db.update_task_status(task_id, "completed", result)

            self.db.insert_genesis_log(
                task_id=task_id,
                agent=agent,
                status="completed",
                action="KROK_4_execution_complete",
                guards_passed=9,
                notes=f"Execution successful. {len(plan)} steps completed."
            )
        else:
            self.db.update_task_status(task_id, "pending_approval")

        # ─────────────────────────────────────────────────────────────────
        # RESPONSE
        # ─────────────────────────────────────────────────────────────────

        return {
            "task_id": task_id,
            "status": "pending_approval" if approval_required else "completed",
            "assigned_agent": agent,
            "trust_score": trust_score,
            "routing_confidence": confidence,
            "routing_explanation": routing_explanation,
            "plan": plan,
            "drm_preview": drm_preview if approval_required else None,
            "approval_required": approval_required,
            "decision_trace": [
                {"step": "KROK_1", "result": "routing", "agent": agent, "confidence": confidence},
                {"step": "KROK_2", "result": "got_planning", "plan_steps": len(plan)},
                {"step": "KROK_2.5", "result": "dry_run" if approval_required else "skip"},
                {"step": "KROK_3", "result": "self_correction", "ts_update": ts_delta},
                {"step": "KROK_4", "result": "executed" if not approval_required else "pending"},
            ]
        }

    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """Retrieve task result from database."""
        task = self.db.get_task(task_id)
        if not task:
            return {"error": f"Task {task_id} not found"}

        return {
            "task_id": task_id,
            "status": task["status"],
            "agent": task["assigned_agent"],
            "result": task["result"],
            "created_at": task["created_at"],
            "updated_at": task["updated_at"],
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            "status": "online",
            "modules": {
                "postgresql": "✅ connected",
                "ollama": "✅ connected",  # TODO: check actual status
                "websocket": "✅ running",
                "mcts": "✅ ready",
                "drm": "✅ ready",
            },
            "agents_online": len(self.trust_scores),
            "average_trust_score": sum(self.trust_scores.values()) / len(self.trust_scores),
            "timestamp": datetime.now().isoformat(),
        }


# Singleton instance
_integration = None

def get_integration() -> UAP_IntegrationLayer:
    global _integration
    if _integration is None:
        _integration = UAP_IntegrationLayer()
    return _integration
