"""
ADRION 369 — B2B Wholesale Scout Bridge (PROGRAMATOR #6/#12)
Bridges wholesale supplier feeds → deals table → Oracle analysis.

Architecture:
  Hurtownia API/Feed → Sentinel Monitor → Orchestrator Bridge
  → Oracle scoring → DB (deals table) → SPP generation trigger

Supported feed formats: JSON, XML (product catalog), CSV.
Mock mode available for testing without live feeds.
"""
import hashlib
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Literal

from .analyzer import calculate_market_resonance
from .config import QUANTUM_SCAN_CHANNELS
from .database import upsert_deal

logger = logging.getLogger("adrion.wholesale_scout")

FeedFormat = Literal["json", "xml", "csv"]

# ═══════════════════════════════════════════════════════════════
# MOCK WHOLESALE DATA
# ═══════════════════════════════════════════════════════════════

MOCK_WHOLESALE_PRODUCTS = [
    {"sku": "SEN-HD660S2", "name": "Sennheiser HD 660S2", "wholesale": 285.00,
     "retail_de": 399.00, "retail_pl": 1799.00, "stock": 12, "supplier": "ThomannDE",
     "channel": "AUDIO_PREMIUM", "url": "https://example.com/hd660s2"},
    {"sku": "BEY-DT1990", "name": "Beyerdynamic DT 1990 Pro", "wholesale": 320.00,
     "retail_de": 449.00, "retail_pl": 1999.00, "stock": 8, "supplier": "ThomannDE",
     "channel": "AUDIO_PREMIUM", "url": "https://example.com/dt1990"},
    {"sku": "FIO-K9PRO", "name": "FiiO K9 Pro ESS", "wholesale": 199.00,
     "retail_de": 299.00, "retail_pl": 1399.00, "stock": 15, "supplier": "AmazonWH",
     "channel": "AUDIO_PREMIUM", "url": "https://example.com/k9pro"},
    {"sku": "SOL-INV5KW", "name": "Solis 5kW Hybrid Inverter", "wholesale": 780.00,
     "retail_de": 1150.00, "retail_pl": 5200.00, "stock": 25, "supplier": "SolarDACH",
     "channel": "SMART_ENERGY", "url": "https://example.com/solis5kw"},
    {"sku": "ROB-HUSQ435", "name": "Husqvarna Automower 435X AWD", "wholesale": 2100.00,
     "retail_de": 3299.00, "retail_pl": 14999.00, "stock": 4, "supplier": "RobotShopDE",
     "channel": "ROBOTICS_AI", "url": "https://example.com/husq435"},
    {"sku": "AUD-TOPPING", "name": "Topping D90SE DAC", "wholesale": 420.00,
     "retail_de": 599.00, "retail_pl": 2699.00, "stock": 20, "supplier": "AmazonWH",
     "channel": "AUDIO_PREMIUM", "url": "https://example.com/toppingd90"},
    {"sku": "ENR-BATT10", "name": "BYD Battery Box HVS 10.2kWh", "wholesale": 3200.00,
     "retail_de": 4500.00, "retail_pl": 19900.00, "stock": 6, "supplier": "SolarDACH",
     "channel": "SMART_ENERGY", "url": "https://example.com/byd102"},
    {"sku": "BIO-OURA4", "name": "Oura Ring Gen4", "wholesale": 280.00,
     "retail_de": 399.00, "retail_pl": 1899.00, "stock": 50, "supplier": "BioTechGmbH",
     "channel": "BIOTECH_HEALTH", "url": "https://example.com/oura4"},
    {"sku": "REF-IPAD12", "name": "iPad Pro 12.9 M2 (Refurbished)", "wholesale": 580.00,
     "retail_de": 799.00, "retail_pl": 3599.00, "stock": 10, "supplier": "RefurbMart",
     "channel": "REFURBISHED_LUX", "url": "https://example.com/ipadrefurb"},
    {"sku": "ROB-DJI-M3", "name": "DJI Mavic 3 Pro", "wholesale": 1500.00,
     "retail_de": 2099.00, "retail_pl": 9499.00, "stock": 7, "supplier": "RobotShopDE",
     "channel": "ROBOTICS_AI", "url": "https://example.com/mavic3"},
]


def _make_deal_id(sku: str, supplier: str) -> str:
    raw = f"{sku}:{supplier}:{datetime.now().date()}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════
# FEED PARSERS
# ═══════════════════════════════════════════════════════════════

def parse_json_feed(data: str | dict | list) -> list[dict]:
    """Parse JSON feed → normalized product list."""
    if isinstance(data, str):
        data = json.loads(data)
    products = data if isinstance(data, list) else data.get("products", [])
    normalized = []
    for p in products:
        normalized.append({
            "sku": p.get("sku", p.get("id", "")),
            "product_name": p.get("name", p.get("product_name", p.get("title", ""))),
            "wholesale_price": float(p.get("wholesale", p.get("wholesale_price", 0))),
            "retail_price_de": float(p.get("retail_de", p.get("retail_price_de", 0))),
            "retail_price_pl": float(p.get("retail_pl", p.get("retail_price_pl", 0))),
            "stock_qty": int(p.get("stock", p.get("stock_qty", 0))),
            "supplier": p.get("supplier", ""),
            "channel_id": p.get("channel", p.get("channel_id", "AUDIO_PREMIUM")),
            "source_url": p.get("url", p.get("source_url", "")),
        })
    return normalized


def parse_xml_feed(xml_data: str) -> list[dict]:
    """Parse XML product catalog → normalized product list."""
    root = ET.fromstring(xml_data)
    products = []
    for item in root.iter("product"):
        products.append({
            "sku": _xml_text(item, "sku") or _xml_text(item, "id") or "",
            "product_name": _xml_text(item, "name") or _xml_text(item, "title") or "",
            "wholesale_price": float(_xml_text(item, "wholesale_price") or _xml_text(item, "price") or 0),
            "retail_price_de": float(_xml_text(item, "retail_price_de") or 0),
            "retail_price_pl": float(_xml_text(item, "retail_price_pl") or 0),
            "stock_qty": int(_xml_text(item, "stock") or _xml_text(item, "quantity") or 0),
            "supplier": _xml_text(item, "supplier") or "",
            "channel_id": _xml_text(item, "channel") or "AUDIO_PREMIUM",
            "source_url": _xml_text(item, "url") or "",
        })
    return products


def parse_csv_feed(csv_data: str) -> list[dict]:
    """Parse CSV feed (header row required) → normalized product list."""
    lines = csv_data.strip().split("\n")
    if len(lines) < 2:
        return []
    headers = [h.strip().lower() for h in lines[0].split(",")]
    products = []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = [v.strip() for v in line.split(",")]
        row = dict(zip(headers, values))
        products.append({
            "sku": row.get("sku", row.get("id", "")),
            "product_name": row.get("name", row.get("product_name", "")),
            "wholesale_price": float(row.get("wholesale_price", row.get("wholesale", 0)) or 0),
            "retail_price_de": float(row.get("retail_price_de", row.get("retail_de", 0)) or 0),
            "retail_price_pl": float(row.get("retail_price_pl", row.get("retail_pl", 0)) or 0),
            "stock_qty": int(row.get("stock_qty", row.get("stock", 0)) or 0),
            "supplier": row.get("supplier", ""),
            "channel_id": row.get("channel_id", row.get("channel", "AUDIO_PREMIUM")),
            "source_url": row.get("url", row.get("source_url", "")),
        })
    return products


def _xml_text(element, tag: str) -> str | None:
    child = element.find(tag)
    return child.text.strip() if child is not None and child.text else None


# ═══════════════════════════════════════════════════════════════
# ENRICHMENT — Vortex Scoring
# ═══════════════════════════════════════════════════════════════

def enrich_deal(product: dict) -> dict:
    """
    Enrich a raw product with Vortex resonance scoring.
    Calculates margin, digital root, vortex pass, and assigns channel.
    """
    wp = product.get("wholesale_price", 0)
    rp_de = product.get("retail_price_de", 0)
    rp_pl = product.get("retail_price_pl", 0)
    rp = rp_de or rp_pl  # Prefer DE price for DACH→PL flow

    if wp <= 0 or rp <= 0:
        product["margin_pct"] = 0
        product["vortex_resonance"] = 0
        product["vortex_pass"] = False
        return product

    resonance = calculate_market_resonance(wp, rp)
    product["margin_pct"] = resonance["margin_pct"]
    product["vortex_resonance"] = resonance["resonance"]
    product["vortex_pass"] = resonance["vortex_pass"]
    return product


def filter_by_channel(products: list[dict], channel_id: str) -> list[dict]:
    """Filter products matching a specific channel."""
    channel_conf = next(
        (ch for ch in QUANTUM_SCAN_CHANNELS if ch["id"] == channel_id), None
    )
    if not channel_conf:
        return products

    min_margin = channel_conf["min_margin"] / 100.0
    keywords = [kw.lower() for kw in channel_conf["keywords"]]

    filtered = []
    for p in products:
        # Name must match at least one keyword, or channel must be explicitly set
        name_lower = p.get("product_name", "").lower()
        if p.get("channel_id") == channel_id:
            if p.get("margin_pct", 0) >= min_margin:
                filtered.append(p)
        elif any(kw in name_lower for kw in keywords):
            if p.get("margin_pct", 0) >= min_margin:
                p["channel_id"] = channel_id
                filtered.append(p)
    return filtered


# ═══════════════════════════════════════════════════════════════
# MAIN SCOUT BRIDGE
# ═══════════════════════════════════════════════════════════════

def scout_wholesale(
    feed_data: str | dict | list | None = None,
    feed_format: FeedFormat = "json",
    channel_filter: str | None = None,
    min_margin: float = 0.15,
    min_stock: int = 1,
    use_mock: bool = True,
) -> dict:
    """
    B2B Wholesale Scout Bridge — main entry point.

    1. Parse feed (JSON/XML/CSV) or use mock data
    2. Enrich each product with Vortex resonance
    3. Filter by margin + stock + channel
    4. Persist qualifying deals to DB
    5. Return summary

    Args:
        feed_data: Raw feed string/JSON/list (None = mock mode)
        feed_format: "json" | "xml" | "csv"
        channel_filter: Optional channel_id to filter by
        min_margin: Minimum margin threshold (0.15 = 15%)
        min_stock: Minimum stock quantity
        use_mock: Force mock mode

    Returns:
        {"new_deals": int, "updated_deals": int, "deals": list, "mode": str}
    """
    # ── 1. Parse ──
    if use_mock or feed_data is None:
        products = _mock_wholesale_products()
        mode = "mock"
    elif feed_format == "json":
        products = parse_json_feed(feed_data)
        mode = "json_feed"
    elif feed_format == "xml":
        products = parse_xml_feed(feed_data)
        mode = "xml_feed"
    elif feed_format == "csv":
        products = parse_csv_feed(feed_data)
        mode = "csv_feed"
    else:
        products = []
        mode = "unknown"

    # ── 2. Enrich with Vortex ──
    for p in products:
        enrich_deal(p)

    # ── 3. Filter ──
    qualified = [
        p for p in products
        if p.get("margin_pct", 0) >= min_margin
        and p.get("stock_qty", 0) >= min_stock
    ]
    if channel_filter:
        qualified = filter_by_channel(qualified, channel_filter)

    # ── 4. Persist to DB ──
    new_count = 0
    updated_count = 0
    for deal in qualified:
        is_new = upsert_deal(deal)
        if is_new:
            new_count += 1
        else:
            updated_count += 1

    # ── 5. Summary ──
    logger.info(
        "Wholesale Scout → %d parsed, %d qualified, %d new, %d updated (mode=%s)",
        len(products), len(qualified), new_count, updated_count, mode,
    )

    return {
        "new_deals": new_count,
        "updated_deals": updated_count,
        "total_parsed": len(products),
        "total_qualified": len(qualified),
        "deals": [
            {
                "sku": d["sku"],
                "product_name": d.get("product_name", ""),
                "channel_id": d.get("channel_id", ""),
                "wholesale_price": d.get("wholesale_price", 0),
                "retail_price_de": d.get("retail_price_de", 0),
                "margin_pct": round(d.get("margin_pct", 0), 4),
                "vortex_resonance": d.get("vortex_resonance", 0),
                "vortex_pass": d.get("vortex_pass", False),
                "stock_qty": d.get("stock_qty", 0),
                "supplier": d.get("supplier", ""),
            }
            for d in qualified
        ],
        "mode": mode,
        "scan_timestamp": datetime.now().isoformat(),
    }


def _mock_wholesale_products() -> list[dict]:
    """Convert mock data to normalized format."""
    products = []
    for m in MOCK_WHOLESALE_PRODUCTS:
        products.append({
            "sku": m["sku"],
            "product_name": m["name"],
            "wholesale_price": m["wholesale"],
            "retail_price_de": m["retail_de"],
            "retail_price_pl": m.get("retail_pl", 0),
            "stock_qty": m["stock"],
            "supplier": m["supplier"],
            "channel_id": m["channel"],
            "source_url": m["url"],
        })
    return products
