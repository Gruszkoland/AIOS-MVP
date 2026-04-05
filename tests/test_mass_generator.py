"""
Unit tests for arbitrage/mass_generator.py — Mass Generator v2.6 (PROGRAMATOR #14)
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DB_PATH", ":memory:")

from arbitrage.mass_generator import (
    MARKETS,
    MIN_STOCK_DEFAULT,
    build_product_entry,
    generate_manifest,
    generate_seo_description,
    generate_seo_title,
    slugify,
)

# ── slugify ────────────────────────────────────────────────────────────────────

class TestSlugify:
    def test_basic_ascii(self):
        assert slugify("Hello World") == "hello-world"

    def test_polish_chars(self):
        slug = slugify("Łódź Żółć")
        assert slug == "lodz-zolc"

    def test_german_chars(self):
        slug = slugify("Müller & Söhne GmbH")
        assert slug == "mueller-soehne-gmbh"

    def test_german_sharp_s(self):
        slug = slugify("Weißwurst")
        assert slug == "weisswurst"

    def test_strips_leading_trailing_hyphens(self):
        slug = slugify("  ---test--- ")
        assert not slug.startswith("-")
        assert not slug.endswith("-")

    def test_no_special_chars(self):
        slug = slugify("FiiO K9 Pro 2.0")
        assert slug == "fiio-k9-pro-2-0"

    def test_empty_string(self):
        slug = slugify("")
        assert slug == ""

    def test_all_spaces(self):
        slug = slugify("   ")
        assert slug == ""

    def test_numbers_preserved(self):
        slug = slugify("HD 660S Version 2")
        assert "660" in slug
        assert "2" in slug

    def test_mixed_case(self):
        slug = slugify("Sennheiser HD660S")
        assert slug == slug.lower()


# ── generate_seo_title ─────────────────────────────────────────────────────────

class TestGenerateSeoTitle:
    def test_pl_title_contains_kup(self):
        title = generate_seo_title("FiiO K9 Pro", "PL")
        assert "Kup" in title
        assert "FiiO K9 Pro" in title

    def test_de_title_contains_product(self):
        title = generate_seo_title("Sennheiser HD660", "DE")
        assert "Sennheiser HD660" in title

    def test_pl_title_contains_adrion(self):
        title = generate_seo_title("Test Product", "PL")
        assert "ADRION" in title

    def test_de_title_contains_grosshandel(self):
        title = generate_seo_title("Test Product", "DE")
        assert "Gro" in title  # "Großhandel" or "Großhandelspreis"


# ── generate_seo_description ──────────────────────────────────────────────────

class TestGenerateSeoDescription:
    def test_pl_contains_margin(self):
        desc = generate_seo_description("Test Product", 0.25, "PL")
        assert "25.0%" in desc or "25%" in desc

    def test_de_contains_margin(self):
        desc = generate_seo_description("Test Product", 0.30, "DE")
        assert "30.0%" in desc or "30%" in desc

    def test_pl_in_polish_language(self):
        desc = generate_seo_description("Produkt", 0.15, "PL")
        assert "hurtow" in desc.lower() or "magazyn" in desc.lower() or "marż" in desc.lower()

    def test_de_in_german_language(self):
        desc = generate_seo_description("Produkt", 0.15, "DE")
        assert "Großhandels" in desc or "Marge" in desc


# ── build_product_entry ────────────────────────────────────────────────────────

class TestBuildProductEntry:
    DEAL = {
        "sku": "FIIO-K9-PRO",
        "product_name": "FiiO K9 Pro",
        "channel_id": "AUDIO_PREMIUM",
        "wholesale_price": 199.0,
        "retail_price_de": 299.0,
        "retail_price_pl": 289.0,
        "margin_pct": 0.33,
        "vortex_resonance": 9,
        "vortex_pass": 1,
        "stock_qty": 25,
        "supplier": "AudioHaus",
        "status": "new",
        "scouted_at": "2025-01-01T12:00:00",
    }

    def test_slug_generated(self):
        entry = build_product_entry(self.DEAL)
        assert entry["slug"] == "fiio-k9-pro"

    def test_sku_preserved(self):
        entry = build_product_entry(self.DEAL)
        assert entry["sku"] == "FIIO-K9-PRO"

    def test_name_preserved(self):
        entry = build_product_entry(self.DEAL)
        assert entry["name"] == "FiiO K9 Pro"

    def test_margin_is_percentage(self):
        entry = build_product_entry(self.DEAL)
        # margin_pct 0.33 → stored as 33.0% in manifest
        assert entry["marginPct"] == pytest.approx(33.0, abs=0.1)

    def test_markets_present(self):
        entry = build_product_entry(self.DEAL)
        assert "markets" in entry
        for mkt in MARKETS:
            assert mkt in entry["markets"]

    def test_markets_have_seo_data(self):
        entry = build_product_entry(self.DEAL)
        for mkt in MARKETS:
            mkt_data = entry["markets"][mkt]
            assert "seoTitle" in mkt_data
            assert "seoDescription" in mkt_data
            assert "slug" in mkt_data

    def test_vortex_pass_is_bool(self):
        entry = build_product_entry(self.DEAL)
        assert isinstance(entry["vortexPass"], bool)

    def test_solfeggio_hz_field_present(self):
        entry = build_product_entry(self.DEAL)
        assert "solfeggioHz" in entry

    def test_wholesale_price_preserved(self):
        entry = build_product_entry(self.DEAL)
        assert entry["wholesalePrice"] == 199.0

    def test_market_slug_contains_market_prefix(self):
        entry = build_product_entry(self.DEAL)
        de_slug = entry["markets"]["DE"]["slug"]
        pl_slug = entry["markets"]["PL"]["slug"]
        assert de_slug.startswith("de/")
        assert pl_slug.startswith("pl/")

    def test_polish_product_name_slugified(self):
        deal = {**self.DEAL, "product_name": "Głośnik Bluetooth Łódź", "sku": "GLO-001"}
        entry = build_product_entry(deal)
        assert "głośnik" not in entry["slug"]
        assert "losnik" in entry["slug"] or "glosnik" in entry["slug"]


# ── generate_manifest ─────────────────────────────────────────────────────────

class TestGenerateManifest:
    """These tests require DB access — uses real init_db() with tmp_path DB."""

    @pytest.fixture(autouse=True)
    def setup_db(self, monkeypatch, tmp_path):
        db_file = str(tmp_path / "manifest_test.db")
        import arbitrage.config as cfg
        import arbitrage.database as db_mod
        monkeypatch.setattr(cfg, "DB_PATH", db_file)
        monkeypatch.setattr(db_mod, "DB_PATH", db_file)
        import sqlite3
        def patched_conn():
            conn = sqlite3.connect(db_file)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            return conn
        monkeypatch.setattr(db_mod, "get_conn", patched_conn)
        db_mod.init_db()

        # Seed 3 deals above threshold
        for i in range(3):
            db_mod.upsert_deal({
                "sku": f"PROD-{i:03d}",
                "product_name": f"Product {i}",
                "channel_id": "AUDIO_PREMIUM",
                "wholesale_price": 100.0,
                "retail_price_de": 150.0,
                "margin_pct": 0.33,
                "supplier": f"Sup{i}",
                "stock_qty": 10,
            })
        # One below stock threshold
        db_mod.upsert_deal({
            "sku": "LOW-STOCK",
            "product_name": "Low Stock Product",
            "channel_id": "AUDIO_PREMIUM",
            "wholesale_price": 100.0,
            "retail_price_de": 150.0,
            "margin_pct": 0.33,
            "supplier": "SupX",
            "stock_qty": 2,  # < MIN_STOCK_DEFAULT (5)
        })

    def test_manifest_structure(self):
        manifest = generate_manifest()
        assert "generated_at" in manifest
        assert "total_products" in manifest
        assert "channels" in manifest
        assert "products" in manifest
        assert "staticParams" in manifest

    def test_excludes_low_stock(self):
        manifest = generate_manifest(min_stock=MIN_STOCK_DEFAULT)
        slugs = [p["slug"] for p in manifest["products"]]
        assert not any("low-stock" in s for s in slugs)

    def test_channel_filter(self):
        manifest = generate_manifest(channel_filter="AUDIO_PREMIUM")
        assert all(p["channel"] == "AUDIO_PREMIUM" for p in manifest["products"])

    def test_counts_match_products(self):
        manifest = generate_manifest()
        assert manifest["total_products"] == len(manifest["products"])

    def test_static_params_have_slug(self):
        manifest = generate_manifest()
        for sp in manifest["staticParams"]:
            assert "slug" in sp


# ── export_manifest ────────────────────────────────────────────────────────────

class TestExportManifest:
    def test_creates_json_file(self, tmp_path, monkeypatch):
        import arbitrage.mass_generator as mg_mod
        manifest_file = tmp_path / "data" / "product-manifest.json"
        monkeypatch.setattr(mg_mod, "MANIFEST_DIR", tmp_path / "data")
        monkeypatch.setattr(mg_mod, "MANIFEST_FILE", manifest_file)

        manifest = {
            "generated_at": "2025-01-01T00:00:00",
            "total_products": 2,
            "channels": {"AUDIO_PREMIUM": 2},
            "products": [{"slug": "test-product", "name": "Test"}],
            "staticParams": [{"slug": "test-product"}],
        }
        path = mg_mod.export_manifest(manifest)
        assert path.exists()

    def test_json_content_valid(self, tmp_path, monkeypatch):
        import arbitrage.mass_generator as mg_mod
        manifest_file = tmp_path / "data" / "product-manifest.json"
        monkeypatch.setattr(mg_mod, "MANIFEST_DIR", tmp_path / "data")
        monkeypatch.setattr(mg_mod, "MANIFEST_FILE", manifest_file)

        manifest = {
            "generated_at": "2025-01-01T00:00:00",
            "total_products": 1,
            "channels": {},
            "products": [],
            "staticParams": [],
        }
        path = mg_mod.export_manifest(manifest)
        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["total_products"] == 1

    def test_unicode_preserved(self, tmp_path, monkeypatch):
        import arbitrage.mass_generator as mg_mod
        manifest_file = tmp_path / "data" / "product-manifest.json"
        monkeypatch.setattr(mg_mod, "MANIFEST_DIR", tmp_path / "data")
        monkeypatch.setattr(mg_mod, "MANIFEST_FILE", manifest_file)

        manifest = {
            "generated_at": "2025-01-01T00:00:00",
            "total_products": 1,
            "channels": {},
            "products": [{"name": "Głośnik Łódź"}],
            "staticParams": [],
        }
        path = mg_mod.export_manifest(manifest)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "Głośnik" in content
