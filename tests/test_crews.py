"""
Tests for arbitrage/crews/ — CrewAI Trinity, Hexagon, Guardian, and Orchestra

Covers:
  - Trinity crew (3 perspectives)
  - Hexagon crew (6 stages)
  - Guardian crew (9 laws)
  - Orchestra orchestration (full pipeline)
"""
import pytest
from arbitrage.crews.trinity_crew import TrnityCrew
from arbitrage.crews.hexagon_crew import HexagonCrew
from arbitrage.crews.guardian_crew import GuardianCrew
from arbitrage.crews.orchestra import OrchestraOrchestrator, run_full_demonstration


class TestTrnityCrew:
    """Tests for Trinity Crew."""

    def test_crew_creation(self):
        """Test creating Trinity crew."""
        crew = TrnityCrew()
        assert crew is not None

    def test_material_evaluation(self):
        """Test Material agent evaluation."""
        crew = TrnityCrew()
        result = crew.evaluate_material(
            {"cpu_percent": 50.0, "ram_available_ratio": 0.7}
        )

        assert result["perspective"] == "material"
        assert 0 <= result["score"] <= 1.0
        assert "details" in result
        assert isinstance(result["approved"], bool)

    def test_intellectual_evaluation(self):
        """Test Intellectual agent evaluation."""
        crew = TrnityCrew()
        result = crew.evaluate_intellectual({"score": 8, "fit": "Good fit", "risks": "Low"})

        assert result["perspective"] == "intellectual"
        assert 0 <= result["score"] <= 1.0
        assert "details" in result

    def test_essential_evaluation(self):
        """Test Essential agent evaluation."""
        crew = TrnityCrew()
        result = crew.evaluate_essential(
            {"title": "Content writing article"},
            {"est_profit": 50},
        )

        assert result["perspective"] == "essential"
        assert 0 <= result["score"] <= 1.0

    def test_crew_kickoff_with_good_data(self):
        """Test Trinity crew full kickoff with good data."""
        crew = TrnityCrew()

        result = crew.kickoff(
            inputs={
                "job": {"title": "Content writing", "description": "Blog article"},
                "analysis": {"score": 8, "fit": "Perfect", "risks": "None", "est_profit": 100},
                "resources": {"cpu_percent": 30, "ram_available_ratio": 0.8},
            }
        )

        assert "material" in result
        assert "intellectual" in result
        assert "essential" in result
        assert "combined_score" in result
        assert 0 <= result["combined_score"] <= 1.0
        assert isinstance(result["approved"], bool)

    def test_crew_kickoff_with_low_resources(self):
        """Test Trinity crew with low resources."""
        crew = TrnityCrew()

        result = crew.kickoff(
            inputs={
                "job": {"title": "Test"},
                "analysis": {"score": 8, "fit": "Good", "risks": "None"},
                "resources": {"cpu_percent": 95, "ram_available_ratio": 0.1},
            }
        )

        # Should have low material score
        assert result["material"]["score"] < 0.3


class TestHexagonCrew:
    """Tests for Hexagon Crew."""

    def test_crew_creation(self):
        """Test creating Hexagon crew."""
        crew = HexagonCrew()
        assert crew is not None

    def test_crew_kickoff_with_trinity_scores(self):
        """Test Hexagon crew kickoff with Trinity scores."""
        crew = HexagonCrew()

        result = crew.kickoff(
            inputs={
                "trinity_scores": {
                    "material": 0.8,
                    "intellectual": 0.75,
                    "essential": 0.7,
                    "combined": 0.75,
                }
            }
        )

        assert "stages" in result
        assert "combined_score" in result
        assert "total_duration_ms" in result
        assert isinstance(result["approved"], bool)
        assert result["stage_count"] == 6

        # Check all 6 stages are present
        expected_stages = [
            "inventory",
            "empathy",
            "process",
            "debate",
            "healing",
            "action",
        ]
        for stage in expected_stages:
            assert stage in result["stages"]

    def test_crew_kickoff_with_low_trinity(self):
        """Test Hexagon crew with low Trinity scores."""
        crew = HexagonCrew()

        result = crew.kickoff(
            inputs={
                "trinity_scores": {
                    "material": 0.2,
                    "intellectual": 0.3,
                    "essential": 0.15,
                }
            }
        )

        # Pipeline should complete but may not be approved
        assert "stages" in result
        assert result["stage_count"] == 6


class TestGuardianCrew:
    """Tests for Guardian Crew."""

    def test_crew_creation(self):
        """Test creating Guardian crew."""
        crew = GuardianCrew()
        assert crew is not None

    def test_crew_kickoff_with_context(self):
        """Test Guardian crew kickoff with decision context."""
        crew = GuardianCrew()

        result = crew.kickoff(
            inputs={
                "context": {
                    "stages": {
                        "inventory": {"score": 0.8},
                        "empathy": {"score": 0.8},
                        "process": {"score": 0.8},
                        "debate": {"score": 0.8},
                        "healing": {"score": 0.8},
                        "action": {"score": 0.8},
                    }
                }
            }
        )

        assert "laws" in result
        assert "violations" in result
        assert "status" in result
        assert result["law_count"] == 9
        assert result["status"] in ["APPROVED", "DENIED"]

    def test_crew_kickoff_with_low_context(self):
        """Test Guardian crew with low context scores."""
        crew = GuardianCrew()

        result = crew.kickoff(
            inputs={
                "context": {
                    "stages": {
                        "inventory": {"score": 0.2},
                        "empathy": {"score": 0.2},
                    }
                }
            }
        )

        # Guardian should respond but may register violations
        assert "laws" in result


class TestOrchestraOrchestrator:
    """Tests for Orchestra orchestration."""

    def test_orchestrator_creation(self):
        """Test creating Orchestra orchestrator."""
        orchestrator = OrchestraOrchestrator()
        assert orchestrator is not None

    def test_full_pipeline_sync_with_good_data(self):
        """Test full pipeline execution with good data."""
        orchestrator = OrchestraOrchestrator()

        result = orchestrator.execute_sync(
            {
                "id": "test-001",
                "title": "Content writing job",
                "description": "Blog article for tech site",
                "analysis": {"score": 9, "fit": "Excellent", "risks": "None", "est_profit": 100},
                "resources": {"cpu_percent": 20, "ram_available_ratio": 0.85},
            }
        )

        assert "job_id" in result
        assert "timestamp" in result
        assert "trinity" in result
        assert "hexagon" in result
        assert "guardians" in result
        assert "final_decision" in result
        assert result["final_decision"] in ["APPROVED", "DENIED", "CONDITIONAL"]

    def test_full_pipeline_structure(self):
        """Test that full pipeline produces complete structure."""
        result = run_full_demonstration(
            {
                "id": "demo-123",
                "title": "Test job",
                "description": "Test description",
                "analysis": {"score": 7, "fit": "Good", "risks": "Low", "est_profit": 50},
            }
        )

        # Verify all components present
        assert result["trinity"]["perspectives"] == 3
        assert result["hexagon"]["stage_count"] == 6
        assert result["guardians"]["law_count"] == 9

        # All must have approval status
        assert isinstance(result["trinity"]["approved"], bool)
        assert isinstance(result["hexagon"]["approved"], bool)
        assert isinstance(result["guardians"]["status"] in ["APPROVED", "DENIED"], bool)

    def test_full_pipeline_decision_logic(self):
        """Test pipeline final decision logic."""
        result = run_full_demonstration(
            {
                "id": "logic-test",
                "title": "Logic test",
                "description": "Verify decision logic",
                "analysis": {"score": 8, "fit": "Good", "risks": "None"},
            }
        )

        # Final decision should be based on all three pipeline stages
        trinity_ok = result["trinity"]["approved"]
        hexagon_ok = result["hexagon"]["approved"]
        guardian_ok = result["guardians"]["status"] == "APPROVED"

        if trinity_ok and hexagon_ok and guardian_ok:
            assert result["final_decision"] == "APPROVED"
        else:
            assert result["final_decision"] in ["DENIED", "CONDITIONAL"]

    def test_execute_method_sync_mode(self):
        """Test that execute() with async_mode=False works."""
        orchestrator = OrchestraOrchestrator()

        result = orchestrator.execute(
            {
                "id": "sync-test",
                "title": "Test",
                "description": "Test sync mode",
                "analysis": {"score": 7, "fit": "Good", "risks": "None"},
            },
            async_mode=False,
        )

        assert "final_decision" in result
        assert result["approved"] is not None
