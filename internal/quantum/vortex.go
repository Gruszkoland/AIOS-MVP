package quantum

import (
	"math"
	"sync"
	"time"
)

// Perspective weights (Trinity)
// 162-Dimensional Optimization (3 Perspektywy x 6 Agentów x 9 Praw)
const (
	MaxSingularity = 9
	Pulse147Hz     = 147 * time.Millisecond // Zoptymalizowano (174 -> 147 dla wyższej czułości GoT)
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

// EBDIState tracks the Pleasure-Arousal-Dominance vector for EBDI homeostasis.
// Values are in the range [0.0, 1.0] and decay exponentially (half-life 5 min).
type EBDIState struct {
	Dominance  float64   // authority / control dimension
	Arousal    float64   // activation / energy dimension
	Pleasure   float64   // satisfaction / reward dimension
	LastUpdate time.Time // timestamp of last explicit update (for decay)
}

// VortexNode implements 3-6-9 Logic Engine
type VortexNode struct {
	mu        sync.RWMutex // protects all mutable fields below
	LastValue float64
	Resonance int
	Pulse     *time.Ticker
	Health    float64   // 0.0 - 1.0 (backward-compat alias for EBDI.Dominance)
	EBDI      EBDIState // full PAD vector
}

// TriggerSelfHealing (HEALER v3.0)
// Automatyczna pętla naprawcza aktywowana przy spadku Dominance lub Resonance
func (v *VortexNode) TriggerSelfHealing(errorMsg string) {
	v.mu.Lock()
	defer v.mu.Unlock()
	v.triggerSelfHealingLocked(errorMsg)
}

// triggerSelfHealingLocked — internal helper, must be called with mu held.
func (v *VortexNode) triggerSelfHealingLocked(errorMsg string) {
	v.EBDI.Dominance -= 0.1
	v.Health = v.EBDI.Dominance
	if v.EBDI.Dominance < 0.5 {
		if v.Pulse != nil {
			v.Pulse.Reset(Pulse147Hz)
		}
		v.EBDI.Dominance = 1.0
		v.EBDI.Arousal = 0.5
		v.EBDI.Pleasure = 0.8
		v.EBDI.LastUpdate = time.Now()
		v.Health = 1.0
	}
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

	v.mu.Lock()
	v.Resonance = root
	v.mu.Unlock()

	is369 := (root == 3 || root == 6 || root == 9)
	vortexPass := marginPct >= 0.05

	if marginPct >= MarginThresholdAffirm {
		return StateTrue, marginPct, is369, vortexPass
	}
	if marginPct >= MarginThresholdSuperposition {
		if is369 {
			return StateTrue, marginPct, true, vortexPass
		}
		return StateQuantum, marginPct, false, vortexPass
	}
	return StateFalse, marginPct, is369, vortexPass
}

// CalculateMarketResonance - Legacy support
func (v *VortexNode) CalculateMarketResonance(priceA, priceB float64) DecisionState {
	state, _, _, _ := v.CalculateMarketResonanceFull(priceA, priceB)
	return state
}

// StartOscillation initiates the 147Hz market scanning
func (v *VortexNode) StartOscillation(callback func(int)) {
	v.Pulse = time.NewTicker(Pulse147Hz)
	go func() {
		for range v.Pulse.C {
			callback(v.GetResonance())
		}
	}()
}

// UpdateEBDI applies new PAD measurements with exponential decay (half-life 5 min).
// Automatically triggers self-healing if any dimension falls below 0.3.
func (v *VortexNode) UpdateEBDI(dominance, arousal, pleasure float64) {
	now := time.Now()
	v.mu.Lock()
	defer v.mu.Unlock()

	elapsed := now.Sub(v.EBDI.LastUpdate).Seconds()
	if elapsed <= 0 {
		elapsed = 0
	}
	const halfLife = 300.0
	decay := math.Exp(-math.Log(2) / halfLife * elapsed)

	v.EBDI.Dominance = v.EBDI.Dominance*decay + dominance*(1-decay)
	v.EBDI.Arousal = v.EBDI.Arousal*decay + arousal*(1-decay)
	v.EBDI.Pleasure = v.EBDI.Pleasure*decay + pleasure*(1-decay)
	v.EBDI.LastUpdate = now
	v.Health = v.EBDI.Dominance

	if v.EBDI.Dominance < 0.3 || v.EBDI.Arousal < 0.3 || v.EBDI.Pleasure < 0.3 {
		v.triggerSelfHealingLocked("EBDI below homeostasis threshold")
	}
}

// GetResonance returns the current resonance value safely.
func (v *VortexNode) GetResonance() int {
	v.mu.RLock()
	defer v.mu.RUnlock()
	return v.Resonance
}

// GetHealth returns the current health value safely.
func (v *VortexNode) GetHealth() float64 {
	v.mu.RLock()
	defer v.mu.RUnlock()
	return v.Health
}

// GetEBDI returns a snapshot copy of the current EBDI state safely.
func (v *VortexNode) GetEBDI() EBDIState {
	v.mu.RLock()
	defer v.mu.RUnlock()
	return v.EBDI
}

// NewVortexNode creates a VortexNode with baseline EBDI homeostasis values.
func NewVortexNode() *VortexNode {
	return &VortexNode{
		Health: 1.0,
		EBDI: EBDIState{
			Dominance:  1.0,
			Arousal:    0.5,
			Pleasure:   0.8,
			LastUpdate: time.Now(),
		},
	}
}
