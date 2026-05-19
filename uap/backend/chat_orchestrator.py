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
from typing import Any, Dict, List, Optional, Tuple
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
    HEAL_KEYWORDS = ["heal", "fix", "repair", "solve", "crash", "hang"]
    QUERY_KEYWORDS = ["what", "how", "why", "status", "check", "info", "help", "explain"]
    DELEGATE_KEYWORDS = ["task", "run", "execute", "schedule", "create", "deploy", "start"]

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
        # U4: Lazy-init RAG context optimizer
        self._rag = None

    def process_message(
        self,
        session_id: str,
        user_message: str,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Process user message and generate orchestrator response.

        Supports multi-step directives (U1): "do A, then B, finally C"
        is split into sequential steps processed in order.

        Args:
            session_id: Session ID
            user_message: User input
            context: Optional context (e.g., {"platform": "vscode", "health_status": {...}})

        Returns:
            {
                "response": "AI response text",
                "decision_type": "QUERY|DELEGATE|HEAL|CONTINUE|CLARIFY|MULTI_STEP",
                "action_id": "optional task ID if action taken",
                "confidence": 0.0-1.0,
                "genesis_logged": bool,
                "timestamp": ISO datetime,
                "steps": [...] (only for multi-step)
            }
        """
        context = context or {}
        timestamp = datetime.now().isoformat()

        # U3: Cognitive dissonance safety check
        dissonance_alert = self._check_dissonance(user_message)
        if dissonance_alert:
            logger.warning("Cognitive dissonance alert for session %s — escalating to Sentinel", session_id)
            self.sm.save_chat_message(
                session_id=session_id, sender="orchestrator",
                message="[SECURITY] Cognitive dissonance detected. Escalating to Sentinel for review.",
                response_type="security_alert", genesis_logged=True,
            )

        # U1: Check for multi-step directive
        steps = self._split_multi_step(user_message)
        if len(steps) > 1:
            return self._process_multi_step(session_id, steps, context, timestamp)

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
        Analyze user message intent using LLM classification with keyword fallback.

        Tries LLM first (if self.llm is set), falls back to keyword scoring.

        Returns:
            (decision_type, confidence, extracted_data)
        """
        # Try LLM classification first
        if self.llm:
            try:
                result = self._llm_classify_intent(message)
                if result:
                    return result
            except Exception as exc:
                logger.warning("LLM intent classification failed: %s, using keywords", exc)

        # Keyword scoring fallback
        return self._keyword_classify_intent(message)

    def _llm_classify_intent(self, message: str) -> Optional[Tuple[str, float, Dict]]:
        """Use LLM to classify intent. Returns None if classification fails."""
        try:
            from arbitrage.llm import chat
        except ImportError:
            return None

        prompt = (
            f"Classify the user intent of this message into exactly one category.\n"
            f"Categories:\n"
            f"- QUERY: User is asking a question or requesting information\n"
            f"- DELEGATE: User wants a task executed or action performed\n"
            f"- HEAL: User reports a problem that needs fixing\n"
            f"- CONTINUE: User wants to resume previous work\n"
            f"- CLARIFY: Message is too vague to classify\n\n"
            f"Message: \"{message}\"\n\n"
            f"Reply with ONLY valid JSON: {{\"decision\": \"CATEGORY\", \"confidence\": 0.0-1.0}}"
        )
        raw = chat(prompt, system="You are an intent classifier for ADRION 369 autonomous agent system. Reply only with JSON.")
        data = json.loads(raw.strip().strip("`").strip())
        decision = data["decision"].upper()
        valid_decisions = (
            self.DECISION_QUERY, self.DECISION_DELEGATE, self.DECISION_HEAL,
            self.DECISION_CONTINUE, self.DECISION_CLARIFY,
        )
        if decision not in valid_decisions:
            return None
        confidence = max(0.0, min(1.0, float(data["confidence"])))
        extracted = {"task_description": message} if decision == self.DECISION_DELEGATE else {}
        return decision, confidence, extracted

    def _keyword_classify_intent(self, message: str) -> Tuple[str, float, Dict]:
        """Keyword scoring fallback for intent classification."""
        message_lower = message.lower()

        # Continue/Resume: explicit and unambiguous — check first
        if "continue" in message_lower or "resume" in message_lower:
            return self.DECISION_CONTINUE, 0.9, {}

        # Score each category by keyword overlap count
        scores = {
            self.DECISION_QUERY: sum(1 for k in self.QUERY_KEYWORDS if k in message_lower),
            self.DECISION_DELEGATE: sum(1 for k in self.DELEGATE_KEYWORDS if k in message_lower),
            self.DECISION_HEAL: sum(1 for k in self.HEAL_KEYWORDS if k in message_lower),
        }

        # Priority order for tie-breaking: QUERY > DELEGATE > HEAL
        priority = [self.DECISION_QUERY, self.DECISION_DELEGATE, self.DECISION_HEAL]

        best = max(priority, key=lambda d: scores[d])
        if scores[best] == 0:
            return self.DECISION_QUERY, 0.5, {}

        confidence = min(0.9, 0.6 + scores[best] * 0.1)
        data = {"task_description": message} if best == self.DECISION_DELEGATE else {}
        return best, confidence, data

    def _generate_response(self, decision_type: str, message: str, data: Dict) -> str:
        """Generate response using LLM with template fallback."""
        if self.llm:
            try:
                return self._llm_generate_response(decision_type, message, data)
            except Exception as exc:
                logger.warning("LLM response generation failed: %s, using template", exc)

        return self._template_response(decision_type, message)

    def _llm_generate_response(self, decision_type: str, message: str, data: Dict) -> str:
        """Generate natural-language response via LLM, with RAG context if available."""
        from arbitrage.llm import chat
        context_str = json.dumps(data, ensure_ascii=False) if data else "none"

        # U4: Inject RAG context from Genesis Record
        rag_context = self._get_rag_context(message)
        rag_section = ""
        if rag_context:
            rag_section = f"\nRelevant knowledge base context:\n{rag_context}\n"

        prompt = (
            f"You are the ADRION 369 Master Orchestrator. The user said:\n"
            f"\"{message}\"\n\n"
            f"Decision type: {decision_type}\n"
            f"Context data: {context_str}\n"
            f"{rag_section}\n"
            f"Generate a helpful, concise response (max 150 words) in the language "
            f"the user used. Be direct and actionable."
        )
        return chat(prompt, system="You are an AI system orchestrator assistant for ADRION 369.")

    def _get_rag_context(self, query: str) -> str:
        """U4: Retrieve relevant context from Genesis Record via RAG.

        Returns empty string if RAG is unavailable.
        """
        if self._rag is None:
            try:
                from scripts.orchestration.rag_context_optimizer import RAGContextOptimizer
                self._rag = RAGContextOptimizer()
                logger.info("RAG context optimizer initialized for chat responses")
            except (ImportError, SystemExit, Exception) as exc:
                logger.info("RAG context not available: %s", exc)
                self._rag = False  # Sentinel: don't retry
                return ""

        if self._rag is False:
            return ""

        try:
            return self._rag.get_relevant_context(query, top_k=3)
        except Exception as exc:
            logger.warning("RAG context retrieval failed: %s", exc)
            return ""

    def _template_response(self, decision_type: str, message: str) -> str:
        """Fallback template-based response when LLM is unavailable."""
        if decision_type == self.DECISION_QUERY:
            return f"I understand you're asking: '{message}'. I'm analyzing the system state to provide you with accurate information..."

        elif decision_type == self.DECISION_DELEGATE:
            return f"I'm delegating this task to the appropriate agent for execution: '{message[:50]}...'"

        elif decision_type == self.DECISION_HEAL:
            return "Detected system issues. Activating self-healing protocol with the Healer agent..."

        elif decision_type == self.DECISION_CONTINUE:
            return "Resuming tasks from your previous session..."

        elif decision_type == self.DECISION_CLARIFY:
            return "I need clarification. Could you provide more details?"

        else:
            return "I received your message but couldn't determine the intent. Please try again."

    # ── U1: Multi-step Directive Support ──────────────────────────────────────

    # Connectors that indicate multi-step sequences (PL + EN)
    _STEP_SEPARATORS = [
        ", then ", ", potem ", ", następnie ", ", na końcu ", ", finally ",
        "; then ", "; potem ", "; następnie ",
        ". then ", ". potem ", ". następnie ",
    ]

    def _split_multi_step(self, message: str) -> List[str]:
        """Split a user message into multiple directive steps.

        Recognizes connectors like "then", "potem", "następnie", "na końcu", "finally".
        If LLM is available, uses LLM to split ambiguous compound commands.
        Returns a list with 1 element if the message is a single directive.
        """
        msg_lower = message.lower()

        # Try keyword splitting first
        for sep in self._STEP_SEPARATORS:
            if sep in msg_lower:
                # Split on the separator (case-insensitive)
                idx = msg_lower.index(sep)
                parts = [message[:idx].strip()]
                remainder = message[idx + len(sep):].strip()
                # Recursively split remainder for chained separators
                parts.extend(self._split_multi_step(remainder))
                return [p for p in parts if p]

        # Try numbered list: "1. do X  2. do Y  3. do Z"
        import re
        numbered = re.split(r'\s*\d+\.\s+', message)
        numbered = [s.strip() for s in numbered if s.strip()]
        if len(numbered) > 1:
            return numbered

        # Try LLM splitting for complex phrases
        if self.llm and any(kw in msg_lower for kw in ["and", "i ", "oraz", "a potem", "after that"]):
            try:
                return self._llm_split_steps(message)
            except Exception:
                pass

        return [message]

    def _llm_split_steps(self, message: str) -> List[str]:
        """Use LLM to split a compound directive into sequential steps."""
        from arbitrage.llm import chat
        prompt = (
            f"Split this user directive into sequential steps. "
            f"If it's a single action, return it as-is.\n"
            f"Directive: \"{message}\"\n\n"
            f"Reply with ONLY a JSON array of step strings, e.g.: "
            f'["step 1", "step 2", "step 3"]'
        )
        raw = chat(prompt, system="You split compound user directives into sequential steps. Reply only with a JSON array.")
        steps = json.loads(raw.strip().strip("`").strip())
        if isinstance(steps, list) and len(steps) > 1:
            return [str(s) for s in steps]
        return [message]

    def _process_multi_step(
        self, session_id: str, steps: List[str], context: Dict, timestamp: str
    ) -> Dict[str, Any]:
        """Process a multi-step directive sequentially."""
        logger.info("Processing multi-step directive: %d steps", len(steps))
        step_results = []
        all_action_ids = []
        total_genesis = False

        for i, step_msg in enumerate(steps, 1):
            logger.info("Multi-step [%d/%d]: %s", i, len(steps), step_msg[:60])

            decision_type, confidence, extracted_data = self.analyze_intent(step_msg)
            response = self._generate_response(decision_type, step_msg, extracted_data)
            action_id = None

            if decision_type == self.DECISION_DELEGATE:
                action_id = self._execute_delegate(session_id, step_msg, extracted_data, context)
                total_genesis = True
            elif decision_type == self.DECISION_HEAL:
                action_id = self._execute_heal(session_id, context)
                total_genesis = True

            step_results.append({
                "step": i,
                "message": step_msg,
                "decision_type": decision_type,
                "confidence": confidence,
                "response": response,
                "action_id": action_id,
            })

            if action_id:
                all_action_ids.append(action_id)

        # Compose combined response
        combined = "\n".join(
            f"Step {r['step']}: [{r['decision_type']}] {r['response']}"
            for r in step_results
        )

        # Save to session
        self.sm.save_chat_message(
            session_id=session_id, sender="user",
            message=f"[MULTI-STEP: {len(steps)} steps] {steps[0][:80]}...",
            response_type="input", genesis_logged=False,
        )
        self.sm.save_chat_message(
            session_id=session_id, sender="orchestrator",
            message=combined, response_type="multi_step",
            genesis_logged=total_genesis,
        )

        return {
            "response": combined,
            "decision_type": "MULTI_STEP",
            "action_id": all_action_ids[0] if all_action_ids else None,
            "confidence": sum(r["confidence"] for r in step_results) / len(step_results),
            "genesis_logged": total_genesis,
            "timestamp": timestamp,
            "steps": step_results,
        }

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

    def _check_dissonance(self, text: str) -> Optional[Dict]:
        """U3: Check for cognitive dissonance (polite language + risky intent)."""
        try:
            from uap.backend.cognitive_dissonance import check_and_escalate
            return check_and_escalate(text)
        except ImportError:
            return None
