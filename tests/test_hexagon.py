"""
Tests for arbitrage/hexagon.py — Hexagon Pipeline Processor

Covers:
  - HexagonProcessor.process() with valid Trinity scores
  - All 6 stages (inventory → empathy → process → debate → healing → action)
  - Error handling and stage failures
"""
import pytest
from arbitrage.hexagon import (
    HexagonProcessor,
    HexagonResult,
    HexagonStageResult,
    _inventory_stage,
    _empathy_stage,
    _process_stage,
    _debate_stage,
    _healing_stage,
    _action_stage,
)


class TestHexagonStageResult:
    """Tests for HexagonStageResult dataclass."""

    def test_stage_result_creation(self):
        """Test creating a HexagonStageResult."""
        result = HexagonStageResult(
            stage_name="inventory",
            score=0.75,
            duration_ms=42.5,
            analysis={"test": "data"},
            recommendations=["rec1"],
            risks=["risk1"],
            approved=True,
        )

        assert result.stage_name == "inventory"
        assert result.duration_ms == 42.5
        assert result.score == 0.75
        assert result.approved is True

    def test_stage_result_to_dict(self):
        """Test converting HexagonStageResult to dict."""
        result = HexagonStageResult(
            stage_name="inventory",
            score=0.7543,
            approved=True,
        )

        result_dict = result.to_dict()

        assert result_dict["stage_name"] == "inventory"
        assert result_dict["duration_ms"] == 0.0
        assert result_dict["score"] == 0.7543  # rounded
        assert result_dict["approved"] is True


class TestHexagonResult:
    """Tests for HexagonResult aggregation."""

    def test_hexagon_result_creation(self):
        """Test creating a HexagonResult."""
        result = HexagonResult(
            stages=[],
            combined_score=0.65,
            total_duration_ms=250.0,
            approved=True,
        )

        assert result.combined_score == 0.65
        assert result.total_duration_ms == 250.0
        assert result.approved is True

    def test_hexagon_result_stage_by_name(self):
        """Test finding stage by name in HexagonResult."""
        stage1 = HexagonStageResult(stage_name="inventory", score=0.7)
        stage2 = HexagonStageResult(stage_name="empathy", score=0.8)

        result = HexagonResult(stages=[stage1, stage2])

        found_stage = result.stage_by_name("inventory")
        assert found_stage is not None
        assert found_stage.stage_name == "inventory"
        assert found_stage.score == 0.7

        not_found = result.stage_by_name("nonexistent")
        assert not_found is None


class TestHexagonStages:
    """Tests for individual Hexagon stages."""

    def test_inventory_stage_with_good_trinity(self):
        """Test Inventory stage with good Trinity scores."""
        trinity_scores = {
            "material": 0.8,
            "intellectual": 0.75,
            "essential": 0.7,
        }

        result = _inventory_stage(trinity_scores)

        assert result.stage_name == "inventory"
        assert result.score >= 0.6  # Should be high
        assert result.approved is True
        assert len(result.recommendations) > 0
        assert result.duration_ms >= 0

    def test_inventory_stage_with_low_resources(self):
        """Test Inventory stage with low resources."""
        trinity_scores = {
            "material": 0.2,  # Low resources
            "intellectual": 0.75,
            "essential": 0.7,
        }

        result = _inventory_stage(trinity_scores)

        assert result.approved is True  # Still approved (score >= 0.3)
        assert any("resource" in risk.lower() for risk in result.risks)

    def test_empathy_stage_with_good_inventory(self):
        """Test Empathy stage with good Inventory result."""
        inventory_result = HexagonStageResult(
            stage_name="inventory",
            score=0.75,
        )

        result = _empathy_stage(inventory_result)

        assert result.stage_name == "empathy"
        assert result.approved is True
        assert result.score >= 0.6

    def test_empathy_stage_with_failed_inventory(self):
        """Test Empathy stage when Inventory failed."""
        inventory_result = HexagonStageResult(
            stage_name="inventory",
            score=0.0,
            approved=False,
        )

        result = _empathy_stage(inventory_result)

        assert result.stage_name == "empathy"
        assert result.approved is False
        assert result.score == 0.0

    def test_process_stage(self):
        """Test Process stage."""
        empathy_result = HexagonStageResult(
            stage_name="empathy",
            score=0.7,
        )

        result = _process_stage(empathy_result)

        assert result.stage_name == "process"
        assert result.approved is True
        assert len(result.analysis) > 0

    def test_debate_stage(self):
        """Test Debate stage."""
        process_result = HexagonStageResult(
            stage_name="process",
            score=0.75,
        )

        result = _debate_stage(process_result)

        assert result.stage_name == "debate"
        assert result.approved is True

    def test_healing_stage(self):
        """Test Healing stage."""
        debate_result = HexagonStageResult(
            stage_name="debate",
            score=0.7,
        )

        result = _healing_stage(debate_result)

        assert result.stage_name == "healing"
        assert result.approved is True

    def test_action_stage(self):
        """Test Action (final) stage."""
        healing_result = HexagonStageResult(
            stage_name="healing",
            score=0.75,
        )

        result = _action_stage(healing_result)

        assert result.stage_name == "action"
        assert result.approved is True
        assert any("RECOMMEND" in rec or "APPROVAL" in rec for rec in result.recommendations)


class TestHexagonProcessor:
    """Tests for HexagonProcessor orchestration."""

    def test_processor_creation(self):
        """Test creating HexagonProcessor."""
        processor = HexagonProcessor()
        assert processor is not None

    def test_full_pipeline_with_good_trinity(self):
        """Test full Hexagon pipeline with good Trinity scores."""
        processor = HexagonProcessor()

        trinity_scores = {
            "material": 0.85,
            "intellectual": 0.8,
            "essential": 0.75,
            "combined": 0.8,
        }

        result = processor.process(trinity_scores)

        assert isinstance(result, HexagonResult)
        assert len(result.stages) == 6
        assert result.stages[0].stage_name == "inventory"
        assert result.stages[-1].stage_name == "action"
        assert result.combined_score >= 0.5  # Should be reasonably high
        assert result.total_duration_ms >= 0
        assert result.approved is True

    def test_full_pipeline_stage_sequence(self):
        """Test that pipeline stages execute in correct sequence."""
        processor = HexagonProcessor()

        trinity_scores = {
            "material": 0.7,
            "intellectual": 0.7,
            "essential": 0.7,
        }

        result = processor.process(trinity_scores)

        stage_names = [s.stage_name for s in result.stages]
        expected_order = ["inventory", "empathy", "process", "debate", "healing", "action"]

        assert stage_names == expected_order

    def test_full_pipeline_with_low_trinity(self):
        """Test pipeline with low Trinity scores."""
        processor = HexagonProcessor()

        trinity_scores = {
            "material": 0.2,
            "intellectual": 0.3,
            "essential": 0.15,
        }

        result = processor.process(trinity_scores)

        # Pipeline should complete, but most stages should fail
        assert len(result.stages) == 6
        # With very low scores, later stages may not approve
        assert result.total_duration_ms >= 0

    def test_full_pipeline_each_stage_has_data(self):
        """Test that each stage produces meaningful output."""
        processor = HexagonProcessor()

        trinity_scores = {
            "material": 0.75,
            "intellectual": 0.75,
            "essential": 0.75,
        }

        result = processor.process(trinity_scores)

        for stage in result.stages:
            assert stage.stage_name is not None
            assert stage.duration_ms >= 0
            assert 0 <= stage.score <= 1.0
            assert isinstance(stage.analysis, dict)
            assert isinstance(stage.recommendations, list)
            assert isinstance(stage.risks, list)
            assert isinstance(stage.approved, bool)

    def test_combined_score_is_average(self):
        """Test that combined_score is average of all 6 stages."""
        processor = HexagonProcessor()

        trinity_scores = {
            "material": 0.7,
            "intellectual": 0.7,
            "essential": 0.7,
        }

        result = processor.process(trinity_scores)

        individual_scores = [s.score for s in result.stages]
        expected_average = sum(individual_scores) / len(individual_scores)

        assert abs(result.combined_score - expected_average) < 0.001

    def test_overall_approval_needs_all_stages(self):
        """Test that overall approval requires all stages to approve."""
        processor = HexagonProcessor()

        # Even with good scores, if any stage fails, result should reflect it
        trinity_scores = {
            "material": 0.7,
            "intellectual": 0.7,
            "essential": 0.7,
        }

        result = processor.process(trinity_scores)

        # Check that approved status matches all stages approving
        all_approved = all(s.approved for s in result.stages)
        assert result.approved == all_approved
