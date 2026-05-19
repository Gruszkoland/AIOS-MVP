"""Tests for keyword_persona_match routing with scoring approach."""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from uap.backend.blueprints import keyword_persona_match


# ── Bug 1.4: Scoring-based persona routing ──────────────────────────────────


@pytest.mark.parametrize("description,expected_agent", [
    # Pure single-agent keywords
    ("scout for new freelance opportunities", "SAP"),
    ("find a new project on Upwork", "SAP"),
    ("analyze the job requirements carefully", "Auditor"),
    ("design a new microservice architecture", "Architect"),
    ("fix the broken database connection", "Healer"),
    ("there is a crisis in production", "Sentinel"),
    ("archive the old session logs", "Librarian"),

    # NEW: previously unreachable agents
    ("amplify the outreach campaign", "Amplifier"),
    ("schedule a recurring health check", "Chronos"),
    ("leverage and accelerate the pipeline", "BoosterLever"),

    # Mixed keywords — scoring decides winner
    ("find and fix the error", "Sentinel"),  # error=Sentinel wins priority tie
    ("search and evaluate results", "Auditor"),  # evaluate(Auditor)=1, search(SAP)=1, Auditor wins tie
    ("design and plan the architecture", "Architect"),  # 3 Architect keywords

    # No keywords — default fallback
    ("random gibberish", "SAP"),
    ("hello world", "SAP"),
])
def test_keyword_persona_match(description, expected_agent):
    result = keyword_persona_match(description)
    assert result == expected_agent, f"'{description}' routed to {result}, expected {expected_agent}"


def test_all_agents_reachable():
    """Every agent must be reachable via at least one keyword."""
    all_agents = {
        "SAP", "Auditor", "Sentinel", "Architect", "Healer",
        "Librarian", "Amplifier", "BoosterLever", "Chronos",
    }
    reachable = set()
    test_phrases = [
        "scout", "analyze", "crisis", "design", "heal",
        "history", "amplify", "leverage", "schedule",
    ]
    for phrase in test_phrases:
        agent = keyword_persona_match(phrase)
        reachable.add(agent)

    assert reachable == all_agents, f"Unreachable agents: {all_agents - reachable}"
