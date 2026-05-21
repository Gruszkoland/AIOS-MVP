package quantum

import (
	"testing"
)

func newOracle() *OracleNode {
	return &OracleNode{Vortex: NewVortexNode()}
}

// ── IsMaterialFlow ────────────────────────────────────────────────────────────

func TestIsMaterialFlowExactMatch(t *testing.T) {
	o := newOracle()
	if !o.IsMaterialFlow([]int{1, 4, 2, 8, 5, 7}) {
		t.Error("exact hexad should match")
	}
}

func TestIsMaterialFlowPatternInsideLonger(t *testing.T) {
	o := newOracle()
	seq := []int{0, 9, 1, 4, 2, 8, 5, 7, 3}
	if !o.IsMaterialFlow(seq) {
		t.Error("hexad embedded in longer sequence should match")
	}
}

func TestIsMaterialFlowRepeatedPattern(t *testing.T) {
	o := newOracle()
	// Two back-to-back repetitions — should still match
	seq := []int{1, 4, 2, 8, 5, 7, 1, 4, 2, 8, 5, 7}
	if !o.IsMaterialFlow(seq) {
		t.Error("repeated hexad should match")
	}
}

func TestIsMaterialFlowNoMatch(t *testing.T) {
	o := newOracle()
	seq := []int{1, 4, 2, 9, 5, 7} // 9 instead of 8
	if o.IsMaterialFlow(seq) {
		t.Error("corrupted hexad should not match")
	}
}

func TestIsMaterialFlowTooShort(t *testing.T) {
	o := newOracle()
	if o.IsMaterialFlow([]int{1, 4, 2}) {
		t.Error("sequence shorter than hexad should not match")
	}
}

func TestIsMaterialFlowEmpty(t *testing.T) {
	o := newOracle()
	if o.IsMaterialFlow([]int{}) {
		t.Error("empty sequence should not match")
	}
}

func TestIsMaterialFlowPartialAtEnd(t *testing.T) {
	o := newOracle()
	// 1,4,2,8,5 — one element short
	seq := []int{1, 4, 2, 8, 5}
	if o.IsMaterialFlow(seq) {
		t.Error("incomplete hexad should not match")
	}
}

// ── PredictTrend ──────────────────────────────────────────────────────────────

func TestPredictTrendSingularity(t *testing.T) {
	o := newOracle()
	// sum*100 → digital root 9 → StateTrue
	// Pick values whose sum * 100 has digital root 9: e.g., [0.09]→9, but we need
	// at least 3 items. [0.03, 0.03, 0.03] → sum=9 → dr=9
	history := []float64{0.03, 0.03, 0.03}
	if got := o.PredictTrend(history); got != StateTrue {
		t.Errorf("PredictTrend singularity = %v, want StateTrue", got)
	}
}

func TestPredictTrendQuantum(t *testing.T) {
	o := newOracle()
	// sum*100 → digital root 3 → StateQuantum
	// [0.01, 0.01, 0.01] → sum*100 = 3 → dr=3
	history := []float64{0.01, 0.01, 0.01}
	if got := o.PredictTrend(history); got != StateQuantum {
		t.Errorf("PredictTrend quantum = %v, want StateQuantum", got)
	}
}

func TestPredictTrendInsufficientData(t *testing.T) {
	o := newOracle()
	history := []float64{1.0, 2.0}
	if got := o.PredictTrend(history); got != StateQuantum {
		t.Errorf("PredictTrend insufficient = %v, want StateQuantum", got)
	}
}

// ── GetFrequency ──────────────────────────────────────────────────────────────

func TestGetFrequencyStateTrue(t *testing.T) {
	o := newOracle()
	if got := o.GetFrequency(StateTrue); got != 528 {
		t.Errorf("GetFrequency(StateTrue) = %d, want 528", got)
	}
}

func TestGetFrequencyStateQuantum(t *testing.T) {
	o := newOracle()
	if got := o.GetFrequency(StateQuantum); got != 417 {
		t.Errorf("GetFrequency(StateQuantum) = %d, want 417", got)
	}
}

func TestGetFrequencyStateFalse(t *testing.T) {
	o := newOracle()
	if got := o.GetFrequency(StateFalse); got != 396 {
		t.Errorf("GetFrequency(StateFalse) = %d, want 396", got)
	}
}

func TestGetFrequencyDefault(t *testing.T) {
	o := newOracle()
	if got := o.GetFrequency(DecisionState(0.99)); got != 174 {
		t.Errorf("GetFrequency(unknown) = %d, want 174", got)
	}
}
