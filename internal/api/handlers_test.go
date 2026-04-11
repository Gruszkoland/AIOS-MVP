package api

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"adrion-vortex/internal/quantum"

	"github.com/labstack/echo/v4"
)

// testHandler returns a ready-to-use Handler backed by a fresh VortexNode.
func testHandler() *Handler {
	v := quantum.NewVortexNode()
	return &Handler{
		Vortex: v,
		Oracle: &quantum.OracleNode{Vortex: v},
	}
}

func request(method, path, body string) (echo.Context, *httptest.ResponseRecorder) {
	e := echo.New()
	var req *http.Request
	if body != "" {
		req = httptest.NewRequest(method, path, strings.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
	} else {
		req = httptest.NewRequest(method, path, nil)
	}
	rec := httptest.NewRecorder()
	return e.NewContext(req, rec), rec
}

// ── HealthCheck ───────────────────────────────────────────────────────────────

func TestHealthCheckStatus200(t *testing.T) {
	h := testHandler()
	c, rec := request(http.MethodGet, "/health", "")
	if err := h.HealthCheck(c); err != nil {
		t.Fatal(err)
	}
	if rec.Code != http.StatusOK {
		t.Errorf("status = %d, want 200", rec.Code)
	}
}

func TestHealthCheckReturnsEngine(t *testing.T) {
	h := testHandler()
	c, rec := request(http.MethodGet, "/health", "")
	_ = h.HealthCheck(c)
	var body map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &body)
	if body["engine"] != "vortex-369" {
		t.Errorf("engine = %v, want vortex-369", body["engine"])
	}
}

// ── GetStatus ─────────────────────────────────────────────────────────────────

func TestGetStatusReturnsEBDI(t *testing.T) {
	h := testHandler()
	c, rec := request(http.MethodGet, "/status", "")
	_ = h.GetStatus(c)
	var body map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &body)
	ebdi, ok := body["ebdi"].(map[string]interface{})
	if !ok {
		t.Fatal("missing ebdi field in status response")
	}
	if _, ok := ebdi["dominance"]; !ok {
		t.Error("ebdi.dominance missing")
	}
}

// ── PostDecide ────────────────────────────────────────────────────────────────

func TestPostDecideValidAffirmation(t *testing.T) {
	h := testHandler()
	body := `{"asset_a":"A","asset_b":"B","price_a":100,"price_b":200}`
	c, rec := request(http.MethodPost, "/decide", body)
	if err := h.PostDecide(c); err != nil {
		t.Fatal(err)
	}
	if rec.Code != http.StatusOK {
		t.Errorf("status = %d, want 200", rec.Code)
	}
	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)
	if resp["action"] != "EXECUTE" {
		t.Errorf("action = %v, want EXECUTE", resp["action"])
	}
}

func TestPostDecideNegation(t *testing.T) {
	h := testHandler()
	// Tiny margin → REJECT
	body := `{"asset_a":"X","asset_b":"Y","price_a":100,"price_b":101}`
	c, rec := request(http.MethodPost, "/decide", body)
	_ = h.PostDecide(c)
	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)
	if resp["action"] != "REJECT" {
		t.Errorf("action = %v, want REJECT", resp["action"])
	}
}

func TestPostDecideInvalidBody(t *testing.T) {
	h := testHandler()
	c, rec := request(http.MethodPost, "/decide", "not-json{{")
	_ = h.PostDecide(c)
	if rec.Code != http.StatusBadRequest {
		t.Errorf("status = %d, want 400", rec.Code)
	}
}

func TestPostDecideResponseHasTimestamp(t *testing.T) {
	h := testHandler()
	body := `{"price_a":100,"price_b":200}`
	c, rec := request(http.MethodPost, "/decide", body)
	_ = h.PostDecide(c)
	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)
	if resp["timestamp"] == "" || resp["timestamp"] == nil {
		t.Error("response missing timestamp")
	}
}

func TestPostDecideMarginPctPresent(t *testing.T) {
	h := testHandler()
	body := `{"price_a":100,"price_b":200}`
	c, rec := request(http.MethodPost, "/decide", body)
	_ = h.PostDecide(c)
	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)
	if _, ok := resp["margin_pct"]; !ok {
		t.Error("margin_pct field missing in response")
	}
}

func TestPostDecideFrequencyPresent(t *testing.T) {
	h := testHandler()
	body := `{"price_a":100,"price_b":200}`
	c, rec := request(http.MethodPost, "/decide", body)
	_ = h.PostDecide(c)
	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)
	if _, ok := resp["frequency"]; !ok {
		t.Error("frequency field missing in response")
	}
}

// ── SentinelScan ──────────────────────────────────────────────────────────────

func TestSentinelScanCountsCorrectly(t *testing.T) {
	h := testHandler()
	body := `{"products":[
		{"sku":"A","wholesale_price":100,"retail_price":200},
		{"sku":"B","wholesale_price":100,"retail_price":101},
		{"sku":"C","wholesale_price":0,"retail_price":100}
	],"channel":"test"}`
	c, rec := request(http.MethodPost, "/sentinel/scan", body)
	_ = h.SentinelScan(c)
	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)
	if resp["scanned"].(float64) != 2 {
		t.Errorf("scanned = %v, want 2 (zero-price entry skipped)", resp["scanned"])
	}
}

func TestSentinelScanInvalidBody(t *testing.T) {
	h := testHandler()
	c, rec := request(http.MethodPost, "/sentinel/scan", "bad}")
	_ = h.SentinelScan(c)
	if rec.Code != http.StatusBadRequest {
		t.Errorf("status = %d, want 400", rec.Code)
	}
}

func TestSentinelScanReturnsChannel(t *testing.T) {
	h := testHandler()
	body := `{"products":[],"channel":"wholesale"}`
	c, rec := request(http.MethodPost, "/sentinel/scan", body)
	_ = h.SentinelScan(c)
	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)
	if resp["channel"] != "wholesale" {
		t.Errorf("channel = %v, want wholesale", resp["channel"])
	}
}

// ── GetThreats ────────────────────────────────────────────────────────────────

func TestGetThreatsReturnsVectors(t *testing.T) {
	h := testHandler()
	c, rec := request(http.MethodGet, "/sentinel/threats", "")
	_ = h.GetThreats(c)
	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)
	if resp["threat_vectors_monitored"].(float64) != 12 {
		t.Errorf("threat_vectors_monitored = %v, want 12", resp["threat_vectors_monitored"])
	}
}

func TestGetThreatsActiveAlertsZero(t *testing.T) {
	h := testHandler()
	c, rec := request(http.MethodGet, "/sentinel/threats", "")
	_ = h.GetThreats(c)
	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)
	if resp["active_alerts"].(float64) != 0 {
		t.Errorf("active_alerts = %v, want 0", resp["active_alerts"])
	}
}

// ── OraclePredict ─────────────────────────────────────────────────────────────

func TestOraclePredictValidInput(t *testing.T) {
	h := testHandler()
	body := `{"price_history":[0.01,0.01,0.01],"channel":"test"}`
	c, rec := request(http.MethodPost, "/oracle/predict", body)
	_ = h.OraclePredict(c)
	if rec.Code != http.StatusOK {
		t.Errorf("status = %d, want 200", rec.Code)
	}
}

func TestOraclePredictInvalidBody(t *testing.T) {
	h := testHandler()
	c, rec := request(http.MethodPost, "/oracle/predict", "{bad")
	_ = h.OraclePredict(c)
	if rec.Code != http.StatusBadRequest {
		t.Errorf("status = %d, want 400", rec.Code)
	}
}

func TestOraclePredictSignalField(t *testing.T) {
	h := testHandler()
	body := `{"price_history":[0.03,0.03,0.03]}`
	c, rec := request(http.MethodPost, "/oracle/predict", body)
	_ = h.OraclePredict(c)
	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)
	if resp["signal"] == nil {
		t.Error("signal field missing in oracle response")
	}
}

// ── GetThreats Dynamic Level Tests ──────────────────────────────────────────

func TestGetThreatsCriticalLevel(t *testing.T) {
	// resonance=1 → norm=1/9≈0.111 < 0.2 → critical
	h := testHandler()
	h.Vortex.Resonance = 1
	h.Vortex.Health = 0.1

	c, rec := request(http.MethodGet, "/sentinel/threats", "")
	if err := h.GetThreats(c); err != nil {
		t.Fatal(err)
	}

	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)

	threats := resp["threats"].([]interface{})
	firstThreat := threats[0].(map[string]interface{})
	if firstThreat["level"] != "critical" {
		t.Errorf("level = %v, want critical", firstThreat["level"])
	}
	if resp["active_alerts"].(float64) != 2 {
		t.Errorf("active_alerts = %v, want 2", resp["active_alerts"])
	}
}

func TestGetThreatsWarningLevel(t *testing.T) {
	// resonance=3 → norm=3/9≈0.333 < 0.4, health=0.3 < 0.4 → warning (both AND)
	h := testHandler()
	h.Vortex.Resonance = 3
	h.Vortex.Health = 0.3

	c, rec := request(http.MethodGet, "/sentinel/threats", "")
	_ = h.GetThreats(c)

	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)

	threats := resp["threats"].([]interface{})
	firstThreat := threats[0].(map[string]interface{})
	if firstThreat["level"] != "warning" {
		t.Errorf("level = %v, want warning", firstThreat["level"])
	}
	if resp["active_alerts"].(float64) != 1 {
		t.Errorf("active_alerts = %v, want 1", resp["active_alerts"])
	}
}

func TestGetThreatsElevatedLevel(t *testing.T) {
	// resonance=5 → norm=5/9≈0.556 < 0.7 → elevated (OR condition)
	// health=0.8 >= 0.7, so only resonance triggers elevated
	h := testHandler()
	h.Vortex.Resonance = 5
	h.Vortex.Health = 0.8

	c, rec := request(http.MethodGet, "/sentinel/threats", "")
	_ = h.GetThreats(c)

	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)

	threats := resp["threats"].([]interface{})
	firstThreat := threats[0].(map[string]interface{})
	if firstThreat["level"] != "elevated" {
		t.Errorf("level = %v, want elevated", firstThreat["level"])
	}
	if resp["active_alerts"].(float64) != 0 {
		t.Errorf("active_alerts = %v, want 0", resp["active_alerts"])
	}
}

func TestGetThreatsNominalLevel(t *testing.T) {
	// resonance=8 → norm=8/9≈0.889 >= 0.7, health=0.9 >= 0.7 → nominal
	h := testHandler()
	h.Vortex.Resonance = 8
	h.Vortex.Health = 0.9

	c, rec := request(http.MethodGet, "/sentinel/threats", "")
	_ = h.GetThreats(c)

	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)

	threats := resp["threats"].([]interface{})
	firstThreat := threats[0].(map[string]interface{})
	if firstThreat["level"] != "nominal" {
		t.Errorf("level = %v, want nominal", firstThreat["level"])
	}
	if resp["active_alerts"].(float64) != 0 {
		t.Errorf("active_alerts = %v, want 0", resp["active_alerts"])
	}
}

func TestGetThreatsBoundaryResonanceTwo(t *testing.T) {
	// resonance=2 → norm=2/9≈0.222 >= 0.2, NOT critical from resonance alone.
	// health=0.3 < 0.4. Since resonanceNorm < 0.4 AND health < 0.4 → warning.
	h := testHandler()
	h.Vortex.Resonance = 2
	h.Vortex.Health = 0.3

	c, rec := request(http.MethodGet, "/sentinel/threats", "")
	_ = h.GetThreats(c)

	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)

	threats := resp["threats"].([]interface{})
	firstThreat := threats[0].(map[string]interface{})
	if firstThreat["level"] != "warning" {
		t.Errorf("level = %v, want warning (boundary: resonance=2 norm≈0.222, health=0.3)", firstThreat["level"])
	}
}

func TestGetThreatsBoundaryResonanceSeven(t *testing.T) {
	// resonance=7 → norm=7/9≈0.778 >= 0.7, health=0.75 >= 0.7 → nominal
	h := testHandler()
	h.Vortex.Resonance = 7
	h.Vortex.Health = 0.75

	c, rec := request(http.MethodGet, "/sentinel/threats", "")
	_ = h.GetThreats(c)

	var resp map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &resp)

	threats := resp["threats"].([]interface{})
	firstThreat := threats[0].(map[string]interface{})
	if firstThreat["level"] != "nominal" {
		t.Errorf("level = %v, want nominal (boundary: resonance=7 norm≈0.778, health=0.75)", firstThreat["level"])
	}
	if resp["active_alerts"].(float64) != 0 {
		t.Errorf("active_alerts = %v, want 0 at nominal", resp["active_alerts"])
	}
}
