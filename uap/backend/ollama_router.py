"""
Unified Admin Panel (UAP) — Ollama NL Routing
Uses local LLM to determine best agent for task

Replaces keyword-based routing with LLM-powered decision
"""
import os
import sys
import json
import requests
from typing import Optional, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db import get_db

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-coder:6.7b")

AGENTS = [
    "Librarian",
    "SAP",
    "Auditor",
    "Sentinel",
    "Architect",
    "Healer",
    "Amplifier",
    "BoosterLever",
    "Chronos",
]

AGENT_DESCRIPTIONS = {
    "Librarian": "Historical continuity, knowledge archiving, git analysis, dependency tracking",
    "SAP": "Strategic Action Planning, critical path planning, resource allocation",
    "Auditor": "Quality assurance, testing, non-regression, compliance checks",
    "Sentinel": "Error detection, crisis response, rapid threat monitoring",
    "Architect": "Design authority, unified patterns, system architecture",
    "Healer": "Continuous improvement, technical debt reduction, optimization",
    "Amplifier": "Public narrative, engagement, content marketing",
    "BoosterLever": "AI content generation, lead interaction, sales enablement",
    "Chronos": "Temporal master, scheduling, cycle orchestration",
}


class OllamaRouter:
    """LLM-powered task routing using Ollama."""

    def __init__(self):
        self.db = get_db()
        self.model = OLLAMA_MODEL
        self._test_connection()

    def _test_connection(self):
        """Test Ollama connection."""
        try:
            resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            if resp.status_code == 200:
                print(f"✅ Ollama connected: {OLLAMA_URL}")
        except Exception as e:
            print(f"⚠️ Ollama unavailable: {e}. Falling back to keyword routing.")

    def _query_ollama(self, prompt: str) -> str:
        """Query Ollama LLM."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,  # Lower = more deterministic
            }

            resp = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
                timeout=10
            )

            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
            else:
                return None
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return None

    def route_task(self, task_description: str, agent_hint: Optional[str] = None) -> Tuple[str, float]:
        """
        Route task to best agent using LLM.

        Returns: (agent_name, confidence_score)
        """
        # If agent_hint provided, use it with high confidence
        if agent_hint and agent_hint in AGENTS:
            return agent_hint, 0.95

        # Prepare agent descriptions for context
        agent_context = "\n".join([
            f"- {agent}: {desc}"
            for agent, desc in AGENT_DESCRIPTIONS.items()
        ])

        prompt = f"""Given these ADRION 369 multi-agent personas:
{agent_context}

Which agent is BEST suited for this task? Only respond with the agent name:

TASK: {task_description}

AGENT: """

        response = self._query_ollama(prompt)

        if response:
            # Clean response - extract agent name
            response = response.strip().split('\n')[0].strip()

            for agent in AGENTS:
                if agent.lower() in response.lower():
                    # Query confidence score
                    confidence = self._get_confidence(task_description, agent)
                    return agent, confidence

        # Fallback to keyword routing if LLM fails
        return self._fallback_keyword_routing(task_description), 0.6

    def _get_confidence(self, task_description: str, agent: str) -> float:
        """Estimate LLM confidence for routing decision."""
        prompt = f"""Rate how suitable is the {agent} agent for this task (0.0-1.0):

Task: {task_description}

Agent: {agent} - {AGENT_DESCRIPTIONS.get(agent, '')}

Confidence (0.0-1.0): """

        response = self._query_ollama(prompt)

        if response:
            try:
                # Extract numeric value
                parts = response.strip().split()
                for part in parts:
                    try:
                        score = float(part)
                        return max(0.0, min(1.0, score))
                    except ValueError:
                        continue
            except Exception:
                pass

        return 0.75  # Default confidence

    def _fallback_keyword_routing(self, task_description: str) -> str:
        """Keyword-based routing (Phase 1 fallback)."""
        keywords = task_description.lower()

        if "scout" in keywords or "find" in keywords or "search" in keywords:
            return "SAP"
        elif "analyze" in keywords or "evaluate" in keywords or "test" in keywords:
            return "Auditor"
        elif "crisis" in keywords or "urgent" in keywords or "error" in keywords:
            return "Sentinel"
        elif "design" in keywords or "architecture" in keywords or "pattern" in keywords:
            return "Architect"
        elif "heal" in keywords or "fix" in keywords or "optimize" in keywords:
            return "Healer"
        elif "history" in keywords or "document" in keywords or "archive" in keywords:
            return "Librarian"
        elif "content" in keywords or "marketing" in keywords or "narrative" in keywords:
            return "Amplifier"
        elif "schedule" in keywords or "timing" in keywords or "cycle" in keywords:
            return "Chronos"
        else:
            return "SAP"  # Default

    def explain_routing(self, task_description: str, agent: str) -> str:
        """Get LLM explanation for routing decision."""
        prompt = f"""Why is {agent} the best agent for this task?

Task: {task_description}
Agent profile: {AGENT_DESCRIPTIONS.get(agent, '')}

Explanation (1-2 sentences):"""

        response = self._query_ollama(prompt)
        return response if response else f"{agent} is suited for this task."


# Singleton instance
_router = None

def get_router() -> OllamaRouter:
    global _router
    if _router is None:
        _router = OllamaRouter()
    return _router
