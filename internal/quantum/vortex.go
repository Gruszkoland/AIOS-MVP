package quantum

import (
	"math"
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

// VortexNode implements 3-6-9 Logic Engine
type VortexNode struct {
	LastValue  float64
	Resonance  int
	Pulse      *time.Ticker
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

// CalculateMarketResonance applies 162D decision space mapping
func (v *VortexNode) CalculateMarketResonance(priceA, priceB float64) DecisionState {
	diff := math.Abs(priceA - priceB)
	// Scale to integer for Digital Root
	scaledDiff := int(diff * 1000000)
	root := DigitalRoot(scaledDiff)

	v.Resonance = root

	// Digital Root 9 represents the Singularity (Maximum Arbitrage)
	if root == 9 {
		return StateTrue
	}
	// 3 and 6 represent harmonic potential (1/2 logic)
	if root == 3 || root == 6 {
		return StateQuantum
	}

	return StateFalse
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
