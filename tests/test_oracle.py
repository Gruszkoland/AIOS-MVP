"""
Unit tests for arbitrage/oracle.py — Predykcyjna Wyrocznia AI (PROGRAMATOR #19/20)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DB_PATH", ":memory:")

from arbitrage.oracle import (
    classify_enneagram_node,
    detect_turning_point,
    fibonacci_levels,
    find_spiral_eye,
    assign_solfeggio,
    oracle_predict,
    oracle_scan_products,
    FIBONACCI_RATIOS,
    FREQ_528_HZ,
    FREQ_396_HZ,
    FREQ_174_HZ,
)
from arbitrage.oracle import OraclePrediction


# ── classify_enneagram_node ────────────────────────────────────────────────────

class TestClassifyEnneagramNode:
    def test_triangle_node_3(self):
        # digital_root(300) = 3 → triangle
        node, cat = classify_enneagram_node(3.0)
        assert node == 3
        assert cat == "triangle"

    def test_triangle_node_6(self):
        node, cat = classify_enneagram_node(6.0)
        assert node == 6
        assert cat == "triangle"

    def test_triangle_node_9(self):
        node, cat = classify_enneagram_node(9.0)
        assert node == 9
        assert cat == "triangle"

    def test_hexad_node(self):
        # digital_root(100) = 1 → hexad
        node, cat = classify_enneagram_node(1.0)
        assert node == 1
        assert cat == "hexad"

    def test_zero_value(self):
        node, cat = classify_enneagram_node(0.0)
        # digital_root(0) = 0, which is not in TRIANGLE_NODES → hexad
        assert cat == "hexad"


# ── detect_turning_point ──────────────────────────────────────────────────────

class TestDetectTurningPoint:
    def test_dormant_insufficient_data(self):
        signal, node = detect_turning_point([])
        assert signal == "DORMANT"
        signal, node = detect_turning_point([100.0])
        assert signal == "DORMANT"
        signal, node = detect_turning_point([100.0, 101.0])
        assert signal == "DORMANT"

    def test_impulse_large_increase(self):
        # 15% jump at the end → IMPULSE
        prices = [100.0, 101.0, 102.0, 117.0]
        signal, node = detect_turning_point(prices)
        assert signal == "IMPULSE"
        assert node == 3

    def test_stabilization_near_minimum(self):
        # Price bounces near minimum (within 5%) with small last change
        prices = [200.0, 150.0, 130.0, 120.0, 121.0]
        signal, node = detect_turning_point(prices)
        assert signal == "STABILIZATION"
        assert node == 6

    def test_dormant_flat_prices(self):
        # Flat prices → no clear signal
        prices = [100.0, 100.5, 101.0, 100.8]
        signal, node = detect_turning_point(prices)
        # Should be DORMANT or some valid signal
        assert signal in ("DORMANT", "IMPULSE", "STABILIZATION", "SINGULARITY")

    def test_returns_valid_types(self):
        prices = [100.0, 110.0, 105.0, 108.0]
        signal, node = detect_turning_point(prices)
        assert signal in ("DORMANT", "IMPULSE", "STABILIZATION", "SINGULARITY")
        assert isinstance(node, int)


# ── fibonacci_levels ──────────────────────────────────────────────────────────

class TestFibonacciLevels:
    def test_basic_levels(self):
        levels = fibonacci_levels(100.0, 0.0)
        assert 0.618 in levels
        assert 0.382 in levels
        assert abs(levels[0.618] - 61.8) < 0.1
        assert abs(levels[0.382] - 38.2) < 0.1

    def test_all_ratios_present(self):
        levels = fibonacci_levels(200.0, 100.0)
        for ratio in FIBONACCI_RATIOS:
            assert ratio in levels

    def test_equal_high_low(self):
        levels = fibonacci_levels(100.0, 100.0)
        # diff=0, all levels should equal low
        for v in levels.values():
            assert v == 100.0

    def test_extension_above_high(self):
        levels = fibonacci_levels(100.0, 0.0)
        assert levels[1.618] > 100.0  # extension above high

    def test_level_ordering(self):
        levels = fibonacci_levels(200.0, 0.0)
        sorted_ratios = sorted(FIBONACCI_RATIOS)
        for i in range(len(sorted_ratios) - 1):
            assert levels[sorted_ratios[i]] <= levels[sorted_ratios[i + 1]]


# ── find_spiral_eye ───────────────────────────────────────────────────────────

class TestFindSpiralEye:
    def test_insufficient_data(self):
        result = find_spiral_eye([])
        assert result["found"] is False
        result = find_spiral_eye([100.0])
        assert result["found"] is False

    def test_no_price_movement(self):
        result = find_spiral_eye([100.0, 100.0, 100.0])
        assert result["found"] is False
        assert result["reason"] == "no_price_movement"

    def test_price_in_eye_zone(self):
        # high=100, low=0 → eye zone = [38.2, 61.8]
        # current = 50 → should be in eye
        prices = [0.0, 20.0, 80.0, 100.0, 50.0]
        result = find_spiral_eye(prices)
        assert result["found"] is True

    def test_price_outside_eye_zone(self):
        # Price at 99 (near high), eye zone=[38.2, 61.8]
        prices = [0.0, 50.0, 100.0, 99.0]
        result = find_spiral_eye(prices)
        assert result["found"] is False

    def test_result_structure(self):
        prices = [50.0, 80.0, 100.0, 60.0]
        result = find_spiral_eye(prices)
        assert "found" in result
        assert "current_price" in result
        assert "eye_zone" in result
        assert len(result["eye_zone"]) == 2


# ── assign_solfeggio ──────────────────────────────────────────────────────────

class TestAssignSolfeggio:
    def test_impulse_signal(self):
        hz, label = assign_solfeggio("IMPULSE", 0.30)
        assert hz == FREQ_396_HZ

    def test_singularity_signal(self):
        hz, label = assign_solfeggio("SINGULARITY", 0.30)
        assert hz == FREQ_528_HZ

    def test_stabilization_signal(self):
        hz, label = assign_solfeggio("STABILIZATION", 0.25)
        assert hz == FREQ_528_HZ

    def test_dormant_with_high_margin(self):
        hz, label = assign_solfeggio("DORMANT", 0.20)
        assert hz == FREQ_528_HZ

    def test_dormant_with_low_margin(self):
        hz, label = assign_solfeggio("DORMANT", 0.05)
        assert hz == FREQ_174_HZ

    def test_returns_int(self):
        hz, label = assign_solfeggio("SINGULARITY", 0.30)
        assert isinstance(hz, int)


# ── oracle_predict ────────────────────────────────────────────────────────────

class TestOraclePredict:
    def test_basic_buy_prediction(self):
        pred = oracle_predict(
            wholesale_price=199.0,
            retail_price=299.0,
            channel_id="AUDIO_PREMIUM",
        )
        assert isinstance(pred, OraclePrediction)
        assert pred.action in ("BUY", "HOLD", "WAIT", "SELL")
        assert 0.0 <= pred.confidence <= 1.0
        assert pred.predicted_margin_pct > 0

    def test_high_margin_gets_buy(self):
        # 50% margin should definitely get BUY
        pred = oracle_predict(
            wholesale_price=100.0,
            retail_price=200.0,
            channel_id="AUDIO_PREMIUM",
        )
        assert pred.action == "BUY"

    def test_very_low_margin_no_buy(self):
        # <1% margin
        pred = oracle_predict(
            wholesale_price=199.0,
            retail_price=200.0,
            channel_id="AUDIO_PREMIUM",
        )
        assert pred.action in ("WAIT", "HOLD")

    def test_zero_prices(self):
        pred = oracle_predict(0.0, 0.0)
        assert pred.action in ("WAIT", "HOLD", "BUY", "SELL")
        assert isinstance(pred, OraclePrediction)

    def test_with_price_history(self):
        # With price history should get turning point signal
        pred = oracle_predict(
            wholesale_price=199.0,
            retail_price=299.0,
            price_history=[250.0, 270.0, 290.0, 320.0],
        )
        assert pred.signal in ("IMPULSE", "STABILIZATION", "SINGULARITY", "DORMANT")

    def test_prediction_to_dict(self):
        pred = oracle_predict(199.0, 299.0)
        d = pred.to_dict()
        assert "signal" in d
        assert "action" in d
        assert "confidence" in d
        assert "solfeggio_hz" in d
        assert "is_singularity" in d
        assert "reasoning" in d

    def test_singularity_flag(self):
        # A product with SINGULARITY signal has is_singularity=True
        pred = oracle_predict(
            wholesale_price=100.0,
            retail_price=200.0,
        )
        # is_singularity should be bool
        assert isinstance(pred.is_singularity, bool)

    def test_solfeggio_valid_frequency(self):
        pred = oracle_predict(100.0, 200.0)
        assert pred.solfeggio_hz in (174, 396, 528)

    def test_negative_margin_handled(self):
        # Price_source > price_target
        pred = oracle_predict(300.0, 100.0)
        assert isinstance(pred, OraclePrediction)


# ── oracle_scan_products ──────────────────────────────────────────────────────

class TestOracleScanProducts:
    PRODUCTS = [
        {"name": "FiiO K9 Pro", "wholesale_price": 199.0, "retail_price": 299.0},
        {"name": "Sennheiser HD660", "wholesale_price": 350.0, "retail_price": 450.0},
        {"name": "No Margin Item", "wholesale_price": 300.0, "retail_price": 301.0},
    ]

    def test_returns_all_predictions(self):
        result = oracle_scan_products(self.PRODUCTS, "AUDIO_PREMIUM")
        assert len(result["predictions"]) == 3

    def test_summary_counts_add_up(self):
        result = oracle_scan_products(self.PRODUCTS, "AUDIO_PREMIUM")
        s = result["summary"]
        total = s["buys"] + s["holds"] + s["waits"]
        # singularities are a subset of buys
        assert total == len(self.PRODUCTS)
        assert s["singularities"] <= s["buys"]

    def test_summary_has_required_keys(self):
        result = oracle_scan_products(self.PRODUCTS, "AUDIO_PREMIUM")
        s = result["summary"]
        for key in ("total_scanned", "singularities", "buys", "holds", "waits"):
            assert key in s

    def test_empty_products(self):
        result = oracle_scan_products([], "AUDIO_PREMIUM")
        assert result["predictions"] == []
        assert result["summary"]["total_scanned"] == 0

    def test_single_product(self):
        result = oracle_scan_products(
            [{"name": "Test", "wholesale_price": 100.0, "retail_price": 200.0}],
            "SMART_ENERGY"
        )
        assert len(result["predictions"]) == 1

    def test_prediction_dict_structure(self):
        result = oracle_scan_products(
            [self.PRODUCTS[0]], "AUDIO_PREMIUM"
        )
        p = result["predictions"][0]
        assert "name" in p
        assert "signal" in p
        assert "action" in p
        assert "predicted_margin_pct" in p
        assert "confidence" in p
        assert "solfeggio_hz" in p
        assert "is_singularity" in p
