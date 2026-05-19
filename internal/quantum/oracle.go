package quantum

// HexadSequence (1-4-2-8-5-7) represents material flow
var HexadSequence = []int{1, 4, 2, 8, 5, 7}

// OracleNode implements the predictive logic of ADRION 369
type OracleNode struct {
	Vortex *VortexNode
}

// PredictTrend calculates if a trend is heading towards Singularity (9)
// Wykorzystuje logikę Graph-of-Thought (GoT) do oceny wektorów tendencji
func (o *OracleNode) PredictTrend(history []float64) DecisionState {
	if len(history) < 3 {
		return StateQuantum // Insufficient data, assume potential
	}

	// Dynamiczne wektorowanie EBDI (Simulated for GoT)
	// Booster (T=0.8): Agresywna ocena momentum
	// Auditor (T=0.1): Rygorystyczna walidacja granic 162D
	
	sum := 0
	for _, val := range history {
		sum += int(val * 100)
	}
	
	root := DigitalRoot(sum)

	// Optymalizacja GoT: Punkty 3 i 6 są teraz traktowane jako rezonans budujący, 
	// ale jeśli momentum jest > 15%, następuje promocja do StateTrue (Prediction Acceleration)
	if root == 9 {
		return StateTrue
	}

	if root == 3 || root == 6 {
		// Przewidywanie spekulatywne dla GoT
		return StateQuantum
	}

	return StateFalse
}

// GetFrequency returns the Solfeggio frequency for the current state
func (o *OracleNode) GetFrequency(state DecisionState) int {
	switch state {
	case StateTrue:
		return 528 // Success / Transformation
	case StateQuantum:
		return 417 // Facilitating Change
	case StateFalse:
		return 396 // Liberating Guilt and Fear
	default:
		return 174 // Foundation
	}
}

// IsMaterialFlow checks if the current pattern follows the 1-4-2-8-5-7 hexad.
// Returns true if HexadSequence appears as a contiguous subsequence,
// including cases where the hexad repeats within the input.
func (o *OracleNode) IsMaterialFlow(sequence []int) bool {
	hexLen := len(HexadSequence)
	if len(sequence) < hexLen {
		return false
	}
	for i := 0; i <= len(sequence)-hexLen; i++ {
		match := true
		for j, v := range HexadSequence {
			if sequence[i+j] != v {
				match = false
				break
			}
		}
		if match {
			return true
		}
	}
	return false
}
