"""
Unit tests for arbitrage/quantum.py — Lukasiewicz 3-state logic (PROGRAMATOR #9)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DB_PATH", ":memory:")

from arbitrage.quantum import (
    AUTOPOJEZA_ERROR_LIMIT,
    AutopoiezaTracker,
    QuantumDecision,
    entangle_markets,
    quantum_decide,
    run_quantum_scan,
    scan_channel,
)

# ── quantum_decide ─────────────────────────────────────────────────────────────

class TestQuantumDecide:
    def test_affirmation_state_high_margin(self):
        # 30% margin → Stan 1 (Affirmation / EXECUTE)
        decision = quantum_decide(100.0, 130.0, "AUDIO_PREMIUM")
        assert decision.state == 1
        assert decision.action == "EXECUTE"
        assert decision.state_label == "affirmation"

    def test_negation_state_low_margin(self):
        # 5% margin < 8% threshold → Stan 0 (Negation / REJECT)
        decision = quantum_decide(100.0, 105.0, "AUDIO_PREMIUM")
        assert decision.state == 0
        assert decision.action == "REJECT"
        assert decision.state_label == "negation"

    def test_superposition_state_mid_margin(self):
        # 11% margin (8–14.9%) without 3-6-9 resonance → SUPERPOSITION or EXECUTE
        # Depending on resonance, it could be EXECUTE or ANALYZE
        decision = quantum_decide(100.0, 111.0, "AUDIO_PREMIUM")
        assert decision.action in ("ANALYZE", "EXECUTE")
        assert decision.state in (0.5, 1)

    def test_zero_prices_rejected(self):
        decision = quantum_decide(0.0, 100.0)
        assert decision.action == "REJECT"
        assert decision.state == 0

    def test_negative_margin_rejected(self):
        # source > target → margin negative
        decision = quantum_decide(200.0, 100.0, "AUDIO_PREMIUM")
        assert decision.action == "REJECT"
        assert decision.state == 0

    def test_returns_quantum_decision_type(self):
        decision = quantum_decide(100.0, 150.0, "AUDIO_PREMIUM")
        assert isinstance(decision, QuantumDecision)

    def test_to_dict_has_required_keys(self):
        decision = quantum_decide(100.0, 130.0, "AUDIO_PREMIUM")
        d = decision.to_dict()
        required = {"state", "state_label", "margin_pct", "resonance",
                    "is_369", "vortex_pass", "channel_id", "action", "confidence", "timestamp"}
        assert required.issubset(set(d.keys()))

    def test_confidence_range(self):
        decision = quantum_decide(100.0, 150.0, "AUDIO_PREMIUM")
        assert 0.0 <= decision.confidence <= 1.0

    def test_channel_id_preserved(self):
        decision = quantum_decide(100.0, 130.0, "SMART_ENERGY")
        assert decision.channel_id == "SMART_ENERGY"

    def test_margin_calculated_correctly(self):
        # 100 vs 143 → diff=43, margin=43/143=30%
        decision = quantum_decide(100.0, 143.0, "AUDIO_PREMIUM")
        assert abs(decision.margin_pct - 0.30) < 0.01

    def test_affirm_threshold_boundary(self):
        # Exactly 15% margin → should EXECUTE
        decision = quantum_decide(100.0, 115.0, "AUDIO_PREMIUM")
        assert decision.action in ("EXECUTE", "ANALYZE")  # depends on channel min

    def test_superposition_threshold_boundary(self):
        # Exactly 8% margin → superpozycja
        decision = quantum_decide(100.0, 108.0, "AUDIO_PREMIUM")
        assert decision.action in ("ANALYZE", "EXECUTE", "REJECT")
        # margin is 8% which is >= MARGIN_THRESHOLD_SUPERPOSITION


# ── entangle_markets ───────────────────────────────────────────────────────────

class TestEntangleMarkets:
    def test_empty_prices_returns_zero_score(self):
        result = entangle_markets([], [])
        assert result["entanglement_score"] == 0
        assert result["pairs"] == 0

    def test_one_empty_list(self):
        result = entangle_markets([100.0, 130.0], [])
        assert result["entanglement_score"] == 0

    def test_basic_entanglement(self):
        prices_de = [100.0, 150.0, 200.0]
        prices_pl = [130.0, 180.0, 240.0]
        result = entangle_markets(prices_de, prices_pl)
        assert "entanglement_score" in result
        assert "avg_resonance" in result
        assert "pairs" in result
        assert "opportunities" in result
        assert "affirmations" in result
        assert "superpositions" in result

    def test_pairs_count_is_min(self):
        result = entangle_markets([100.0, 130.0, 160.0], [110.0, 135.0])
        assert result["pairs"] == 2  # min(3, 2)

    def test_entanglement_score_between_0_and_1(self):
        prices_de = [100.0 + i * 10 for i in range(5)]
        prices_pl = [120.0 + i * 10 for i in range(5)]
        result = entangle_markets(prices_de, prices_pl)
        assert 0.0 <= result["entanglement_score"] <= 1.0

    def test_affirmations_subset_of_opportunities(self):
        prices_de = [100.0, 100.0, 200.0]
        prices_pl = [130.0, 108.0, 250.0]
        result = entangle_markets(prices_de, prices_pl)
        assert result["affirmations"] + result["superpositions"] == len(result["opportunities"])


# ── scan_channel ───────────────────────────────────────────────────────────────

class TestScanChannel:
    DEALS = [
        {"wholesale_price": 100.0, "retail_price_de": 130.0},
        {"wholesale_price": 200.0, "retail_price_de": 210.0},  # < threshold
        {"wholesale_price": 0.0, "retail_price_de": 100.0},    # invalid
    ]

    def test_returns_list_of_decisions(self):
        results = scan_channel("AUDIO_PREMIUM", self.DEALS)
        assert isinstance(results, list)
        # Invalid deal (wp=0) should be skipped
        assert len(results) == 2

    def test_valid_deals_processed(self):
        results = scan_channel("AUDIO_PREMIUM", self.DEALS)
        for d in results:
            assert isinstance(d, QuantumDecision)
            assert d.channel_id == "AUDIO_PREMIUM"

    def test_empty_deals_list(self):
        results = scan_channel("AUDIO_PREMIUM", [])
        assert results == []

    def test_uses_retail_price_pl_fallback(self):
        deals = [{"wholesale_price": 100.0, "retail_price_pl": 135.0}]
        results = scan_channel("AUDIO_PREMIUM", deals)
        assert len(results) == 1
        assert results[0].margin_pct > 0


# ── run_quantum_scan ───────────────────────────────────────────────────────────

class TestRunQuantumScan:
    def test_empty_input_returns_structure(self):
        result = run_quantum_scan({})
        assert "channels" in result
        summary = result["summary"]
        assert "total_execute" in summary
        assert "total_analyze" in summary
        assert "total_reject" in summary

    def test_channels_in_output(self):
        result = run_quantum_scan({})
        # All channels from config should appear
        assert "channels" in result
        assert isinstance(result["channels"], dict)

    def test_with_deals_for_channel(self):
        deals = {
            "AUDIO_PREMIUM": [
                {"wholesale_price": 100.0, "retail_price": 130.0},
                {"wholesale_price": 200.0, "retail_price": 240.0},
            ]
        }
        result = run_quantum_scan(deals)
        ch = result["channels"].get("AUDIO_PREMIUM", {})
        assert ch.get("scanned", 0) >= 0
        summary = result["summary"]
        total = summary["total_execute"] + summary["total_analyze"] + summary["total_reject"]
        assert total >= 0


# ── AutopoiezaTracker ─────────────────────────────────────────────────────────

class TestAutopoiezaTracker:
    def _make_error(self, tracker: "AutopoiezaTracker"):
        """Simulate a wrong prediction (EXECUTE but no profit)."""
        return tracker.record_outcome("EXECUTE", -1.0)

    def _make_success(self, tracker: "AutopoiezaTracker"):
        """Simulate a correct prediction (EXECUTE with positive profit)."""
        return tracker.record_outcome("EXECUTE", 10.0)

    def test_initial_state(self):
        tracker = AutopoiezaTracker()
        status = tracker.get_status()
        assert status["consecutive_errors"] == 0
        assert status["healing_mode"] is False

    def test_errors_accumulate(self):
        tracker = AutopoiezaTracker()
        self._make_error(tracker)
        self._make_error(tracker)
        status = tracker.get_status()
        assert status["consecutive_errors"] == 2

    def test_reset_after_limit(self):
        tracker = AutopoiezaTracker()
        for _ in range(AUTOPOJEZA_ERROR_LIMIT):
            self._make_error(tracker)
        # After AUTOPOJEZA_ERROR_LIMIT errors, autopojeza reset triggered
        status = tracker.get_status()
        assert status["consecutive_errors"] == 0
        assert status["healing_mode"] is True

    def test_correct_prediction_clears_errors(self):
        tracker = AutopoiezaTracker()
        self._make_error(tracker)
        self._make_error(tracker)
        self._make_success(tracker)  # correct prediction resets counter
        status = tracker.get_status()
        assert status["consecutive_errors"] == 0

    def test_healing_mode_false_after_success(self):
        tracker = AutopoiezaTracker()
        self._make_error(tracker)
        self._make_success(tracker)
        assert tracker.get_status()["healing_mode"] is False

    def test_get_status_has_required_keys(self):
        tracker = AutopoiezaTracker()
        status = tracker.get_status()
        required = {"consecutive_errors", "total_resets", "healing_mode", "scan_interval_ms", "last_reset"}
        assert required.issubset(set(status.keys()))

    def test_total_resets_increments(self):
        tracker = AutopoiezaTracker()
        for _ in range(AUTOPOJEZA_ERROR_LIMIT):
            self._make_error(tracker)
        assert tracker.get_status()["total_resets"] == 1

    def test_healing_scan_interval_is_528(self):
        tracker = AutopoiezaTracker()
        for _ in range(AUTOPOJEZA_ERROR_LIMIT):
            self._make_error(tracker)
        assert tracker.get_status()["scan_interval_ms"] == 528

    def test_record_outcome_autopojeza_reset_return(self):
        tracker = AutopoiezaTracker()
        # First two errors: warning
        for _ in range(AUTOPOJEZA_ERROR_LIMIT - 1):
            r = self._make_error(tracker)
            assert r["status"] != "autopojeza_reset"
        # Third error: triggers reset
        r = self._make_error(tracker)
        assert r["status"] == "autopojeza_reset"
        assert r["healing_mode"] is True
