"""VerifyMode — Self-Correction Engine for ROPE 3.0 agents.

Provides Devil's Advocate sub-prompt generation and output safety verification
for all 9 ROPE agent personas (AIO-01 through RIA-09).

Public API:
    vm = VerifyMode()
    result = vm.verify_agent_output("AIO-01", my_output_dict)
    # -> {"is_safe": bool, "risk_level": str, "concerns": [...], "recommendations": [...]}

    prompt = vm.generate_devil_advocate_prompt("AIO-01", "implement rate limiter")
    # -> str  (devil's advocate prompt for the agent to fill in)

    laws = vm.check_against_guardian_laws(my_output_dict)
    # -> {"verdict": "ALLOW"|"DENY", "violations": [...], "laws_mapping": {...}, ...}

This module is importable without the mcp SDK — business logic only.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

_MCP_DIR = Path(__file__).parent
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from shared import (  # noqa: E402
    GUARDIAN_LAWS,
    GUARDIAN_LAWS_BY_ID,
    evaluate_guardian_laws,
    utc_now,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KNOWN_AGENT_IDS: frozenset[str] = frozenset(
    {"AIO-01", "PAA-02", "TDO-03", "AUA-04", "VTA-05", "GRA-06", "OCA-07", "KSA-08", "RIA-09"}
)

RISK_LEVELS: tuple[str, ...] = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

# Required fields every ROPE v3.0 output must contain
_REQUIRED_OUTPUT_FIELDS: tuple[str, ...] = (
    "agent",
    "trace_id",
    "confidence_level",
    "status",
    "guardian_result",
    "handoff",
)

# trace_id must match: UUID4.AGENT_CODE.UNIX_MS
_TRACE_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
    r"\.[A-Z]{2,3}-[0-9]{2}\.\d+$"
)

# PII detection patterns (applied to the serialized output string)
_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    "api_key_sk": re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    "github_pat": re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
    "hardcoded_password": re.compile(
        r'(?:password|passwd|secret)\s*[=:]\s*["\'][^"\']{6,}["\']',
        re.IGNORECASE,
    ),
}

# Scoring penalties (applied against a starting score of 100)
_PENALTIES: dict[str, int] = {
    "critical_guardian_violation": 60,
    "high_guardian_violation":     25,
    "medium_guardian_violation":   10,
    "pii_detected":                50,
    "low_confidence":              20,
    "missing_required_field":      15,
    "agent_anti_pattern":          20,
    "malformed_trace_id":           5,
}

# Per-agent keyword checks: (check_name, trigger_keyword, description)
# A concern is raised when the keyword IS found in the serialized output string.
_AGENT_KEYWORD_CHECKS: dict[str, list[tuple[str, str, str]]] = {
    "AIO-01": [
        ("sql_fstring_select", 'f"SELECT',   "f-string SQL SELECT injection risk in output"),
        ("sql_fstring_update", 'f"UPDATE',   "f-string SQL UPDATE injection risk in output"),
        ("sql_fstring_delete", 'f"DELETE',   "f-string SQL DELETE injection risk in output"),
        ("hardcoded_api_key",  '"sk-',       "Potential hardcoded API key found in output"),
        ("drop_table",         "DROP TABLE", "Destructive SQL keyword without backup reference"),
    ],
    "PAA-02": [
        ("change_me_placeholder", "CHANGE_ME", "Unresolved placeholder in architecture decision"),
        ("todo_design",           "TODO: design", "Incomplete design note in output"),
    ],
    "TDO-03": [
        ("zero_version",    "==0.",           "Unstable 0.x package version pinned"),
        ("unpinned_dep",    ">=",             "Potentially unpinned dependency range in output"),
    ],
    "AUA-04": [
        ("guardian_bypass", "skip_guardian", "Explicit Guardian Law bypass keyword detected"),
        ("force_execute",   "force_execute", "Force-execute flag — bypasses safety checks"),
    ],
    "VTA-05": [
        ("mock_only",  "MagicMock",     "Heavy mock usage may indicate coverage inflation"),
        ("todo_test",  "# TODO: add",  "Incomplete test stub in output (TODO marker)"),
    ],
    "GRA-06": [
        ("audit_bypass",  "SKIP_AUDIT", "Audit trail skip keyword detected"),
        ("owasp_bypass",  "bypass",     "Generic bypass keyword in security clearance output"),
    ],
    "OCA-07": [
        ("force_route",      "FORCE",      "Unilateral force-routing keyword detected"),
        ("stale_hop_marker", "hop_count",  "High hop_count reference — check for routing loop"),
    ],
    "KSA-08": [
        ("wrong_law_truth",    '"Truth"',    "Wrong Guardian Law name: 'Truth' (canonical: 'Harmony')"),
        ("wrong_law_autonomy", '"Autonomy"', "Wrong Guardian Law name: 'Autonomy' (canonical: 'Authenticity')"),
        ("wrong_law_justice",  '"Justice"',  "Wrong Guardian Law name: 'Justice' (canonical: 'Privacy')"),
    ],
    "RIA-09": [
        ("force_release",    "FORCE_RELEASE", "Force-release flag — skips mandatory gates"),
        ("without_backup",   "without_backup", "Release-without-backup pattern detected"),
    ],
}

# ---------------------------------------------------------------------------
# Devil's Advocate: agent-specific challenges
# ---------------------------------------------------------------------------

_AGENT_SPECIFIC_CHALLENGES: dict[str, str] = {
    "AIO-01": (
        "CHALLENGE IMPLEMENTACJI:\n"
        "  - Czy kod zawiera f-string SQL? (grep: f\".*SELECT|UPDATE|DELETE)\n"
        "  - Czy wszystkie nowe funkcje maja type hints i docstrings?\n"
        "  - Czy nie wprowadzasz circular importu (Services -> Blueprints = FORBIDDEN)?\n"
        "  - Czy PAA-02 approval jest w context.paa02_decision = 'APPROVE'?"
    ),
    "PAA-02": (
        "CHALLENGE ARCHITEKTURY:\n"
        "  - Czy decyzja architektoniczna ma ADR (Architecture Decision Record)?\n"
        "  - Czy nie wychodzisz poza scope_files bez zatwierdzenia PAA-02?\n"
        "  - Czy oceniles ryzyko: co sie stanie, gdy to rozwiazanie zawiedzie?\n"
        "  - Czy rozwazyles alternatywne wzorce przed zatwierdzeniem?"
    ),
    "TDO-03": (
        "CHALLENGE ZALEZNOSCI:\n"
        "  - Czy zadna nowa zaleznosc nie ma known CVE? (safety check)\n"
        "  - Czy licencja nowego pakietu jest zgodna z projektem (MIT/Apache)?\n"
        "  - Czy requirements*.txt nie zawiera unpinned wersji w prod?\n"
        "  - Czy bandit przeszedl bez HIGH findings po dodaniu paczki?"
    ),
    "AUA-04": (
        "CHALLENGE AUTOMATYZACJI:\n"
        "  - Czy nowa automatyzacja jest idempotentna (uruchomienie 2x = ten sam wynik)?\n"
        "  - Czy skrypt ma tryb --dry-run dla operacji na danych?\n"
        "  - Czy nie obchodzisz Guardian Law evaluation w zadnym miejscu skryptu?\n"
        "  - Czy automation mozna zatrzymac bez side effects (Ctrl+C safe)?"
    ),
    "VTA-05": (
        "CHALLENGE TESTOWANIA:\n"
        "  - Czy coverage nie jest 'inflated' przez mock-only testy bez real assertions?\n"
        "  - Czy testujesz edge cases, nie tylko happy path?\n"
        "  - Czy twoj PASS verdict jest uzasadniony — czy wszystkie AC sprawdzone?\n"
        "  - Czy testy przejda na czystym srodowisku (bez lokalnych artefaktow)?"
    ),
    "GRA-06": (
        "CHALLENGE BEZPIECZENSTWA:\n"
        "  - Czy sprawdziles OWASP Top 10 dla tej konkretnej operacji?\n"
        "  - Czy CRITICAL Guardian violation jest zapisana w audit trail?\n"
        "  - Czy Twoja clearance nie jest zbyt permissive dla danego ryzyka?\n"
        "  - Czy veto power (G7/G8) jest wlasciwie zastosowane w tym przypadku?"
    ),
    "OCA-07": (
        "CHALLENGE ORCHESTRACJI:\n"
        "  - Czy nie tworzysz infinite routing loop (A->B->A->B->...)?\n"
        "  - Czy hop_count < 10? Sprawdz teraz zanim wyemitujesz.\n"
        "  - Czy nie podejmujesz unilateralnej decyzji zamiast ja facilitowac?\n"
        "  - Czy clarification_round <= 3? (po 3 rundach eskaluj do OCA-07)"
    ),
    "KSA-08": (
        "CHALLENGE DOKUMENTACJI:\n"
        "  - Czy OpenAPI spec jest zsynchronizowany z aktualnymi endpointami kodu?\n"
        "  - Czy nazwy Guardian Laws zgadzaja sie z docs/GUARDIAN_LAWS_CANONICAL.json?\n"
        "  - Czy CHANGELOG ma date i numer wersji dla kazdego wpisu?\n"
        "  - Czy docstringi nowych funkcji sa kompletne (Args, Returns, Raises)?"
    ),
    "RIA-09": (
        "CHALLENGE RELEASU:\n"
        "  - Czy VTA-05 zwrocil verdict = PASS? Sprawdz vta05_verdict w context.\n"
        "  - Czy backup istnieje i jest zweryfikowany przed deployem do produkcji?\n"
        "  - Czy version bump jest zsynchronizowany z git tag (semver)?\n"
        "  - Czy post-release monitoring jest aktywny (Prometheus, Grafana alerts)?"
    ),
    "DEFAULT": (
        "CHALLENGE OGOLNA:\n"
        "  - Czy output jest kompletny i zawiera wszystkie 6 wymaganych pol?\n"
        "  - Czy Guardian Laws zostaly sprawdzone przed emisja?\n"
        "  - Czy confidence_level odzwierciedla rzeczywista pewnosc wyniku?"
    ),
}

_DEVIL_ADVOCATE_TEMPLATE = """\
VERIFY_MODE — ADWOKAT DIABLA AKTYWNY
=====================================
Agent:  {agent_id}
Task:   {task}

PRZED emisja output odpowiedz na 3 obowiazkowe pytania:

1. KWESTIONUJ ZALOZENIA
   "Co musialoby byc falszywe w moich zalozeniach, zeby ten output byl bledny?"

2. KWESTIONUJ KOMPLETNOSC
   "Jaki scenariusz testowy moglby obalic moja odpowiedz w ciagu 60 sekund?"

3. KWESTIONUJ BEZPIECZENSTWO
   "Czy ktos z zewnatrz moglby uzyc tego output w sposob szkodliwy?"

{agent_specific_challenge}

5 SCENARIUSZY EDGE-CASE — sprawdz kazdy przed emisja:
  E1: Czy Guardian Laws zwroca DENY po finalizacji? -> wywolaj verify_output
  E2: Czy confidence_baseline z poprzedniego agenta jest w zakresie [0, 100]?
  E3: Czy output nie zawiera PII (email, API key, haslo, PESEL)?
  E4: Czy obsluguje JSONDecodeError jesli LLM zwroci malformed JSON?
  E5: Czy retry_count < 3? (jesli >= 3 -> NIE wykonuj, eskaluj do OCA-07)

FORMAT ODPOWIEDZI (wypelnij przed wywolaniem verify_output):
  CLAIM:     [jedno zdanie opisujace output]
  CHALLENGE: [najsilniejszy kontrargument]
  EVIDENCE:  [konkretny dowod potwierdzajacy lub obalajacy]
  VERDICT:   safe | uncertain | unsafe

REGULY:
  VERDICT = unsafe     -> status = blocked; route to GRA-06
  VERDICT = uncertain  -> confidence_level -= 15; dodaj notes
  VERDICT = safe       -> wywolaj oracle/verify_output i dzialaj wg wyniku
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _score_to_risk(score: int) -> tuple[str, bool]:
    """Map a numeric safety score [0-100] to (risk_level, is_safe)."""
    if score >= 80:
        return "LOW", True
    if score >= 60:
        return "MEDIUM", True
    if score >= 40:
        return "HIGH", False
    return "CRITICAL", False


def _infer_operation(output: dict[str, Any]) -> str:
    """Infer the Guardian-Laws operation type from an agent output dict."""
    agent = str(output.get("agent", ""))
    status = str(output.get("status", ""))
    handoff_scenario = str(output.get("handoff", {}).get("scenario", ""))

    if "RIA-09" in agent and status == "completed":
        return "deploy"
    if "GRA-06" in agent:
        # GRA-06 may reference exports or deletes in its clearance
        summary = str(output.get("genesis_log", {}).get("summary", "")).lower()
        if "export" in summary:
            return "export"
        if "delete" in summary or "destroy" in summary:
            return "delete"
    if handoff_scenario == "escalation":
        return "deploy"
    return "query"


# ---------------------------------------------------------------------------
# VerifyMode
# ---------------------------------------------------------------------------

class VerifyMode:
    """Self-Correction Engine for ROPE 3.0 agent output verification.

    Usage:
        vm = VerifyMode()
        result = vm.verify_agent_output("AIO-01", output_dict)
        prompt  = vm.generate_devil_advocate_prompt("AIO-01", "implement X")
        laws    = vm.check_against_guardian_laws(output_dict)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify_agent_output(
        self,
        agent_id: str,
        output: dict[str, Any],
    ) -> dict[str, Any]:
        """Verify agent output safety and return a risk assessment.

        Args:
            agent_id: ROPE agent code, e.g. "AIO-01".
            output:   The agent's JSON output dict (pre-emission).

        Returns:
            dict with keys:
                is_safe (bool), risk_level (str), score (int),
                concerns (list[str]), recommendations (list[str]),
                agent_id (str), timestamp (str).
        """
        score: int = 100
        concerns: list[str] = []
        recommendations: list[str] = []

        # Serialize output for pattern matching
        output_str: str = json.dumps(output, default=str)

        # --- 1. PII scan ---------------------------------------------------
        for pattern_name, pattern in _PII_PATTERNS.items():
            if pattern.search(output_str):
                score -= _PENALTIES["pii_detected"]
                concerns.append(
                    f"PII pattern '{pattern_name}' detected in output "
                    f"— G7 Privacy (CRITICAL) violation"
                )
                recommendations.append(
                    f"Remove '{pattern_name}' PII from output; use anonymized identifiers"
                )

        # --- 2. Required fields check --------------------------------------
        for field in _REQUIRED_OUTPUT_FIELDS:
            if field not in output:
                score -= _PENALTIES["missing_required_field"]
                concerns.append(f"Missing required output field: '{field}'")
                recommendations.append(
                    f"Add '{field}' to output JSON (ROPE v3.0 mandatory)"
                )

        # --- 3. Confidence level ------------------------------------------
        confidence = output.get("confidence_level")
        if isinstance(confidence, (int, float)) and confidence < 30:
            score -= _PENALTIES["low_confidence"]
            concerns.append(
                f"Low confidence_level ({confidence}) — output may be unreliable downstream"
            )
            recommendations.append(
                "Raise confidence or emit status=partial with detailed notes"
            )

        # --- 4. Guardian result from agent's own pre-check ----------------
        guardian_result = output.get("guardian_result", {})
        if isinstance(guardian_result, dict) and not guardian_result.get("passed", True):
            violations = guardian_result.get("violations", [])
            for v in violations:
                law = GUARDIAN_LAWS_BY_ID.get(str(v).upper(), {})
                severity = law.get("severity", "MEDIUM")
                name = law.get("name", "Unknown")
                if severity == "CRITICAL":
                    score -= _PENALTIES["critical_guardian_violation"]
                    concerns.append(
                        f"CRITICAL Guardian Law violation: {v} ({name}) — instant DENY"
                    )
                    recommendations.append(
                        f"G{v[-1]} CRITICAL violation must be resolved before emission; route to GRA-06"
                    )
                elif severity == "HIGH":
                    score -= _PENALTIES["high_guardian_violation"]
                    concerns.append(f"HIGH Guardian Law violation: {v} ({name})")
                    recommendations.append(f"Resolve {v} ({name}) violation before emitting")
                else:
                    score -= _PENALTIES["medium_guardian_violation"]
                    concerns.append(f"MEDIUM Guardian Law violation: {v} ({name})")
                    recommendations.append(f"Address {v} ({name}) and document mitigation in notes")

        # --- 5. Agent-specific keyword anti-pattern checks -----------------
        checks = _AGENT_KEYWORD_CHECKS.get(agent_id, [])
        if not checks and agent_id not in KNOWN_AGENT_IDS:
            # Unknown agent — apply a subset of AIO-01 checks as default
            checks = _AGENT_KEYWORD_CHECKS.get("AIO-01", [])
        for check_name, keyword, description in checks:
            if keyword and keyword in output_str:
                score -= _PENALTIES["agent_anti_pattern"]
                concerns.append(f"Anti-pattern [{check_name}]: {description}")
                recommendations.append(
                    f"Investigate '{keyword}' reference and remove or justify it in notes"
                )

        # --- 6. trace_id format -------------------------------------------
        trace_id = str(output.get("trace_id", ""))
        if trace_id and not _TRACE_ID_RE.match(trace_id):
            score -= _PENALTIES["malformed_trace_id"]
            concerns.append(
                f"Malformed trace_id '{trace_id}' "
                f"— expected UUID4.AGENT_CODE.UNIX_MS"
            )
            recommendations.append(
                "Fix trace_id to match format: {UUID4}.{AGENT_CODE}.{UNIX_TIMESTAMP_MS}"
            )

        # --- Final scoring -------------------------------------------------
        score = max(0, min(100, score))
        risk_level, is_safe = _score_to_risk(score)

        return {
            "status": "ok",
            "agent_id": agent_id,
            "is_safe": is_safe,
            "risk_level": risk_level,
            "score": score,
            "concerns": concerns,
            "recommendations": recommendations,
            "timestamp": utc_now(),
        }

    def generate_devil_advocate_prompt(
        self,
        agent_id: str,
        task: str,
    ) -> str:
        """Generate a Devil's Advocate self-correction prompt for an agent.

        Args:
            agent_id: ROPE agent code, e.g. "AIO-01".
            task:     Short task description (one sentence).

        Returns:
            Formatted prompt string the agent must fill in before emitting output.
        """
        specific = _AGENT_SPECIFIC_CHALLENGES.get(
            agent_id,
            _AGENT_SPECIFIC_CHALLENGES["DEFAULT"],
        )
        return _DEVIL_ADVOCATE_TEMPLATE.format(
            agent_id=agent_id,
            task=task,
            agent_specific_challenge=specific,
        )

    def check_against_guardian_laws(
        self,
        output: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate an agent's output against all 9 Guardian Laws.

        Infers the operation type and context from the output dict, then
        runs the canonical evaluate_guardian_laws() function and returns
        a per-law mapping with violation status.

        Args:
            output: The agent's JSON output dict.

        Returns:
            dict with keys:
                verdict ("ALLOW"|"DENY"), violations (list[str]),
                weighted_score (int), laws_mapping (dict per law),
                is_compliant (bool), operation (str), timestamp (str).
        """
        operation = _infer_operation(output)

        # Build context from output fields
        _notes = str(output.get("notes") or "")
        _task_id = str(output.get("task_id") or "")
        context: dict[str, Any] = {
            "reason": _notes or _task_id,  # empty string if both absent — triggers G4
            "audit_logged": output.get("genesis_log", {}).get("write_required", False),
            "backup_exists": output.get("agent_output", {}).get("backup_verified", False),
            "scope": "local",
            "resource_cost": 0,
        }

        is_compliant, violations, weighted_score = evaluate_guardian_laws(
            operation, context
        )

        # Build per-law mapping for all 9 laws
        laws_mapping: dict[str, dict[str, Any]] = {
            law["id"]: {
                "name":        law["name"],
                "severity":    law["severity"],
                "veto":        law["veto"] == "true",
                "violated":    law["id"] in violations,
                "description": law["description"],
            }
            for law in GUARDIAN_LAWS
        }

        return {
            "status":         "ok",
            "operation":      operation,
            "is_compliant":   is_compliant,
            "verdict":        "ALLOW" if is_compliant else "DENY",
            "violations":     violations,
            "weighted_score": weighted_score,
            "laws_mapping":   laws_mapping,
            "timestamp":      utc_now(),
        }
