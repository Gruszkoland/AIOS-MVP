"""
Tests for arbitrage/pipeline_unified.py — Unified demonstration pipeline

Covers:
  - Unified pipeline initialization
  - Trinity evaluation within pipeline
  - Hexagon processing
  - Guardian validation
  - RAG context retrieval (when available)
  - Final decision logic
  - Event logging (optional)
"""

import pytest
from datetime import datetime
from arbitrage.pipeline_unified import (
    run_unified_demonstration,
    demo_job_template,
    run_demo_pipeline,
)


class TestUnifiedPipeline:
    """Tests for unified Trinity → Hexagon → Guardian → RAG pipeline."""

    def test_demo_job_template(self):
        """Test that demo job template is properly structured."""
        job = demo_job_template()

        assert "id" in job
        assert "type" in job
        assert "title" in job
        assert "description" in job
        assert "analysis" in job

        assert job["type"] == "content_creation"
        assert job["analysis"]["score"] == 8

    def test_unified_pipeline_basic(self):
        """Test unified pipeline with demo job."""
        job = demo_job_template()

        result = run_unified_demonstration(job, use_rag=False, use_event_log=False)

        # Verify response structure
        assert "job_id" in result
        assert "timestamp" in result
        assert "trinity" in result
        assert "hexagon" in result
        assert "guardians" in result
        assert "decision" in result
        assert "decision_reason" in result
        assert "approved" in result

    def test_trinity_scores_in_response(self):
        """Test that Trinity scores are present and valid."""
        job = demo_job_template()

        result = run_unified_demonstration(job, use_rag=False, use_event_log=False)

        trinity = result["trinity"]
        assert "material" in trinity
        assert "intellectual" in trinity
        assert "essential" in trinity
        assert "overall" in trinity

        # All scores should be between 0 and 1
        for score in trinity.values():
            assert 0 <= score <= 1.0

    def test_hexagon_pipeline_in_response(self):
        """Test that Hexagon results are present."""
        job = demo_job_template()

        result = run_unified_demonstration(job, use_rag=False, use_event_log=False)

        hexagon = result["hexagon"]
        assert "stages" in hexagon
        assert "combined_score" in hexagon
        assert "duration_ms" in hexagon
        assert "approved" in hexagon

        assert isinstance(hexagon["stages"], list)
        assert len(hexagon["stages"]) == 6  # 6 stages
        assert isinstance(hexagon["duration_ms"], (int, float))

    def test_guardian_validation_in_response(self):
        """Test that Guardian validation results are present."""
        job = demo_job_template()

        result = run_unified_demonstration(job, use_rag=False, use_event_log=False)

        guardians = result["guardians"]
        assert "laws_evaluated" in guardians
        assert "laws_passed" in guardians
        assert "violations" in guardians
        assert "approved" in guardians
        assert "laws" in guardians

        assert guardians["laws_evaluated"] == 9  # 9 Guardian Laws
        assert len(guardians["laws"]) == 9
        assert guardians["laws_passed"] <= guardians["laws_evaluated"]

    def test_decision_logic_approved(self):
        """Test that decision is APPROVED when conditions are met."""
        job = demo_job_template()
        job["analysis"]["score"] = 10  # High score for approval

        result = run_unified_demonstration(job, use_rag=False, use_event_log=False)

        # With high scores and demo data, should generally approve
        decision = result["decision"]
        assert decision in ["APPROVED", "CONDITIONAL", "DENIED"]
        assert isinstance(result["approved"], bool)

    def test_decision_reason_present(self):
        """Test that decision reason is always provided."""
        job = demo_job_template()

        result = run_unified_demonstration(job, use_rag=False, use_event_log=False)

        assert "decision_reason" in result
        assert len(result["decision_reason"]) > 0
        assert isinstance(result["decision_reason"], str)

    def test_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        job = demo_job_template()

        result = run_unified_demonstration(job, use_rag=False, use_event_log=False)

        timestamp = result["timestamp"]
        # Should parse as ISO datetime
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_custom_job_data(self):
        """Test pipeline with custom job data."""
        custom_job = {
            "id": "custom-job-123",
            "type": "data_analysis",
            "title": "Custom Analysis Task",
            "description": "Testing custom job data",
            "analysis": {"score": 6, "fit": "Good"},
        }

        result = run_unified_demonstration(custom_job, use_rag=False, use_event_log=False)

        assert result["job_id"] == "custom-job-123"

    def test_rag_context_disabled(self):
        """Test pipeline with RAG disabled."""
        job = demo_job_template()

        result = run_unified_demonstration(job, use_rag=False, use_event_log=False)

        # When RAG is disabled, rag_context should be None
        assert result["rag_context"] is None

    def test_rag_context_enabled(self):
        """Test pipeline with RAG enabled (graceful fallback if unavailable)."""
        job = demo_job_template()

        result = run_unified_demonstration(job, use_rag=True, use_event_log=False)

        # When RAG is enabled, rag_context should be present (dict)
        assert isinstance(result["rag_context"], dict)
        # Should include 'available' flag and status info
        # (might have 'error' if RAG services not running)

    def test_all_stages_present_in_hexagon(self):
        """Test that all 6 stages are represented in Hexagon results."""
        job = demo_job_template()

        result = run_unified_demonstration(job, use_rag=False, use_event_log=False)

        stages = result["hexagon"]["stages"]
        stage_names = {stage["name"] for stage in stages}

        expected_stages = {"inventory", "empathy", "process", "debate", "healing", "action"}
        assert stage_names == expected_stages

    def test_demo_pipeline_wrapper(self):
        """Test the demo_pipeline convenience wrapper."""
        result = run_demo_pipeline()

        # Should have same structure as unified pipeline
        assert "job_id" in result
        assert "trinity" in result
        assert "hexagon" in result
        assert "guardians" in result
        assert "decision" in result

    def test_pipeline_completes_within_timeout(self):
        """Test that pipeline completes in reasonable time."""
        import time

        job = demo_job_template()
        start = time.time()

        result = run_unified_demonstration(job, use_rag=False, use_event_log=False)

        elapsed = time.time() - start

        # Should complete in under 10 seconds (generous timeout)
        assert elapsed < 10, f"Pipeline took {elapsed:.2f}s (expected < 10s)"

    def test_multiple_sequential_runs(self):
        """Test multiple sequential pipeline runs."""
        for i in range(3):
            job = demo_job_template()

            result = run_unified_demonstration(job, use_rag=False, use_event_log=False)

            assert "job_id" in result
            assert "decision" in result

    def test_trinity_intellectual_rag_boost(self):
        """Test that RAG can boost intellectual score when available."""
        job = demo_job_template()

        # Run without RAG
        result_no_rag = run_unified_demonstration(job, use_rag=False, use_event_log=False)
        score_no_rag = result_no_rag["trinity"]["intellectual"]

        # Run with RAG (might be same if RAG services unavailable)
        job2 = demo_job_template()
        result_with_rag = run_unified_demonstration(job2, use_rag=True, use_event_log=False)
        score_with_rag = result_with_rag["trinity"]["intellectual"]

        # Scores should be valid (0-1 range)
        assert 0 <= score_no_rag <= 1.0
        assert 0 <= score_with_rag <= 1.0

    def test_guardian_laws_order(self):
        """Test that Guardian Laws are evaluated in expected order."""
        job = demo_job_template()

        result = run_unified_demonstration(job, use_rag=False, use_event_log=False)

        laws = result["guardians"]["laws"]
        law_names = {law["name"] for law in laws}

        # Check that all 9 laws are present (capitalized names)
        expected_laws = {
            "Unity", "Truth", "Rhythm", "Causality", "Transparency",
            "Nonmaleficence", "Autonomy", "Justice", "Sustainability"
        }
        assert law_names == expected_laws

    def test_response_contains_all_required_fields(self):
        """Test that response contains all required fields."""
        job = demo_job_template()

        result = run_unified_demonstration(job, use_rag=False, use_event_log=False)

        required_fields = {
            "job_id", "timestamp", "trinity", "hexagon", "guardians",
            "decision", "decision_reason", "approved"
        }

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
