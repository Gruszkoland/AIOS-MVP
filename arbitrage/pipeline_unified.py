"""
ADRION 369 — Unified Demo Pipeline (Trinity → Hexagon → Guardian + RAG)

Complete demonstration integrating:
  - Trinity perspective scoring (Material, Intellectual, Essential)
  - Hexagon sequential pipeline (6 processing stages)
  - Guardian Laws validation (9 ethical rules)
  - RAG context enrichment (Guardian Laws knowledge base reasoning)
  - Event sourcing (immutable audit trail)
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("adrion.pipeline_unified")


def run_unified_demonstration(
    job: dict,
    use_rag: bool = True,
    use_event_log: bool = True,
) -> dict:
    """
    Complete unified pipeline demonstration.

    Args:
        job: Job data (id, title, description, type, analysis, resources)
        use_rag: Whether to use RAG enrichment (default: True)
        use_event_log: Whether to log to event stream (default: True)

    Returns:
        dict with trinity, hexagon, guardians results and final decision
    """
    from arbitrage.trinity import evaluate_trinity
    from arbitrage.guardian import evaluate_guardians, build_context
    from arbitrage.hexagon import HexagonProcessor

    # Prepare job data
    job_id = job.get("id", f"job-{int(datetime.now().timestamp())}")
    logger.info("Starting unified pipeline for job: %s", job_id)

    # Prepare analysis (default if not provided)
    analysis = job.get("analysis", {
        "score": 7,
        "fit": "Good",
        "risks": "None",
        "est_profit": 50,
        "reasoning": "Standard analysis from arbitrage system",
    })

    # Prepare system resources (if not provided, psutil will be used)
    system_resources = job.get("resources")

    # ─────────────────────────────────────────────────────────────────
    # STEP 1: Trinity Score (Material, Intellectual, Essential)
    # ─────────────────────────────────────────────────────────────────

    logger.info("STEP 1: Evaluating Trinity perspectives...")

    trinity_result = evaluate_trinity(job, analysis, system_resources=system_resources)

    trinity_scores = {
        "material": trinity_result.material,
        "intellectual": trinity_result.intellectual,
        "essential": trinity_result.essential,
        "overall": trinity_result.combined,
    }

    logger.info(
        "Trinity scores - Material: %.4f, Intellectual: %.4f, Essential: %.4f, Overall: %.4f",
        trinity_scores["material"],
        trinity_scores["intellectual"],
        trinity_scores["essential"],
        trinity_scores["overall"],
    )

    # ─────────────────────────────────────────────────────────────────
    # STEP 2: RAG Enhancement (Optional - Guard Laws context)
    # ─────────────────────────────────────────────────────────────────

    rag_context = {}
    if use_rag:
        try:
            logger.info("STEP 2A: Retrieving Guardian Laws context via RAG...")
            from arbitrage.rag_integration import get_rag_integration

            rag = get_rag_integration()

            # Query RAG for Guardian Laws relevant to this decision
            query = f"Ethical evaluation of {job.get('type', 'job')}: {job.get('title', 'untitled')}"
            context_docs = rag.retrieve_context(query, top_k=3)

            # Use Ollama to reason over retrieved context
            reasoning = rag.reason_with_context(query, context_docs)

            rag_context = {
                "retrieved_docs": len(context_docs),
                "reasoning": reasoning.get("reasoning", ""),
                "available": rag.ragflow_available and rag.ollama_available,
            }

            logger.info("RAG retrieved %d documents, reasoning available: %s",
                       len(context_docs), rag_context["available"])

            # Optionally enhance intellectual score with RAG
            if rag_context["available"] and context_docs:
                enhanced_scoring = rag.enhance_intellectual_scoring(job, analysis, trinity_scores["intellectual"])
                old_score = trinity_scores["intellectual"]
                trinity_scores["intellectual"] = enhanced_scoring["enhanced_score"]
                trinity_scores["overall"] = (
                    trinity_scores["material"] * 0.3 +
                    trinity_scores["intellectual"] * 0.5 +
                    trinity_scores["essential"] * 0.2
                )
                rag_context["boost"] = enhanced_scoring["rag_boost"]
                logger.info(
                    "RAG enhanced intellectual score: %.4f → %.4f (boost: %.4f)",
                    old_score,
                    trinity_scores["intellectual"],
                    enhanced_scoring["rag_boost"],
                )

        except Exception as exc:
            logger.warning("RAG enhancement failed (non-fatal): %s", exc)
            rag_context["error"] = str(exc)

    # ─────────────────────────────────────────────────────────────────
    # STEP 3: Hexagon Pipeline (6-stage sequential processing)
    # ─────────────────────────────────────────────────────────────────

    logger.info("STEP 2B: Running Hexagon 6-stage pipeline...")

    processor = HexagonProcessor()
    hexagon_result = processor.process(trinity_scores)

    hexagon_summary = {
        "stages": [s.to_dict() for s in hexagon_result.stages],
        "combined_score": hexagon_result.combined_score,
        "duration_ms": hexagon_result.total_duration_ms,
        "approved": hexagon_result.approved,
    }

    logger.info(
        "Hexagon pipeline completed: combined_score=%.4f, approved=%s, duration_ms=%.0f",
        hexagon_summary["combined_score"],
        hexagon_summary["approved"],
        hexagon_summary["duration_ms"],
    )

    # ─────────────────────────────────────────────────────────────────
    # STEP 4: Guardian Laws Validation (9 ethical rules)
    # ─────────────────────────────────────────────────────────────────

    logger.info("STEP 3: Validating Guardian Laws...")

    # Build context for Guardian evaluation (using default bid/cost parameters)
    guardian_context = build_context()

    guardian_result = evaluate_guardians(job, analysis, guardian_context)

    guardian_summary = {
        "laws_evaluated": len(guardian_result.laws),
        "laws_passed": sum(1 for l in guardian_result.laws if l.passed),
        "violations": guardian_result.violations,
        "approved": guardian_result.approved,
        "laws": [
            {
                "name": law.name,
                "passed": law.passed,
                "reason": law.reason,
                "weight": law.weight,
            }
            for law in guardian_result.laws
        ],
    }

    logger.info(
        "Guardian validation: %d/%d laws passed, violations=%d, approved=%s",
        guardian_summary["laws_passed"],
        guardian_summary["laws_evaluated"],
        guardian_summary["violations"],
        guardian_summary["approved"],
    )

    # ─────────────────────────────────────────────────────────────────
    # STEP 5: Final Decision Logic
    # ─────────────────────────────────────────────────────────────────

    logger.info("STEP 4: Determining final decision...")

    # Decision rules:
    # - If any stage fails (Trinity <0.4, Hexagon score <0.5, Guardians violations >1):
    #   DENIED
    # - Else if all pass with good scores:
    #   APPROVED
    # - Else:
    #   CONDITIONAL

    if not guardian_summary["approved"]:
        final_decision = "DENIED"
        decision_reason = f"Guardian validation failed: {guardian_summary['violations']} violations detected"
    elif trinity_scores["overall"] < 0.4:
        final_decision = "DENIED"
        decision_reason = f"Trinity overall score too low: {trinity_scores['overall']:.4f} < 0.4"
    elif hexagon_summary["combined_score"] < 0.5:
        final_decision = "DENIED"
        decision_reason = f"Hexagon pipeline score too low: {hexagon_summary['combined_score']:.4f} < 0.5"
    elif trinity_scores["overall"] >= 0.7 and guardian_summary["violations"] == 0:
        final_decision = "APPROVED"
        decision_reason = "All validations passed with strong scores"
    elif guardian_summary["violations"] == 0 and trinity_scores["overall"] >= 0.5:
        final_decision = "APPROVED"
        decision_reason = "All validations passed, above minimum thresholds"
    else:
        final_decision = "CONDITIONAL"
        decision_reason = "Passed validations but some scores are moderate"

    # ─────────────────────────────────────────────────────────────────
    # STEP 6: Build Response & Log Event
    # ─────────────────────────────────────────────────────────────────

    logger.info("STEP 5: Building response and logging...")

    response = {
        "job_id": job_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trinity": {
            "material": round(trinity_scores["material"], 4),
            "intellectual": round(trinity_scores["intellectual"], 4),
            "essential": round(trinity_scores["essential"], 4),
            "overall": round(trinity_scores["overall"], 4),
        },
        "hexagon": hexagon_summary,
        "guardians": guardian_summary,
        "rag_context": rag_context if use_rag else None,
        "decision": final_decision,
        "decision_reason": decision_reason,
        "approved": final_decision in ["APPROVED", "CONDITIONAL"],
    }

    # Optional: Log to event stream
    if use_event_log:
        try:
            _log_event(job_id, response)
        except Exception as exc:
            logger.warning("Event logging failed (non-fatal): %s", exc)

    logger.info(
        "Pipeline complete: job_id=%s, decision=%s, timestamp=%s",
        job_id,
        final_decision,
        response["timestamp"],
    )

    return response


def _log_event(job_id: str, result: dict) -> None:
    """Log decision event to event stream for audit trail."""
    try:
        from arbitrage.event_sourcing import log_decision

        log_decision(
            job_id=job_id,
            decision=result["decision"],
            trinity=result["trinity"],
            hexagon=result["hexagon"],
            guardians=result["guardians"],
            timestamp=result["timestamp"],
        )
    except ImportError:
        logger.debug("Event sourcing not available, skipping event log")
    except Exception as exc:
        logger.warning("Failed to log event: %s", exc)


# Convenience functions for testing

def demo_job_template() -> dict:
    """Return a sample job for testing the unified pipeline."""
    return {
        "id": f"demo-{int(datetime.now().timestamp())}",
        "type": "content_creation",
        "title": "ADRION 369 Demonstration Job",
        "description": "End-to-end demonstration of Trinity → Hexagon → Guardian → RAG pipeline",
        "analysis": {
            "score": 8,
            "fit": "Excellent",
            "risks": "Low",
            "est_profit": 150,
            "reasoning": "Strong alignment with platform ethics and profitability",
        },
    }


def run_demo_pipeline() -> dict:
    """Run demonstration with a sample job."""
    job = demo_job_template()
    return run_unified_demonstration(job, use_rag=True, use_event_log=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )
    result = run_demo_pipeline()
    print(json.dumps(result, indent=2))
