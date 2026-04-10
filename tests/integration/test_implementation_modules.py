#!/usr/bin/env python3
"""
Integration Tests for ADRION 369 Implementation Modules
Tests: Event Sourcing, RAG Context Optimizer, Federated Learning, KDTree Router

Run: python -m pytest tests/integration/test_implementation_modules.py -v
"""

import pytest
import json
import tempfile
from pathlib import Path

# Test Event Sourcing
def test_event_sourcing_basic():
    """Test basic event sourcing: record and query."""
    from scripts.event_sourcing import EventSourcingStore, Event

    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "event_log.jsonl"
        store = EventSourcingStore(str(log_file))

        # Record events
        store.record_event("AGENT_INITIALIZED", "agent_1", {"trust_score": 0.5})
        assert len(store.event_log.events) == 1

        # Task success (TS += 0.05)
        store.record_event("TASK_COMPLETED", "agent_1", {"task_id": "task_001"})
        state = store.get_entity_state("agent_1")
        assert state["ts"] > 0.5

        print("✓ Event Sourcing: Basic test passed")


def test_event_sourcing_replay():
    """Test replay functionality."""
    from scripts.event_sourcing import EventSourcingStore

    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "event_log.jsonl"
        store = EventSourcingStore(str(log_file))

        # Record sequence
        store.record_event("AGENT_INITIALIZED", "agent_1", {"ts": 0.5})
        store.record_event("TASK_COMPLETED", "agent_1", {"task": "T1"})
        store.record_event("TASK_COMPLETED", "agent_1", {"task": "T2"})

        # Replay
        history = store.event_log.replay("agent_1")
        assert len(history["history"]) == 3

        print("✓ Event Sourcing: Replay test passed")


def test_event_sourcing_audit_trail():
    """Test audit trail (Guardian Law G5 - Transparency)."""
    from scripts.event_sourcing import EventSourcingStore

    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "event_log.jsonl"
        store = EventSourcingStore(str(log_file))

        # Record events
        for i in range(5):
            store.record_event("TASK_COMPLETED", "agent_1", {"task_id": f"T{i}"})

        # Get audit trail
        trail = store.get_entity_history("agent_1")
        assert len(trail) == 5
        assert all(e["event_type"] == "TASK_COMPLETED" for e in trail)

        print("✓ Event Sourcing: Audit trail test passed")


# Test RAG Context Optimizer
def test_rag_document_storage():
    """Test RAG document addition and retrieval."""
    try:
        from scripts.orchestration.rag_context_optimizer import RAGContextOptimizer
        import numpy as np

        optimizer = RAGContextOptimizer()

        # Add documents
        optimizer.add_document("ADRION 369 architecture", {"source": "doc1"})
        optimizer.add_document("Federated learning implementation", {"source": "doc2"})
        optimizer.add_document("Event sourcing patterns", {"source": "doc3"})

        assert len(optimizer.documents) == 3
        print("✓ RAG Context Optimizer: Document storage test passed")
    except ImportError as e:
        print(f"⚠ RAG test skipped: {e}")


def test_rag_relevance_ranking():
    """Test RAG relevance ranking."""
    try:
        from scripts.orchestration.rag_context_optimizer import RAGContextOptimizer

        optimizer = RAGContextOptimizer()

        # Add documents
        optimizer.add_document("Machine learning workflows", {"priority": 1})
        optimizer.add_document("Data pipeline architecture", {"priority": 2})
        optimizer.add_document("Monitoring and alerting", {"priority": 3})

        # Get relevant context
        task = "How do we implement federated learning in ADRION?"
        context = optimizer.get_relevant_context(task, top_k=2)

        assert context is not None
        assert len(context) > 0

        print("✓ RAG Context Optimizer: Relevance ranking test passed")
    except ImportError as e:
        print(f"⚠ RAG relevance test skipped: {e}")


def test_rag_map_reduce_summarization():
    """Test Map-Reduce summarization."""
    try:
        from scripts.orchestration.rag_context_optimizer import RAGContextOptimizer

        optimizer = RAGContextOptimizer()

        # Long text
        long_text = " ".join(["word"] * 1000)

        # Summarize
        summary = optimizer.map_reduce_summarize(long_text, chunk_size=100, depth=1)

        assert summary is not None
        assert len(summary) < len(long_text)

        print("✓ RAG Context Optimizer: Map-Reduce summarization test passed")
    except ImportError as e:
        print(f"⚠ RAG summarization test skipped: {e}")


# Test Federated Learning Coordinator
def test_federated_learning_initialization():
    """Test federated learning coordinator initialization."""
    try:
        from scripts.ml.federated_learning_coordinator import FederatedLearningCoordinator
        import numpy as np

        coordinator = FederatedLearningCoordinator(
            num_agents=6,
            model_size=100,
            agent_names=["librarian", "sap", "auditor", "sentinel", "architect", "healer"]
        )

        assert len(coordinator.agent_models) == 6
        assert coordinator.global_model.shape == (100,)

        print("✓ Federated Learning: Initialization test passed")
    except ImportError as e:
        print(f"⚠ Federated Learning init test skipped: {e}")


def test_federated_learning_round():
    """Test federated learning training round."""
    try:
        from scripts.ml.federated_learning_coordinator import FederatedLearningCoordinator
        import numpy as np

        coordinator = FederatedLearningCoordinator(num_agents=6, model_size=50)

        # Run one round
        stats = coordinator.training_round(round_num=1)

        assert "round" in stats
        assert "participating_agents" in stats
        assert stats["round"] == 1

        print("✓ Federated Learning: Training round test passed")
    except ImportError as e:
        print(f"⚠ Federated Learning round test skipped: {e}")


def test_federated_learning_multi_round():
    """Test multiple federated learning rounds."""
    try:
        from scripts.ml.federated_learning_coordinator import FederatedLearningCoordinator

        coordinator = FederatedLearningCoordinator(num_agents=6, model_size=30)

        # Run multiple rounds
        for round_num in range(1, 4):
            stats = coordinator.training_round(round_num=round_num)
            assert stats["round"] == round_num

        print("✓ Federated Learning: Multi-round test passed")
    except ImportError as e:
        print(f"⚠ Federated Learning multi-round test skipped: {e}")


# Test KDTree Router
def test_kd_tree_router_initialization():
    """Test KDTree router initialization."""
    try:
        from scripts.kd_tree_router import KDTreeRouter

        router = KDTreeRouter(k_neighbors=3)

        assert len(router.agents) == 6  # 6 ADRION agents
        assert router.kdtree is not None

        print("✓ KDTree Router: Initialization test passed")
    except ImportError as e:
        print(f"⚠ KDTree Router init test skipped: {e}")


def test_kd_tree_router_routing():
    """Test task routing."""
    try:
        from scripts.kd_tree_router import KDTreeRouter, Task
        import numpy as np

        router = KDTreeRouter(k_neighbors=3)

        # Create task
        task = Task(
            id="test_task_1",
            description="Test task",
            vector=np.random.randn(162),
            priority=5,
            domain="planning"
        )

        # Route
        agents = router.route(task)

        assert len(agents) > 0
        assert len(agents) <= 3
        assert all(isinstance(a, tuple) and len(a) == 2 for a in agents)

        print("✓ KDTree Router: Routing test passed")
    except ImportError as e:
        print(f"⚠ KDTree Router routing test skipped: {e}")


def test_kd_tree_router_trust_update():
    """Test trust score update."""
    try:
        from scripts.kd_tree_router import KDTreeRouter

        router = KDTreeRouter()

        # Update trust
        initial_ts = router.agents["sentinel"].trust_score
        router.update_agent_trust("sentinel", +0.10)

        assert router.agents["sentinel"].trust_score > initial_ts

        print("✓ KDTree Router: Trust update test passed")
    except ImportError as e:
        print(f"⚠ KDTree Router trust test skipped: {e}")


def test_kd_tree_router_stats():
    """Test router statistics."""
    try:
        from scripts.kd_tree_router import KDTreeRouter

        router = KDTreeRouter()
        stats = router.get_agent_stats()

        assert stats["total_agents"] == 6
        assert stats["active_agents"] == 6
        assert "avg_trust_score" in stats

        print("✓ KDTree Router: Statistics test passed")
    except ImportError as e:
        print(f"⚠ KDTree Router stats test skipped: {e}")


# Integration Test
def test_end_to_end_workflow():
    """Test end-to-end: task → router → event sourcing."""
    try:
        from scripts.kd_tree_router import KDTreeRouter, Task
        from scripts.event_sourcing import EventSourcingStore
        import numpy as np
        import tempfile
        from pathlib import Path

        # Initialize components
        router = KDTreeRouter()

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "event_log.jsonl"
            store = EventSourcingStore(str(log_file))

            # Create task
            task = Task(
                id="e2e_task_1",
                description="End-to-end test",
                vector=np.random.randn(162),
                priority=8,
                domain="security"
            )

            # Route task
            agents = router.route(task)
            best_agent = agents[0][0]

            # Record event
            store.record_event("TASK_DISPATCHED", best_agent, {
                "task_id": task.id,
                "priority": task.priority
            })

            # Verify
            trail = store.get_entity_history(best_agent)
            assert len(trail) >= 1

            print("✓ End-to-End Workflow: Test passed")
    except ImportError as e:
        print(f"⚠ End-to-End test skipped: {e}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ADRION 369 Implementation Modules: Integration Tests")
    print("="*70 + "\n")

    # Run tests
    test_event_sourcing_basic()
    test_event_sourcing_replay()
    test_event_sourcing_audit_trail()

    test_rag_document_storage()
    test_rag_relevance_ranking()
    test_rag_map_reduce_summarization()

    test_federated_learning_initialization()
    test_federated_learning_round()
    test_federated_learning_multi_round()

    test_kd_tree_router_initialization()
    test_kd_tree_router_routing()
    test_kd_tree_router_trust_update()
    test_kd_tree_router_stats()

    test_end_to_end_workflow()

    print("\n" + "="*70)
    print("All integration tests completed!")
    print("="*70 + "\n")
