package quantum

import (
	"time"
)

// Perspective weights (Trinity)
// Material: 0.33, Intellectual: 0.33, Essential: 0.34
const (
	MaxSingularity = 9
	Pulse174Hz     = 174 * time.Millisecond
)

// DecisionState representing 0, 1, 1/2 logic
type DecisionState float64

const (
	StateFalse   DecisionState = 0.0
	StateTrue    DecisionState = 1.0
	StateQuantum DecisionState = 0.5
)

// Progi decyzyjne z Python
const (
	MarginThresholdAffirm        = 0.15
	MarginThresholdSuperposition = 0.08
)

// VortexNode implements 3-6-9 Logic Engine
type VortexNode struct {
	LastValue float64
	Resonance int
	Pulse     *time.Ticker
}

// DigitalRoot calculates the 3-6-9 reduction
func DigitalRoot(n int) int {
	if n == 0 {
		return 0
	}
	res := n % 9
	if res == 0 {
		return 9
	}
	return res
}

// CalculateMarketResonanceFull applies 162D decision space mapping with 15% threshold support
func (v *VortexNode) CalculateMarketResonanceFull(priceWholesale, priceRetail float64) (DecisionState, float64, bool, bool) {
	if priceWholesale <= 0 || priceRetail <= 0 || priceRetail <= priceWholesale {
		return StateFalse, 0.0, false, false
	}

	diff := priceRetail - priceWholesale
	marginPct := diff / priceRetail
	root := DigitalRoot(int(diff))

	v.Resonance = root
	is369 := (root == 3 || root == 6 || root == 9)
	vortexPass := marginPct >= 0.05 // Simplified filter from analizer.py

	// ── Stan 1: Afirmacja ──
	if marginPct >= MarginThresholdAffirm {
		return StateTrue, marginPct, is369, vortexPass
	}

	// ── Stan ½: Superpozycja ──
	if marginPct >= MarginThresholdSuperposition {
		if is369 {
			return StateTrue, marginPct, true, vortexPass
		}
		return StateQuantum, marginPct, false, vortexPass
	}

	// ── Stan 0: Negacja ──
	return StateFalse, marginPct, is369, vortexPass
}

// CalculateMarketResonance - Legacy support
func (v *VortexNode) CalculateMarketResonance(priceA, priceB float64) DecisionState {
	state, _, _, _ := v.CalculateMarketResonanceFull(priceA, priceB)
	return state
}

// StartOscillation initiates the 174Hz market scanning
func (v *VortexNode) StartOscillation(callback func(int)) {
	v.Pulse = time.NewTicker(Pulse174Hz)
	go func() {
		for range v.Pulse.C {
			callback(v.Resonance)
		}
	}()
}
