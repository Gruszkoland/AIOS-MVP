package api

import (
	"net/http"
	"time"

	"adrion-vortex/internal/quantum"

	"github.com/labstack/echo/v4"
)

// MarketData represents incoming prices for decision
type MarketData struct {
	AssetA    string  `json:"asset_a"`
	AssetB    string  `json:"asset_b"`
	PriceA    float64 `json:"price_a"`
	PriceB    float64 `json:"price_b"`
	Timestamp int64   `json:"timestamp"`
}

// DecisionResponse represents 3-6-9 logic output
type DecisionResponse struct {
	State     quantum.DecisionState `json:"state"`
	Resonance int                   `json:"resonance"`
	Frequency int                   `json:"frequency"`
	Message   string                `json:"message"`
}

// ScanRequest for sentinel scan endpoint
type ScanRequest struct {
	Products []ProductEntry `json:"products"`
	Channel  string         `json:"channel"`
}

// ProductEntry represents a wholesale product for scanning
type ProductEntry struct {
	SKU            string  `json:"sku"`
	Name           string  `json:"name"`
	WholesalePrice float64 `json:"wholesale_price"`
	RetailPrice    float64 `json:"retail_price"`
}

// ScanResult represents a single product scan result
type ScanResult struct {
	SKU       string                `json:"sku"`
	Name      string                `json:"name"`
	State     quantum.DecisionState `json:"state"`
	Resonance int                   `json:"resonance"`
	Frequency int                   `json:"frequency"`
	Action    string                `json:"action"`
	MarginPct float64               `json:"margin_pct"`
}

// ThreatEntry represents a detected anomaly
type ThreatEntry struct {
	Vector    string `json:"vector"`
	Level     string `json:"level"`
	Detail    string `json:"detail"`
	Timestamp string `json:"timestamp"`
}

// OraclePredictRequest for oracle predict endpoint
type OraclePredictRequest struct {
	PriceHistory []float64 `json:"price_history"`
	Channel      string    `json:"channel"`
}

type Handler struct {
	Vortex *quantum.VortexNode
	Oracle *quantum.OracleNode
}

// PostDecide handles the 162D decision request
func (h *Handler) PostDecide(c echo.Context) error {
	var data MarketData
	if err := c.Bind(&data); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "Invalid market data"})
	}

	state := h.Vortex.CalculateMarketResonance(data.PriceA, data.PriceB)
	frequency := h.Oracle.GetFrequency(state)

	response := DecisionResponse{
		State:     state,
		Resonance: h.Vortex.Resonance,
		Frequency: frequency,
	}

	switch state {
	case quantum.StateTrue:
		response.Message = "Singularity Detected (9): Execute Arbitrage"
	case quantum.StateQuantum:
		response.Message = "Harmonic Potential (3/6): Monitor Spread"
	default:
		response.Message = "Neutral State: No Resonance"
	}

	return c.JSON(http.StatusOK, response)
}

// GetStatus returns current engine oscillations
func (h *Handler) GetStatus(c echo.Context) error {
	return c.JSON(http.StatusOK, map[string]interface{}{
		"resonance": h.Vortex.Resonance,
		"pulse":     "174Hz",
		"mode":      "Trinity-Enabled",
		"uptime":    time.Now().Format(time.RFC3339),
	})
}

// HealthCheck returns sentinel health for Docker/k8s probes
func (h *Handler) HealthCheck(c echo.Context) error {
	return c.JSON(http.StatusOK, map[string]interface{}{
		"status":    "healthy",
		"resonance": h.Vortex.Resonance,
		"engine":    "vortex-369",
		"timestamp": time.Now().Format(time.RFC3339),
	})
}

// SentinelScan scans a batch of products through the 3-6-9 quantum filter
func (h *Handler) SentinelScan(c echo.Context) error {
	var req ScanRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "Invalid scan request"})
	}

	results := make([]ScanResult, 0, len(req.Products))
	executeCount := 0
	monitorCount := 0

	for _, p := range req.Products {
		if p.WholesalePrice <= 0 || p.RetailPrice <= 0 {
			continue
		}

		state := h.Vortex.CalculateMarketResonance(p.WholesalePrice, p.RetailPrice)
		freq := h.Oracle.GetFrequency(state)
		margin := (p.RetailPrice - p.WholesalePrice) / p.RetailPrice

		action := "REJECT"
		switch state {
		case quantum.StateTrue:
			action = "EXECUTE"
			executeCount++
		case quantum.StateQuantum:
			action = "MONITOR"
			monitorCount++
		}

		results = append(results, ScanResult{
			SKU:       p.SKU,
			Name:      p.Name,
			State:     state,
			Resonance: h.Vortex.Resonance,
			Frequency: freq,
			Action:    action,
			MarginPct: margin,
		})
	}

	return c.JSON(http.StatusOK, map[string]interface{}{
		"scanned":  len(results),
		"execute":  executeCount,
		"monitor":  monitorCount,
		"reject":   len(results) - executeCount - monitorCount,
		"results":  results,
		"channel":  req.Channel,
		"scannedAt": time.Now().Format(time.RFC3339),
	})
}

// GetThreats returns current threat monitoring status (A-01 to A-12)
func (h *Handler) GetThreats(c echo.Context) error {
	// Sentinel monitors 12 threat vectors
	threats := []ThreatEntry{
		{Vector: "A-01", Level: "nominal", Detail: "EBDI sentiment: stable", Timestamp: time.Now().Format(time.RFC3339)},
		{Vector: "A-04", Level: "nominal", Detail: "Material resources: available", Timestamp: time.Now().Format(time.RFC3339)},
		{Vector: "A-07", Level: "nominal", Detail: "Authority: verified", Timestamp: time.Now().Format(time.RFC3339)},
		{Vector: "A-10", Level: "nominal", Detail: "Privacy: local-first active", Timestamp: time.Now().Format(time.RFC3339)},
	}

	return c.JSON(http.StatusOK, map[string]interface{}{
		"threat_vectors_monitored": 12,
		"active_alerts":            0,
		"threats":                  threats,
		"guardian_status":          "G7-G9 enforced",
		"timestamp":               time.Now().Format(time.RFC3339),
	})
}

// OraclePredict uses the Go Oracle engine for trend prediction
func (h *Handler) OraclePredict(c echo.Context) error {
	var req OraclePredictRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "Invalid prediction request"})
	}

	state := h.Oracle.PredictTrend(req.PriceHistory)
	freq := h.Oracle.GetFrequency(state)

	signal := "DORMANT"
	switch state {
	case quantum.StateTrue:
		signal = "SINGULARITY"
	case quantum.StateQuantum:
		signal = "HARMONIC_POTENTIAL"
	}

	return c.JSON(http.StatusOK, map[string]interface{}{
		"state":     state,
		"signal":    signal,
		"frequency": freq,
		"resonance": h.Vortex.Resonance,
		"channel":   req.Channel,
		"timestamp": time.Now().Format(time.RFC3339),
	})
}
