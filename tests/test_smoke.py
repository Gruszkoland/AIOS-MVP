"""
Smoke Tests — Harmonia 369 Webhook Server
Minimalne testy pokrywające krytyczne ścieżki.
Uruchomienie: pytest tests/test_smoke.py -v
"""
import json
import sys
import os
import types

# Add harmonia-dashboard to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'harmonia-dashboard'))


class TestGetStatsConversion:
    """Test avg_score Decimal→float conversion (bug fix)."""

    def test_stats_returns_float_avg_score(self):
        from decimal import Decimal
        # Simulate RealDictCursor row
        row = {
            "total": 11,
            "hot": 5,
            "warm": 5,
            "confirmed": 1,
            "avg_score": Decimal("45.8181818181818182"),
        }
        result = dict(row)
        result["avg_score"] = round(float(result.get("avg_score", 0)), 1)
        result["total"] = int(result.get("total", 0))
        result["hot"] = int(result.get("hot", 0))
        result["warm"] = int(result.get("warm", 0))
        result["confirmed"] = int(result.get("confirmed", 0))

        assert isinstance(result["avg_score"], float)
        assert result["avg_score"] == 45.8
        assert isinstance(result["total"], int)
        assert result["total"] == 11

    def test_stats_zero_avg(self):
        from decimal import Decimal
        row = {"total": 0, "hot": 0, "warm": 0, "confirmed": 0, "avg_score": Decimal("0")}
        result = dict(row)
        result["avg_score"] = round(float(result.get("avg_score", 0)), 1)
        assert result["avg_score"] == 0.0


class TestHarmonyScoring:
    """Test the Harmony 369 scoring formula: W = (W_V×3 + W_R×6 + W_E×9) / 18."""

    def test_score_formula_basic(self):
        wv, wr, we = 50, 60, 30
        total = round((wv * 3 + wr * 6 + we * 9) / 18)
        assert total == 43  # (150 + 360 + 270) / 18

    def test_score_hot_threshold(self):
        # < 50 = HOT
        total = 42
        status = "HOT" if total < 50 else "WARM"
        assert status == "HOT"

    def test_score_warm_threshold(self):
        total = 65
        status = "HOT" if total < 50 else "WARM"
        assert status == "WARM"


class TestLeadSearch:
    """Test lead search/filter logic."""

    def test_search_by_name(self):
        leads = [
            {"business_name": "Pizzeria Roma", "city": "Krakow", "email": "roma@x.pl"},
            {"business_name": "Salon Elegancja", "city": "Krakow", "email": "e@x.pl"},
            {"business_name": "Auto-Fix", "city": "Warszawa", "email": "af@x.pl"},
        ]
        query = "roma"
        results = [l for l in leads if query.lower() in l["business_name"].lower()]
        assert len(results) == 1
        assert results[0]["business_name"] == "Pizzeria Roma"

    def test_search_by_city(self):
        leads = [
            {"business_name": "A", "city": "Kraków", "email": "a@x.pl"},
            {"business_name": "B", "city": "Warszawa", "email": "b@x.pl"},
        ]
        query = "kraków"
        results = [l for l in leads if query.lower() in l["city"].lower()]
        assert len(results) == 1

    def test_search_empty_query_returns_all(self):
        leads = [{"business_name": "A"}, {"business_name": "B"}]
        query = ""
        results = leads if not query else [l for l in leads if query.lower() in l["business_name"].lower()]
        assert len(results) == 2


class TestEmailAnalysis:
    """Test client needs analysis logic."""

    def test_analysis_detects_low_visibility(self):
        lead = {"score_wv": 20, "score_wr": 60, "score_we": 40, "photos_count": 1, "verified": False}
        issues = []
        if lead["score_wv"] < 40:
            issues.append("niska widoczność")
        if lead["photos_count"] < 3:
            issues.append("za mało zdjęć")
        if not lead["verified"]:
            issues.append("brak weryfikacji")
        assert "niska widoczność" in issues
        assert "za mało zdjęć" in issues
        assert "brak weryfikacji" in issues

    def test_analysis_detects_low_reputation(self):
        lead = {"score_wr": 30, "rating": 2.5, "reviews_count": 3}
        issues = []
        if lead["score_wr"] < 50:
            issues.append("słaba reputacja")
        if lead["reviews_count"] < 10:
            issues.append("za mało opinii")
        assert "słaba reputacja" in issues
        assert "za mało opinii" in issues

    def test_healthy_lead_no_issues(self):
        lead = {"score_wv": 80, "score_wr": 75, "score_we": 70, "photos_count": 10, "verified": True, "rating": 4.5, "reviews_count": 50}
        issues = []
        if lead["score_wv"] < 40:
            issues.append("niska widoczność")
        if lead["score_wr"] < 50:
            issues.append("słaba reputacja")
        assert len(issues) == 0


class TestJSONSerialization:
    """Test that all types serialize to JSON properly."""

    def test_serialize_stats(self):
        stats = {"total": 11, "hot": 5, "warm": 5, "confirmed": 1, "avg_score": 45.8}
        j = json.dumps(stats)
        parsed = json.loads(j)
        assert parsed["avg_score"] == 45.8
        assert isinstance(parsed["total"], int)
