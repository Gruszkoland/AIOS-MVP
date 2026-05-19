"""
Test integracyjny splitu feedback_engine.py
Weryfikuje:
  1. Import poszczególnych modułów (behavior, vera, judge, golden)
  2. Import orkiestratora (feedback_engine) z re-exportami
  3. Tworzenie instancji i przepływ OODA
  4. Event bus integration
"""
import os
import sys

# Ensure harmonia-dashboard is on the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "harmonia-dashboard"))

def test_feedback_split_all():
    passed = 0
    failed = 0

    def check(label, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  OK  {label}")
        else:
            failed += 1
            print(f"  FAIL  {label}")

    # --- 1. Direct imports from sub-modules ---
    print("=== 1. Direct sub-module imports ===")

    from behavior import BehaviorLogger, Interaction
    check("behavior.BehaviorLogger", BehaviorLogger is not None)
    check("behavior.Interaction", Interaction is not None)

    from vera import VERAScore, VERAScorer
    check("vera.VERAScorer", VERAScorer is not None)
    check("vera.VERAScore", VERAScore is not None)

    from judge import Judge, JudgeVerdict
    check("judge.Judge", Judge is not None)
    check("judge.JudgeVerdict", JudgeVerdict is not None)

    from golden import GoldenAnswerStore
    check("golden.GoldenAnswerStore", GoldenAnswerStore is not None)

    # --- 2. Re-exports from feedback_engine ---
    print("\n=== 2. Re-exports from feedback_engine ===")

    from feedback_engine import (
        HAS_EVENT_BUS,
        FeedbackLoop,
        get_feedback_loop,
    )
    from feedback_engine import (
        BehaviorLogger as BL2,
    )
    from feedback_engine import (
        GoldenAnswerStore as GA2,
    )
    from feedback_engine import (
        Judge as J2,
    )
    from feedback_engine import (
        VERAScorer as VS2,
    )
    check("feedback_engine re-exports BehaviorLogger", BL2 is BehaviorLogger)
    check("feedback_engine re-exports VERAScorer", VS2 is VERAScorer)
    check("feedback_engine re-exports Judge", J2 is Judge)
    check("feedback_engine re-exports GoldenAnswerStore", GA2 is GoldenAnswerStore)
    check("feedback_engine has FeedbackLoop", FeedbackLoop is not None)
    check("feedback_engine has get_feedback_loop", callable(get_feedback_loop))
    check("feedback_engine HAS_EVENT_BUS", isinstance(HAS_EVENT_BUS, bool))

    # --- 3. Instantiation & OODA flow ---
    print("\n=== 3. Instantiation & OODA cycle ===")

    loop = FeedbackLoop()
    check("FeedbackLoop() created", loop is not None)
    check("loop.behavior is BehaviorLogger", isinstance(loop.behavior, BehaviorLogger))
    check("loop.vera is VERAScorer", isinstance(loop.vera, VERAScorer))
    check("loop.judge is Judge", isinstance(loop.judge, Judge))
    check("loop.golden is GoldenAnswerStore", isinstance(loop.golden, GoldenAnswerStore))

    # Observe
    result = loop.observe("Test prompt", "Test response", model="test", latency_ms=100)
    check("observe() returns interaction_id", "interaction_id" in result)
    check("observe() returns vera dict", "vera" in result and isinstance(result["vera"], dict))

    iid = result["interaction_id"]

    # Orient
    orient_result = loop.orient(iid, accepted=True, score=2)
    check("orient() returns feedback_recorded", orient_result.get("feedback_recorded") is True)
    check("orient() returns vera update", orient_result.get("vera") is not None)
    check("orient() returns judge verdict", orient_result.get("judge") is not None)

    # Decide
    decide_result = loop.decide()
    check("decide() returns vera_average", "vera_average" in decide_result)
    check("decide() returns recommendations", "recommendations" in decide_result)

    # Act
    act_result = loop.act("Test prompt")
    check("act() returns augmented_context key", "augmented_context" in act_result)

    # Full status
    status = loop.get_full_status()
    check("get_full_status() returns behavior", "behavior" in status)
    check("get_full_status() returns vera", "vera" in status)
    check("get_full_status() returns judge", "judge" in status)

    # --- 4. Event bus ---
    print("\n=== 4. Event bus integration ===")
    check("HAS_EVENT_BUS is True", HAS_EVENT_BUS is True)

    if HAS_EVENT_BUS:
        from memory_events import get_event_bus
        bus = get_event_bus()
        metrics = bus.get_metrics()
        check("Events were emitted during OODA", metrics["events_emitted"] > 0)
        # No subscribers registered in test → delivered = 0 is correct
        check("Delivery rate consistent", metrics["delivery_rate"] >= 0)

    # --- Summary ---
    print(f"\n{'='*40}")
    total = passed + failed
    print(f"PASSED: {passed}/{total}")
    print(f"FAILED: {failed}/{total}")
    assert failed == 0, f"{failed} test(s) failed"
    if failed == 0:
        print("\nALL INTEGRATION TESTS PASSED")

if __name__ == "__main__":
    test_feedback_split_all()
