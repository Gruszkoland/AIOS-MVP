"""
Chat Orchestrator — Master Orchestrator interface for user conversations

Processes user chat messages and routes to AI orchestrator for autonomous decisions:
- QUERY: Answer question (no action)
- DELEGATE: Route task to agent (autonomic - no approval needed)
- HEAL: Auto-heal detected issues (autonomic)
- CONTINUE: Resume previous task (autonomic)
- CLARIFY: Ask user for clarification
"""

import json
import logging
from typing import Any, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("adrion.uap.chat_orchestrator")


class ChatOrchestrator:
    """Routes chat messages to Master Orchestrator for autonomous decisions."""

    # Decision types
    DECISION_QUERY = "QUERY"
    DECISION_DELEGATE = "DELEGATE"
    DECISION_HEAL = "HEAL"
    DECISION_CONTINUE = "CONTINUE"
    DECISION_CLARIFY = "CLARIFY"

    # Autonomy keywords for LLM analysis
    HEAL_KEYWORDS = ["heal", "fix", "repair", "solve", "problem", "issue", "error", "crash", "hang"]
    QUERY_KEYWORDS = ["what", "how", "why", "status", "check", "info", "help", "explain"]
    DELEGATE_KEYWORDS = ["task", "do", "run", "execute", "schedule", "create", "deploy", "start"]

    def __init__(self, session_manager, db_instance, llm_backend=None, master_orchestrator=None):
        """
        Initialize chat orchestrator.

        Args:
            session_manager: SessionManager instance
            db_instance: PostgreSQL DB instance
            llm_backend: Optional LLM for semantic analysis (arbitrage/llm.py)
            master_orchestrator: Optional Master Orchestrator instance for decisions
        """
        self.sm = session_manager
        self.db = db_instance
        self.llm = llm_backend
        self.orchestrator = master_orchestrator

    def process_message(
        self,
        session_id: str,
        user_message: str,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Process user message and generate orchestrator response.

        Args:
            session_id: Session ID
            user_message: User input
            context: Optional context (e.g., {"platform": "vscode", "health_status": {...}})

        Returns:
            {
                "response": "AI response text",
                "decision_type": "QUERY|DELEGATE|HEAL|CONTINUE|CLARIFY",
                "action_id": "optional task ID if action taken",
                "confidence": 0.0-1.0,
                "genesis_logged": bool,
                "timestamp": ISO datetime
            }
        """
        context = context or {}
        timestamp = datetime.now().isoformat()

        try:
            # Step 1: Analyze intent
            decision_type, confidence, extracted_data = self.analyze_intent(user_message)

            # Step 2: Generate response based on decision type
            response = self._generate_response(decision_type, user_message, extracted_data)

            # Step 3: Execute action if needed (AUTONOMIC)
            action_id = None
            genesis_logged = False

            if decision_type == self.DECISION_DELEGATE:
                action_id = self._execute_delegate(session_id, user_message, extracted_data, context)
                genesis_logged = True

            elif decision_type == self.DECISION_HEAL:
                action_id = self._execute_heal(session_id, context)
                genesis_logged = True

            elif decision_type == self.DECISION_CONTINUE:
                action_id = self._execute_continue(session_id)
                genesis_logged = True

            # Step 4: Save to session chat history
            self.sm.save_chat_message(
                session_id=session_id,
                sender="user",
                message=user_message,
                response_type="input",
                genesis_logged=False,
            )

            self.sm.save_chat_message(
                session_id=session_id,
                sender="orchestrator",
                message=response,
                response_type=decision_type.lower(),
                genesis_logged=genesis_logged,
            )

            logger.info(
                f"💬 Chat message processed: {decision_type} (confidence: {confidence:.2f}, "
                f"action_id: {action_id or 'none'}, genesis_logged: {genesis_logged})"
            )

            return {
                "response": response,
                "decision_type": decision_type,
                "action_id": action_id,
                "confidence": confidence,
                "genesis_logged": genesis_logged,
                "timestamp": timestamp,
            }

        except Exception as e:
            logger.error(f"❌ Chat processing error: {str(e)}")
            response = f"⚠️ Error processing request: {str(e)}"
            self.sm.save_chat_message(
                session_id=session_id,
                sender="orchestrator",
                message=response,
                response_type="error",
                genesis_logged=False,
            )
            return {
                "response": response,
                "decision_type": "ERROR",
                "action_id": None,
                "confidence": 0.0,
                "genesis_logged": False,
                "timestamp": timestamp,
            }

    def analyze_intent(self, message: str) -> Tuple[str, float, Dict]:
        """
        Analyze user message intent using keyword/LLM heuristics.

        Returns:
            (decision_type, confidence, extracted_data)
        """
        message_lower = message.lower()

        # Keyword-based heuristics (fast path)
        if any(k in message_lower for k in self.HEAL_KEYWORDS):
            return self.DECISION_HEAL, 0.8, {}

        if any(k in message_lower for k in self.QUERY_KEYWORDS):
            return self.DECISION_QUERY, 0.85, {}

        if any(k in message_lower for k in self.DELEGATE_KEYWORDS):
            return self.DECISION_DELEGATE, 0.75, {"task_description": message}

        if "continue" in message_lower or "resume" in message_lower:
            return self.DECISION_CONTINUE, 0.9, {}

        # Default: query with lower confidence
        return self.DECISION_QUERY, 0.5, {}

    def _generate_response(self, decision_type: str, message: str, data: Dict) -> str:
        """Generate natural-language response based on decision type."""
        if decision_type == self.DECISION_QUERY:
            return f"I understand you're asking: '{message}'. I'm analyzing the system state to provide you with accurate information..."

        elif decision_type == self.DECISION_DELEGATE:
            return f"✅ I'm delegating this task to the appropriate agent for execution: '{message[:50]}...'"

        elif decision_type == self.DECISION_HEAL:
            return "🔧 Detected system issues. Activating self-healing protocol with the Healer agent..."

        elif decision_type == self.DECISION_CONTINUE:
            return "🔄 Resuming tasks from your previous session..."

        elif decision_type == self.DECISION_CLARIFY:
            return "❓ I need clarification. Could you provide more details?"

        else:
            return "I received your message but couldn't determine the intent. Please try again."

    def _execute_delegate(self, session_id: str, message: str, data: Dict, context: Dict) -> Optional[str]:
        """
        Execute task delegation (AUTONOMIC - no approval needed).

        Returns:
            task_id if successful, None otherwise
        """
        if not self.orchestrator:
            logger.warning("❌ Master Orchestrator not available for delegation")
            return None

        try:
            # Call master orchestrator with KROK 1-4
            result = self.orchestrator.execute_master_loop(
                task_description=message,
                agent_hint=None,
                dry_run=False,
                budget_max=1000,
            )

            task_id = result.get("task_id")
            logger.info(f"✅ Task delegated autonomously: {task_id}")

            # Save to session
            self.sm.save_task_to_session(
                session_id=session_id,
                task_id=task_id,
                status="executing",
                priority=1,
            )

            return task_id

        except Exception as e:
            logger.error(f"❌ Delegation failed: {str(e)}")
            return None

    def _execute_heal(self, session_id: str, context: Dict) -> Optional[str]:
        """
        Execute autonomous healing (AUTONOMIC - no approval).

        Returns:
            task_id of healing task
        """
        if not self.orchestrator:
            logger.warning("❌ Master Orchestrator not available for healing")
            return None

        try:
            # Trigger Healer protocol
            result = self.orchestrator.execute_master_loop(
                task_description="Perform system health check and auto-heal any detected issues",
                agent_hint="Healer",
                dry_run=False,
                budget_max=500,
            )

            task_id = result.get("task_id")
            logger.info(f"🔧 Auto-heal initiated autonomously: {task_id}")

            self.sm.save_task_to_session(
                session_id=session_id,
                task_id=task_id,
                status="executing",
                priority=2,
            )

            return task_id

        except Exception as e:
            logger.error(f"❌ Healing failed: {str(e)}")
            return None

    def _execute_continue(self, session_id: str) -> Optional[str]:
        """
        Resume incomplete task from previous session (AUTONOMIC).

        Returns:
            task_id of resumed task, None if no tasks to resume
        """
        try:
            # Get tasks ready for resume
            resume_tasks = self.sm.get_resumed_tasks(session_id)

            if not resume_tasks:
                logger.info(f"ℹ️  No tasks to resume in session {session_id}")
                return None

            # Resume highest priority task
            task_to_resume = resume_tasks[0]
            task_id = task_to_resume["task_id"]

            # Retrieve original task description from DB
            task = self.db.get_task(task_id)
            if not task:
                logger.warning(f"⚠️  Task not found for resume: {task_id}")
                return None

            # Re-delegate with resume context
            if self.orchestrator:
                result = self.orchestrator.execute_master_loop(
                    task_description=f"[RESUMED] {task['task_description']}",
                    agent_hint=task["assigned_agent"],  # Use previous agent
                    dry_run=False,
                    budget_max=task.get("budget_max", 1000),
                )
                new_task_id = result.get("task_id")
                logger.info(f"🔄 Task resumed: {task_id} → {new_task_id}")

                # Mark as resumed
                self.sm.mark_task_resumed(task_id)
                return new_task_id

            return task_id

        except Exception as e:
            logger.error(f"❌ Resume failed: {str(e)}")
            return None

    # ┌─────────────────────────────────────────────────────────────────────┐
    # │ UTILITIES                                                           │
    # └─────────────────────────────────────────────────────────────────────┘

    def get_chat_context(self, session_id: str) -> Dict[str, Any]:
        """Get context for chat (recent messages, system state)."""
        history = self.sm.get_chat_history(session_id, limit=20)
        return {
            "recent_messages": history[-5:],  # Last 5 messages
            "total_messages": len(history),
        }

    def suggest_next_actions(self, session_id: str) -> List[str]:
        """Suggest next actions based on chat history and system state."""
        suggestions = [
            "Check system health",
            "View task status",
            "Resume previous work",
            "Ask for help",
        ]
        return suggestions
