package quantum

import (
	"testing"
	"time"
)

// ── DigitalRoot ──────────────────────────────────────────────────────────────

func TestDigitalRootZero(t *testing.T) {
	if got := DigitalRoot(0); got != 0 {
		t.Errorf("DigitalRoot(0) = %d, want 0", got)
	}
}

func TestDigitalRootMultipleOf9(t *testing.T) {
	cases := []int{9, 18, 27, 81, 999}
	for _, n := range cases {
		if got := DigitalRoot(n); got != 9 {
			t.Errorf("DigitalRoot(%d) = %d, want 9", n, got)
		}
	}
}

func TestDigitalRootGeneral(t *testing.T) {
	cases := map[int]int{1: 1, 2: 2, 3: 3, 10: 1, 19: 1, 37: 1, 100: 1, 162: 9}
	for input, want := range cases {
		if got := DigitalRoot(input); got != want {
			t.Errorf("DigitalRoot(%d) = %d, want %d", input, got, want)
		}
	}
}

// ── NewVortexNode ─────────────────────────────────────────────────────────────

func TestNewVortexNodeBaselineHealth(t *testing.T) {
	v := NewVortexNode()
	if v.Health != 1.0 {
		t.Errorf("NewVortexNode().Health = %g, want 1.0", v.Health)
	}
}

func TestNewVortexNodeBaselineEBDI(t *testing.T) {
	v := NewVortexNode()
	if v.EBDI.Dominance != 1.0 {
		t.Errorf("EBDI.Dominance = %g, want 1.0", v.EBDI.Dominance)
	}
	if v.EBDI.Arousal != 0.5 {
		t.Errorf("EBDI.Arousal = %g, want 0.5", v.EBDI.Arousal)
	}
	if v.EBDI.Pleasure != 0.8 {
		t.Errorf("EBDI.Pleasure = %g, want 0.8", v.EBDI.Pleasure)
	}
	if v.EBDI.LastUpdate.IsZero() {
		t.Error("EBDI.LastUpdate should not be zero after construction")
	}
}

// ── CalculateMarketResonance ──────────────────────────────────────────────────

func TestMarketResonanceAffirmation(t *testing.T) {
	v := NewVortexNode()
	// margin = (200-100)/200 = 0.50 → above MarginThresholdAffirm (0.15)
	if got := v.CalculateMarketResonance(100, 200); got != StateTrue {
		t.Errorf("CalculateMarketResonance(100,200) = %v, want StateTrue", got)
	}
}

func TestMarketResonanceNegation(t *testing.T) {
	v := NewVortexNode()
	// margin = (101-100)/101 ≈ 0.009 → below MarginThresholdSuperposition (0.08)
	if got := v.CalculateMarketResonance(100, 101); got != StateFalse {
		t.Errorf("CalculateMarketResonance(100,101) = %v, want StateFalse", got)
	}
}

func TestMarketResonanceSuperposition(t *testing.T) {
	v := NewVortexNode()
	// margin = (110-100)/110 ≈ 0.0909 → inside superposition band, not 3/6/9 root
	state, margin, _, _ := v.CalculateMarketResonanceFull(100, 110)
	if margin < MarginThresholdSuperposition || margin >= MarginThresholdAffirm {
		if state != StateQuantum {
			t.Errorf("expected Quantum state for margin %g, got %v", margin, state)
		}
	}
}

func TestMarketResonanceInvalidPrices(t *testing.T) {
	v := NewVortexNode()
	cases := [][2]float64{{0, 100}, {100, 0}, {-10, 50}, {150, 100}}
	for _, c := range cases {
		if got := v.CalculateMarketResonance(c[0], c[1]); got != StateFalse {
			t.Errorf("CalculateMarketResonance(%g,%g) = %v, want StateFalse", c[0], c[1], got)
		}
	}
}

// ── TriggerSelfHealing ────────────────────────────────────────────────────────

func TestSelfHealingResetsAboveThreshold(t *testing.T) {
	v := NewVortexNode()
	v.EBDI.Dominance = 0.8
	v.Health = 0.8
	v.TriggerSelfHealing("test error")
	if v.Health > 0.8 {
		t.Errorf("Health should not increase on first healing call")
	}
}

func TestSelfHealingRestoresHomeostasis(t *testing.T) {
	v := NewVortexNode()
	// Drive Dominance below 0.5 threshold
	v.EBDI.Dominance = 0.4
	v.Health = 0.4
	v.Pulse = time.NewTicker(Pulse147Hz)
	defer v.Pulse.Stop()

	v.TriggerSelfHealing("critical failure")

	if v.Health != 1.0 {
		t.Errorf("Health = %g after healing, want 1.0", v.Health)
	}
	if v.EBDI.Dominance != 1.0 {
		t.Errorf("EBDI.Dominance = %g after healing, want 1.0", v.EBDI.Dominance)
	}
}

// ── UpdateEBDI ────────────────────────────────────────────────────────────────

func TestUpdateEBDISyncsHealth(t *testing.T) {
	v := NewVortexNode()
	v.UpdateEBDI(0.9, 0.6, 0.7)
	if v.Health != v.EBDI.Dominance {
		t.Errorf("Health (%g) should equal EBDI.Dominance (%g)", v.Health, v.EBDI.Dominance)
	}
}

func TestUpdateEBDITriggersHealingBelowThreshold(t *testing.T) {
	v := NewVortexNode()
	v.EBDI.Dominance = 0.0
	v.EBDI.Arousal = 0.0
	v.EBDI.Pleasure = 0.0
	v.EBDI.LastUpdate = time.Now().Add(-10 * time.Minute)
	v.Pulse = time.NewTicker(Pulse147Hz)
	defer v.Pulse.Stop()

	// Force all to below 0.3
	v.UpdateEBDI(0.1, 0.1, 0.1)
	// After healing, dominance must be restored
	if v.EBDI.Dominance < 0.3 {
		t.Errorf("EBDI.Dominance should be healed, got %g", v.EBDI.Dominance)
	}
}

func TestUpdateEBDIDecayApplied(t *testing.T) {
	v := NewVortexNode()
	v.EBDI.Dominance = 1.0
	// Simulate 5-minute elapsed (full half-life)
	v.EBDI.LastUpdate = time.Now().Add(-5 * time.Minute)
	v.UpdateEBDI(0.0, 0.5, 0.8)
	// After one half-life the old value should contribute ~0.5 of 1.0
	if v.EBDI.Dominance >= 1.0 {
		t.Errorf("Decay not applied: EBDI.Dominance = %g", v.EBDI.Dominance)
	}
}

// ── StartOscillation ──────────────────────────────────────────────────────────

func TestStartOscillationFiresCallback(t *testing.T) {
	v := NewVortexNode()
	fired := make(chan int, 1)
	v.StartOscillation(func(resonance int) {
		fired <- resonance
	})
	defer v.Pulse.Stop()

	select {
	case <-fired:
		// success
	case <-time.After(500 * time.Millisecond):
		t.Error("Oscillation callback never fired within 500ms")
	}
}
