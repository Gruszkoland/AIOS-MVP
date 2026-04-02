"""
ADRION 369 — Runtime Connector Tests
Tests: Ollama health, oracle/quantum live calls, api reachability
Run with: pytest tests/test_runtime_connectors.py -v -m runtime
"""

import os
import time
import pytest
import requests

OLLAMA_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:5000")
VORTEX_API = os.getenv("VORTEX_API", "http://localhost:1740")
ARBITRAGE_API_BASE = os.getenv("ARBITRAGE_API_BASE", "http://127.0.0.1:8001")

# ── Markers ──────────────────────────────────────────────────────────────────
# These tests are skipped unless RUNTIME_TESTS=1 env var is set
# Or run with: pytest -m runtime

pytestmark = pytest.mark.runtime


def _service_up(url: str, timeout: int = 2) -> bool:
    """Return True if service responds with 2xx or 4xx (not connection error)."""
    try:
        resp = requests.get(url, timeout=timeout)
        return resp.status_code < 500
    except Exception:
        return False


def _quantum_endpoint_up(base_url: str, timeout: int = 2) -> bool:
    """Return True only if quantum POST endpoint is implemented by the running API."""
    payload = {
        "price_source": 100.0,
        "price_target": 120.0,
        "channel_id": "AUDIO_PREMIUM",
    }
    try:
        resp = requests.post(
            f"{base_url}/api/arbitrage/quantum/decide",
            json=payload,
            timeout=timeout,
        )
        return resp.status_code in (200, 429, 400)
    except Exception:
        return False


# ── Ollama Connector ──────────────────────────────────────────────────────────


@pytest.mark.skipif(not _service_up(f"{OLLAMA_BASE}/api/tags"), reason="Ollama not running")
class TestOllamaConnector:
    def test_ollama_health(self):
        """Ollama /api/tags responds with 200."""
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

    def test_ollama_models_list(self):
        """Ollama returns a list of models (can be empty)."""
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        data = resp.json()
        assert "models" in data, "Response must have 'models' key"
        assert isinstance(data["models"], list)

    def test_ollama_model_loaded(self):
        """Configured model is available (skip if no models yet downloaded)."""
        model_name = os.getenv("OLLAMA_MODEL", "deepseek-coder-v2:lite")
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        models = resp.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        if not models:
            pytest.skip(f"No models yet downloaded; pull '{model_name}' to proceed")
        # Some local environments override OLLAMA_MODEL globally (e.g. gemma3:4b).
        # If at least one model is present and service is healthy, treat it as runtime-ready.
        if not any(model_name in name for name in model_names):
            pytest.skip(
                f"Configured model '{model_name}' is not downloaded; available: {model_names}"
            )


# ── Oracle + Quantum Fallback (no external services needed) ──────────────────


class TestOracleFallbackConnector:
    def test_oracle_basic_prediction(self):
        """oracle_predict returns valid OraclePrediction with fallback logic."""
        from arbitrage.oracle import oracle_predict
        result = oracle_predict(
            wholesale_price=100.0,
            retail_price=130.0,
            price_history=[95.0, 97.0, 100.0, 102.0, 104.0, 105.0],
        )
        assert result is not None
        assert result.action in ("BUY", "HOLD", "WAIT"), f"Unexpected action: {result.action}"
        assert isinstance(result.predicted_margin_pct, float)
        assert 0.0 <= result.confidence <= 1.0, f"Confidence out of range: {result.confidence}"

    def test_oracle_scan_products(self):
        """oracle_scan_products returns dict with predictions list and summary."""
        from arbitrage.oracle import oracle_scan_products
        products = [
            {"name": "TestProduct A", "wholesale_price": 80.0, "retail_price": 120.0},
            {"name": "TestProduct B", "wholesale_price": 50.0, "retail_price": 60.0},
        ]
        results = oracle_scan_products(products)
        assert isinstance(results, dict), f"Expected dict, got {type(results)}"
        assert "predictions" in results, "Result must have 'predictions' key"
        assert "summary" in results, "Result must have 'summary' key"
        assert len(results["predictions"]) == 2


class TestQuantumFallbackConnector:
    def test_quantum_decide_basic(self):
        """quantum_decide returns QuantumDecision with fallback (no Sentinel needed)."""
        os.environ["USE_SENTINEL_QUANTUM"] = "0"
        from arbitrage.quantum import quantum_decide
        result = quantum_decide(price_source=100.0, price_target=115.0)
        assert result is not None
        assert result.state in (0.0, 0.5, 1.0), f"State must be 0/0.5/1, got {result.state}"
        assert result.margin_pct != 0.0, "margin_pct should not be 0 in fallback mode"

    def test_quantum_affirmation_high_margin(self):
        """High margin (>15%) results in affirmation state (1.0)."""
        os.environ["USE_SENTINEL_QUANTUM"] = "0"
        from arbitrage.quantum import quantum_decide
        result = quantum_decide(price_source=80.0, price_target=100.0)
        assert result.state == 1.0, f"Expected affirmation (1.0) for 25% margin, got {result.state}"

    def test_quantum_negation_low_margin(self):
        """Low/negative margin results in negation state (0.0)."""
        os.environ["USE_SENTINEL_QUANTUM"] = "0"
        from arbitrage.quantum import quantum_decide
        result = quantum_decide(price_source=100.0, price_target=100.5)
        assert result.state == 0.0, f"Expected negation (0.0) for low margin, got {result.state}"

    def test_quantum_superposition_mid_margin(self):
        """Mid-range margin (8-15%) results in superposition state (0.5)."""
        os.environ["USE_SENTINEL_QUANTUM"] = "0"
        from arbitrage.quantum import quantum_decide
        result = quantum_decide(price_source=100.0, price_target=111.0)
        assert result.state == 0.5, f"Expected superposition (0.5) for ~11% margin, got {result.state}"


# ── Arbitrage API Runtime (rate limiter verification) ───────────────────────


@pytest.mark.skipif(
    not _quantum_endpoint_up(ARBITRAGE_API_BASE),
    reason="Arbitrage quantum endpoint not running on ARBITRAGE_API_BASE",
)
class TestArbitrageApiRuntime:
    def test_quantum_decide_endpoint_accepts_post(self):
        """Quantum endpoint should respond with 200 or 429 for valid payload."""
        payload = {
            "price_source": 100.0,
            "price_target": 120.0,
            "channel_id": "AUDIO_PREMIUM",
        }
        resp = requests.post(
            f"{ARBITRAGE_API_BASE}/api/arbitrage/quantum/decide",
            json=payload,
            timeout=3,
        )
        assert resp.status_code in (200, 429), (
            f"Expected 200/429, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_quantum_decide_rate_limit_trips_under_burst(self):
        """Burst requests should eventually receive HTTP 429."""
        configured_limit = int(os.getenv("QUANTUM_RATE_LIMIT_MAX", "30"))
        attempts = min(max(configured_limit + 10, 20), 80)
        payload = {
            "price_source": 100.0,
            "price_target": 120.0,
            "channel_id": "AUDIO_PREMIUM",
        }

        status_codes = []
        connection_errors = 0
        for _ in range(attempts):
            success = False
            for _retry in range(2):
                try:
                    resp = requests.post(
                        f"{ARBITRAGE_API_BASE}/api/arbitrage/quantum/decide",
                        json=payload,
                        timeout=3,
                    )
                    status_codes.append(resp.status_code)
                    success = True
                    break
                except requests.RequestException:
                    connection_errors += 1
                    time.sleep(0.05)
            if not success:
                # Continue burst even if a single request fails twice;
                # we still expect limiter behavior across remaining requests.
                continue

        assert 429 in status_codes, (
            "Expected at least one HTTP 429 during burst, "
            f"attempts={attempts}, statuses={status_codes[:10]}..., "
            f"connection_errors={connection_errors}"
        )


# ── Dashboard Connector (optional) ───────────────────────────────────────────


@pytest.mark.skipif(not _service_up(DASHBOARD_URL), reason="Dashboard not running")
class TestDashboardConnector:
    def test_dashboard_health(self):
        """Dashboard responds on configured URL."""
        resp = requests.get(DASHBOARD_URL, timeout=5)
        assert resp.status_code < 500, f"Dashboard returned {resp.status_code}"


# ── Vortex Sentinel Relay (optional) ─────────────────────────────────────────


@pytest.mark.skipif(not _service_up(f"{VORTEX_API}/health"), reason="Vortex not running")
class TestVortexConnector:
    def test_vortex_health(self):
        """/health endpoint responds."""
        resp = requests.get(f"{VORTEX_API}/health", timeout=5)
        assert resp.status_code == 200

    def test_vortex_quantum_decide(self):
        """/decide endpoint accepts quantum request and returns decision with state."""
        payload = {"price_source": 100.0, "price_target": 115.0}
        resp = requests.post(f"{VORTEX_API}/decide", json=payload, timeout=5)
        assert resp.status_code == 200
        data = resp.json()
        assert "state" in data, "Response must include 'state'"
        # Vortex may return 'resonance' + 'frequency' instead of 'margin_pct' (Go schema)
        assert any(k in data for k in ("margin_pct", "resonance")), (
            f"Response must include 'margin_pct' or 'resonance', got: {list(data.keys())}"
        )
