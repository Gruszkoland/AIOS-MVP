"""Tests for ChatOrchestrator: intent analysis, response generation, utilities."""

import json
import pytest
from unittest.mock import MagicMock, patch

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from uap.backend.chat_orchestrator import ChatOrchestrator


# ── Fixtures ────────────────────────────────────────────────────────────────


def _make_orchestrator(llm=None, orchestrator=None):
    sm = MagicMock()
    sm.get_chat_history.return_value = []
    sm.get_resumed_tasks.return_value = []
    db = MagicMock()
    return ChatOrchestrator(sm, db, llm_backend=llm, master_orchestrator=orchestrator)


# ── Bug 1.1: List import ────────────────────────────────────────────────────


def test_suggest_next_actions_returns_list():
    """Bug 1.1: suggest_next_actions must not raise NameError (List import)."""
    co = _make_orchestrator()
    result = co.suggest_next_actions("test-session")
    assert isinstance(result, list)
    assert all(isinstance(s, str) for s in result)


# ── Bug 1.3: Intent scoring priority ────────────────────────────────────────


class TestKeywordIntentClassification:
    """Verify scoring-based intent classification with correct priority."""

    def _classify(self, message):
        co = _make_orchestrator()
        return co._keyword_classify_intent(message)

    def test_query_wins_over_heal_for_questions(self):
        """'What is the error?' should be QUERY, not HEAL (error removed from HEAL)."""
        decision, _, _ = self._classify("What is the error?")
        assert decision == "QUERY"

    def test_how_question_is_query(self):
        decision, _, _ = self._classify("How do I fix this?")
        # 'how' = QUERY(1), 'fix' = HEAL(1) — QUERY wins tie-break
        assert decision == "QUERY"

    def test_pure_heal_command(self):
        decision, _, _ = self._classify("Fix the database immediately")
        assert decision == "HEAL"

    def test_pure_delegate_command(self):
        decision, confidence, data = self._classify("Run the deployment pipeline")
        assert decision == "DELEGATE"
        assert "task_description" in data

    def test_continue_message(self):
        decision, confidence, _ = self._classify("continue")
        assert decision == "CONTINUE"
        assert confidence == 0.9

    def test_resume_message(self):
        decision, _, _ = self._classify("resume previous work")
        assert decision == "CONTINUE"

    def test_no_keywords_defaults_to_query(self):
        decision, confidence, _ = self._classify("hello there")
        assert decision == "QUERY"
        assert confidence == 0.5

    def test_delegate_keywords_no_longer_include_do(self):
        """'do' was removed from DELEGATE_KEYWORDS (too broad)."""
        decision, _, _ = self._classify("What do you think about this?")
        assert decision == "QUERY"  # 'what' = QUERY, 'do' not in DELEGATE

    def test_multiple_heal_keywords_boost_confidence(self):
        decision, confidence, _ = self._classify("Fix and repair the crash")
        assert decision == "HEAL"
        assert confidence > 0.7  # 3 HEAL hits = 0.6 + 3*0.1 = 0.9

    def test_scoring_with_mixed_keywords(self):
        """When QUERY and DELEGATE tie, QUERY wins by priority."""
        decision, _, _ = self._classify("Help me start the task")
        # help = QUERY(1), start = DELEGATE(1), task = DELEGATE(2) → DELEGATE wins 2>1
        assert decision == "DELEGATE"


# ── Gap 2.2: LLM-backed intent classification ──────────────────────────────


class TestLLMIntentClassification:

    def test_llm_classify_intent_success(self):
        co = _make_orchestrator(llm=True)
        mock_response = json.dumps({"decision": "DELEGATE", "confidence": 0.92})
        with patch("uap.backend.chat_orchestrator.ChatOrchestrator._llm_classify_intent",
                   return_value=("DELEGATE", 0.92, {"task_description": "deploy app"})):
            decision, confidence, data = co.analyze_intent("deploy the application")
            assert decision == "DELEGATE"
            assert confidence == 0.92

    def test_llm_failure_falls_back_to_keywords(self):
        co = _make_orchestrator(llm=True)
        with patch.object(co, "_llm_classify_intent", side_effect=RuntimeError("LLM down")):
            decision, _, _ = co.analyze_intent("Fix the server")
            assert decision == "HEAL"  # keyword fallback

    def test_no_llm_uses_keywords_directly(self):
        co = _make_orchestrator(llm=None)
        decision, _, _ = co.analyze_intent("What is the status?")
        assert decision == "QUERY"


# ── Gap 2.3: LLM-backed response generation ────────────────────────────────


class TestResponseGeneration:

    def test_template_response_query(self):
        co = _make_orchestrator()
        resp = co._template_response("QUERY", "test message")
        assert "test message" in resp

    def test_template_response_delegate(self):
        co = _make_orchestrator()
        resp = co._template_response("DELEGATE", "deploy the app now")
        assert "delegating" in resp.lower()

    def test_template_response_heal(self):
        co = _make_orchestrator()
        resp = co._template_response("HEAL", "fix it")
        assert "healing" in resp.lower() or "self-healing" in resp.lower()

    def test_llm_response_with_fallback(self):
        co = _make_orchestrator(llm=True)
        with patch.object(co, "_llm_generate_response", side_effect=Exception("timeout")):
            resp = co._generate_response("QUERY", "hello", {})
            # Should fall back to template
            assert isinstance(resp, str)
            assert len(resp) > 0
