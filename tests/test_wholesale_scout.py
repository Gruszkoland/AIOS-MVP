"""
Unit tests for arbitrage/wholesale_scout.py — B2B Wholesale Scout Bridge.
All DB calls mocked.
"""
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# _make_deal_id
# ---------------------------------------------------------------------------

def test_make_deal_id_returns_16_chars():
    from arbitrage.wholesale_scout import _make_deal_id
    deal_id = _make_deal_id("SEN-HD660S2", "ThomannDE")
    assert len(deal_id) == 16


def test_make_deal_id_consistent_same_day():
    from arbitrage.wholesale_scout import _make_deal_id
    id1 = _make_deal_id("SKU-123", "SupplierA")
    id2 = _make_deal_id("SKU-123", "SupplierA")
    assert id1 == id2


def test_make_deal_id_different_for_different_sku():
    from arbitrage.wholesale_scout import _make_deal_id
    id1 = _make_deal_id("SKU-A", "Supplier")
    id2 = _make_deal_id("SKU-B", "Supplier")
    assert id1 != id2


# ---------------------------------------------------------------------------
# parse_json_feed
# ---------------------------------------------------------------------------

def test_parse_json_feed_list():
    from arbitrage.wholesale_scout import parse_json_feed
    data = [
        {"sku": "TEST-1", "name": "Product 1", "wholesale": 100.0,
         "retail_de": 200.0, "retail_pl": 900.0, "stock": 5,
         "supplier": "SupplierA", "channel": "AUDIO_PREMIUM", "url": "http://x.com"}
    ]
    result = parse_json_feed(data)
    assert len(result) == 1
    assert result[0]["sku"] == "TEST-1"
    assert result[0]["wholesale_price"] == 100.0
    assert result[0]["retail_price_de"] == 200.0


def test_parse_json_feed_dict_with_products():
    from arbitrage.wholesale_scout import parse_json_feed
    data = {"products": [
        {"sku": "P-1", "name": "Test", "wholesale": 50.0, "retail_de": 100.0, "stock": 10}
    ]}
    result = parse_json_feed(data)
    assert len(result) == 1
    assert result[0]["sku"] == "P-1"


def test_parse_json_feed_from_string():
    import json

    from arbitrage.wholesale_scout import parse_json_feed
    data = json.dumps([{"sku": "S-1", "wholesale_price": 80.0, "retail_price_de": 160.0, "stock": 3}])
    result = parse_json_feed(data)
    assert len(result) == 1


def test_parse_json_feed_empty_list():
    from arbitrage.wholesale_scout import parse_json_feed
    result = parse_json_feed([])
    assert result == []


def test_parse_json_feed_alternate_field_names():
    from arbitrage.wholesale_scout import parse_json_feed
    data = [{"id": "X-1", "title": "Alt Product", "wholesale_price": 200.0,
              "retail_price_de": 380.0, "stock_qty": 7, "channel_id": "SMART_ENERGY"}]
    result = parse_json_feed(data)
    assert result[0]["sku"] == "X-1"
    assert result[0]["product_name"] == "Alt Product"
    assert result[0]["channel_id"] == "SMART_ENERGY"


# ---------------------------------------------------------------------------
# parse_xml_feed
# ---------------------------------------------------------------------------

def test_parse_xml_feed_basic():
    from arbitrage.wholesale_scout import parse_xml_feed
    xml = """<catalog>
      <product>
        <sku>XML-001</sku>
        <name>XML Product</name>
        <wholesale_price>150.0</wholesale_price>
        <retail_price_de>300.0</retail_price_de>
        <stock>8</stock>
        <supplier>TestCo</supplier>
        <channel>AUDIO_PREMIUM</channel>
        <url>http://test.com</url>
      </product>
    </catalog>"""
    result = parse_xml_feed(xml)
    assert len(result) == 1
    assert result[0]["sku"] == "XML-001"
    assert result[0]["wholesale_price"] == 150.0


def test_parse_xml_feed_multiple_products():
    from arbitrage.wholesale_scout import parse_xml_feed
    xml = """<catalog>
      <product><sku>A1</sku><name>P1</name><wholesale_price>100</wholesale_price></product>
      <product><sku>A2</sku><name>P2</name><wholesale_price>200</wholesale_price></product>
    </catalog>"""
    result = parse_xml_feed(xml)
    assert len(result) == 2


def test_parse_xml_feed_with_id_fallback():
    from arbitrage.wholesale_scout import parse_xml_feed
    xml = """<catalog>
      <product><id>FALLBACK-ID</id><name>Fallback Product</name></product>
    </catalog>"""
    result = parse_xml_feed(xml)
    assert result[0]["sku"] == "FALLBACK-ID"


# ---------------------------------------------------------------------------
# parse_csv_feed
# ---------------------------------------------------------------------------

def test_parse_csv_feed_basic():
    from arbitrage.wholesale_scout import parse_csv_feed
    csv = "sku,name,wholesale_price,retail_price_de,stock\nCSV-1,CSV Product,120.0,240.0,5"
    result = parse_csv_feed(csv)
    assert len(result) == 1
    assert result[0]["sku"] == "CSV-1"
    assert result[0]["wholesale_price"] == 120.0


def test_parse_csv_feed_empty_returns_empty():
    from arbitrage.wholesale_scout import parse_csv_feed
    result = parse_csv_feed("only-header\n")
    assert result == []


def test_parse_csv_feed_less_than_2_lines():
    from arbitrage.wholesale_scout import parse_csv_feed
    result = parse_csv_feed("sku")
    assert result == []


def test_parse_csv_feed_skips_empty_lines():
    from arbitrage.wholesale_scout import parse_csv_feed
    csv = "sku,name,wholesale_price\nCSV-1,Product,100\n\nCSV-2,Product2,200"
    result = parse_csv_feed(csv)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# _xml_text
# ---------------------------------------------------------------------------

def test_xml_text_returns_text():
    import xml.etree.ElementTree as ET

    from arbitrage.wholesale_scout import _xml_text
    root = ET.fromstring("<product><sku>TEST-SKU</sku></product>")
    assert _xml_text(root, "sku") == "TEST-SKU"


def test_xml_text_returns_none_missing():
    import xml.etree.ElementTree as ET

    from arbitrage.wholesale_scout import _xml_text
    root = ET.fromstring("<product><name>X</name></product>")
    assert _xml_text(root, "sku") is None


# ---------------------------------------------------------------------------
# enrich_deal
# ---------------------------------------------------------------------------

def test_enrich_deal_calculates_margin():
    from arbitrage.wholesale_scout import enrich_deal
    with patch("arbitrage.wholesale_scout.calculate_market_resonance") as mock_mr:
        mock_mr.return_value = {"margin_pct": 0.5, "resonance": 0.8, "vortex_pass": True}
        product = {
            "sku": "E-1", "wholesale_price": 100.0, "retail_price_de": 200.0,
            "retail_price_pl": 900.0, "stock_qty": 5,
        }
        result = enrich_deal(product)
    assert result["margin_pct"] == 0.5
    assert result["vortex_resonance"] == 0.8
    assert result["vortex_pass"] is True


def test_enrich_deal_zero_prices():
    from arbitrage.wholesale_scout import enrich_deal
    product = {"sku": "E-0", "wholesale_price": 0, "retail_price_de": 0, "stock_qty": 5}
    result = enrich_deal(product)
    assert result["margin_pct"] == 0
    assert result["vortex_pass"] is False


def test_enrich_deal_uses_retail_de_preferring_over_pl():
    from arbitrage.wholesale_scout import enrich_deal
    with patch("arbitrage.wholesale_scout.calculate_market_resonance") as mock_mr:
        mock_mr.return_value = {"margin_pct": 0.3, "resonance": 0.6, "vortex_pass": True}
        product = {
            "sku": "E-2", "wholesale_price": 100.0,
            "retail_price_de": 150.0, "retail_price_pl": 500.0
        }
        enrich_deal(product)
        # Should call with (wholesale=100, retail=150) — DE preferred
        mock_mr.assert_called_once_with(100.0, 150.0)


# ---------------------------------------------------------------------------
# filter_by_channel
# ---------------------------------------------------------------------------

def test_filter_by_channel_unknown_channel():
    from arbitrage.wholesale_scout import filter_by_channel
    products = [{"product_name": "Any Product", "channel_id": "UNKNOWN_CH", "margin_pct": 0.5}]
    # Unknown channel → return all products unchanged
    result = filter_by_channel(products, "NONEXISTENT_CHANNEL")
    assert result == products


def test_filter_by_channel_explicit_channel_id():
    from arbitrage.config import QUANTUM_SCAN_CHANNELS
    from arbitrage.wholesale_scout import filter_by_channel
    if not QUANTUM_SCAN_CHANNELS:
        pytest.skip("No channels configured")
    ch = QUANTUM_SCAN_CHANNELS[0]
    ch_id = ch["id"]
    min_margin = ch["min_margin"] / 100.0
    products = [
        {"product_name": "Matching Product", "channel_id": ch_id, "margin_pct": min_margin + 0.1, "stock_qty": 5},
        {"product_name": "Low Margin", "channel_id": ch_id, "margin_pct": 0.0, "stock_qty": 5},
    ]
    result = filter_by_channel(products, ch_id)
    assert len(result) == 1
    assert result[0]["product_name"] == "Matching Product"


# ---------------------------------------------------------------------------
# _mock_wholesale_products
# ---------------------------------------------------------------------------

def test_mock_wholesale_products_returns_list():
    from arbitrage.wholesale_scout import _mock_wholesale_products
    products = _mock_wholesale_products()
    assert isinstance(products, list)
    assert len(products) > 0


def test_mock_wholesale_products_have_required_keys():
    from arbitrage.wholesale_scout import _mock_wholesale_products
    required = {"sku", "product_name", "wholesale_price", "retail_price_de", "stock_qty", "supplier", "channel_id"}
    for p in _mock_wholesale_products():
        assert required.issubset(p.keys())


# ---------------------------------------------------------------------------
# scout_wholesale — integration (mocked DB)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_upsert_deal():
    with patch("arbitrage.wholesale_scout.upsert_deal") as m:
        m.return_value = True  # all new
        yield m


def test_scout_wholesale_mock_mode(mock_upsert_deal):
    from arbitrage.wholesale_scout import scout_wholesale
    with patch("arbitrage.wholesale_scout.calculate_market_resonance",
               return_value={"margin_pct": 0.4, "resonance": 0.7, "vortex_pass": True}):
        result = scout_wholesale(use_mock=True, min_margin=0.1)
    assert result["mode"] == "mock"
    assert result["total_parsed"] > 0
    assert "deals" in result


def test_scout_wholesale_json_feed(mock_upsert_deal):
    from arbitrage.wholesale_scout import scout_wholesale
    feed = [{"sku": "F-1", "name": "Feed Product", "wholesale": 100.0,
              "retail_de": 250.0, "stock": 10, "supplier": "TestCo", "channel": "AUDIO_PREMIUM"}]
    with patch("arbitrage.wholesale_scout.calculate_market_resonance",
               return_value={"margin_pct": 0.6, "resonance": 0.85, "vortex_pass": True}):
        result = scout_wholesale(feed_data=feed, feed_format="json", use_mock=False, min_margin=0.1)
    assert result["mode"] == "json_feed"
    assert result["total_parsed"] == 1


def test_scout_wholesale_filters_by_margin(mock_upsert_deal):
    from arbitrage.wholesale_scout import scout_wholesale
    with patch("arbitrage.wholesale_scout.calculate_market_resonance",
               return_value={"margin_pct": 0.1, "resonance": 0.4, "vortex_pass": False}):
        result = scout_wholesale(use_mock=True, min_margin=0.5)  # very high min
    # With margin=0.1 < min_margin=0.5, nothing qualifies
    assert result["total_qualified"] == 0


def test_scout_wholesale_csv_feed(mock_upsert_deal):
    from arbitrage.wholesale_scout import scout_wholesale
    csv = "sku,name,wholesale_price,retail_price_de,stock,supplier\nC-1,CSV Product,100,250,5,TestCo"
    with patch("arbitrage.wholesale_scout.calculate_market_resonance",
               return_value={"margin_pct": 0.6, "resonance": 0.8, "vortex_pass": True}):
        result = scout_wholesale(feed_data=csv, feed_format="csv", use_mock=False, min_margin=0.1)
    assert result["mode"] == "csv_feed"


def test_scout_wholesale_xml_feed(mock_upsert_deal):
    from arbitrage.wholesale_scout import scout_wholesale
    xml = """<catalog>
      <product>
        <sku>X-1</sku><name>XML Product</name>
        <wholesale_price>100</wholesale_price><retail_price_de>250</retail_price_de>
        <stock>5</stock>
      </product>
    </catalog>"""
    with patch("arbitrage.wholesale_scout.calculate_market_resonance",
               return_value={"margin_pct": 0.6, "resonance": 0.8, "vortex_pass": True}):
        result = scout_wholesale(feed_data=xml, feed_format="xml", use_mock=False, min_margin=0.1)
    assert result["mode"] == "xml_feed"


def test_scout_wholesale_unknown_format(mock_upsert_deal):
    from arbitrage.wholesale_scout import scout_wholesale
    result = scout_wholesale(feed_data="data", feed_format="yaml", use_mock=False)
    assert result["mode"] == "unknown"
    assert result["total_parsed"] == 0


def test_scout_wholesale_updated_counts(mock_upsert_deal):
    from arbitrage.wholesale_scout import scout_wholesale
    mock_upsert_deal.return_value = False  # existing deals → updated
    with patch("arbitrage.wholesale_scout.calculate_market_resonance",
               return_value={"margin_pct": 0.5, "resonance": 0.8, "vortex_pass": True}):
        result = scout_wholesale(use_mock=True, min_margin=0.1)
    assert result["new_deals"] == 0
    assert result["updated_deals"] > 0
