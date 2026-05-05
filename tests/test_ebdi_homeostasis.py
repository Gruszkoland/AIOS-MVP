"""Tests for EBDI Homeostatic Decay Service."""

import math
import time
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from uap.backend.ebdi_homeostasis import (
    EBDIHomeostaticService,
    EBDI_BASELINE,
    EBDI_HALF_LIFE_SECONDS,
)


def _make_store():
    """Create a test telemetry store with known values."""
    return {
        "TestAgent": {"pleasure": 0.8, "arousal": 0.9, "dominance": 0.9},
        "CalmAgent": {"pleasure": 0.0, "arousal": 0.0, "dominance": 0.5},
    }


class TestDecayMath:
    """Verify exponential decay formula correctness."""

    def test_one_half_life_decays_50_percent(self):
        store = _make_store()
        svc = EBDIHomeostaticService(store, half_life=60.0, tick_interval=1.0)

        # Apply exactly one half-life of decay
        svc._apply_decay(60.0)

        # TestAgent pleasure: baseline=0.0, start=0.8
        # After 1 half-life: 0.0 + (0.8 - 0.0) * 0.5 = 0.4
        assert abs(store["TestAgent"]["pleasure"] - 0.4) < 0.01

        # TestAgent arousal: baseline=0.0, start=0.9
        # After 1 half-life: 0.0 + (0.9 - 0.0) * 0.5 = 0.45
        assert abs(store["TestAgent"]["arousal"] - 0.45) < 0.01

        # TestAgent dominance: baseline=0.5, start=0.9
        # After 1 half-life: 0.5 + (0.9 - 0.5) * 0.5 = 0.7
        assert abs(store["TestAgent"]["dominance"] - 0.7) < 0.01

    def test_at_baseline_no_change(self):
        store = _make_store()
        svc = EBDIHomeostaticService(store, half_life=60.0, tick_interval=1.0)
        svc._apply_decay(60.0)

        # CalmAgent is already at baseline — should stay there
        assert abs(store["CalmAgent"]["pleasure"] - 0.0) < 0.001
        assert abs(store["CalmAgent"]["arousal"] - 0.0) < 0.001
        assert abs(store["CalmAgent"]["dominance"] - 0.5) < 0.001

    def test_two_half_lives_decay_75_percent(self):
        store = {"A": {"pleasure": 1.0, "arousal": 0.0, "dominance": 0.5}}
        svc = EBDIHomeostaticService(store, half_life=60.0, tick_interval=1.0)

        svc._apply_decay(120.0)  # 2 half-lives

        # pleasure: 0.0 + (1.0 - 0.0) * 0.25 = 0.25
        assert abs(store["A"]["pleasure"] - 0.25) < 0.01

    def test_values_stay_clamped(self):
        store = {"A": {"pleasure": -0.5, "arousal": 2.0, "dominance": 0.5}}
        svc = EBDIHomeostaticService(store, half_life=60.0, tick_interval=1.0)
        svc._apply_decay(10.0)

        assert store["A"]["pleasure"] >= 0.0
        assert store["A"]["arousal"] <= 1.0


class TestServiceLifecycle:
    """Verify start/stop and background thread behavior."""

    def test_start_stop(self):
        store = _make_store()
        svc = EBDIHomeostaticService(store, half_life=60.0, tick_interval=0.1)
        svc.start()
        assert svc.is_running
        svc.stop()
        assert not svc.is_running

    def test_idempotent_start(self):
        store = _make_store()
        svc = EBDIHomeostaticService(store, half_life=60.0, tick_interval=0.1)
        svc.start()
        svc.start()  # Should not create a second thread
        assert svc.is_running
        svc.stop()

    def test_decay_happens_over_real_time(self):
        store = {"A": {"pleasure": 1.0, "arousal": 0.0, "dominance": 0.5}}
        svc = EBDIHomeostaticService(store, half_life=0.5, tick_interval=0.05)
        svc.start()
        time.sleep(0.6)  # ~1 half-life
        svc.stop()

        # pleasure should have decayed significantly toward 0.0
        assert store["A"]["pleasure"] < 0.7
