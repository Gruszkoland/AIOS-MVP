"""
ADRION 369 — Mass Generator v2.6 (PROGRAMATOR #14)
Bulk import & page generation for qualified wholesale deals.

Pipeline:
  1. Query DB for deals matching thresholds (margin > 15%, stock > 5)
  2. Generate URL slugs + SEO data via RAG market context
  3. Export manifest.json consumed by Next.js generateStaticParams()
  4. Optionally trigger ISR revalidation for changed pages

Usage:
  python -m arbitrage.mass_generator                     # export manifest
  python -m arbitrage.mass_generator --channel AUDIO_PREMIUM
  python -m arbitrage.mass_generator --min-margin 0.20 --min-stock 10
  python -m arbitrage.mass_generator --revalidate        # POST to Next.js
"""
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import BASE_DIR, QUANTUM_SCAN_CHANNELS
from .database import get_deals, init_db, record_kpi_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("mass_generator")

# ── Constants ─────────────────────────────────────────────────────────────────
MANIFEST_DIR = BASE_DIR / "micro-saas" / "data"
MANIFEST_FILE = MANIFEST_DIR / "product-manifest.json"
MIN_MARGIN_DEFAULT = 0.15
MIN_STOCK_DEFAULT = 5
MARKETS = ["DE", "PL"]

# Solfeggio frequency map per channel (for SEO micro-data)
CHANNEL_FREQ = {ch["id"]: ch["frequency"] for ch in QUANTUM_SCAN_CHANNELS}


def slugify(text: str) -> str:
    """Convert product name to URL-safe slug."""
    text = text.lower().strip()
    # Replace common German/Polish chars
    replacements = {
        "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
        "ą": "a", "ć": "c", "ę": "e", "ł": "l",
        "ń": "n", "ó": "o", "ś": "s", "ź": "z", "ż": "z",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def generate_seo_title(name: str, market: str) -> str:
    """Market-specific SEO title."""
    if market == "PL":
        return f"Kup {name} — Najniższa Cena Hurtowa | ADRION"
    return f"{name} — Zertifizierter Händler Großhandel | ADRION"


def generate_seo_description(name: str, margin_pct: float, market: str) -> str:
    """Market-specific meta description."""
    pct = round(margin_pct * 100, 1)
    if market == "PL":
        return (
            f"{name} — cena hurtowa z marżą {pct}%. "
            "Bezpośrednio z magazynu centralnego DACH. Gwarancja producenta."
        )
    return (
        f"{name} — Großhandelspreis mit {pct}% Marge. "
        "Direkt vom Zentrallager. Herstellergarantie."
    )


def build_product_entry(deal: dict) -> dict:
    """Transform a DB deal row into a manifest entry for Next.js."""
    slug = slugify(deal["product_name"])
    channel = deal.get("channel_id", "AUDIO_PREMIUM")
    freq = CHANNEL_FREQ.get(channel, 432)

    entry = {
        "slug": slug,
        "sku": deal["sku"],
        "name": deal["product_name"],
        "channel": channel,
        "wholesalePrice": deal["wholesale_price"],
        "retailPriceDE": deal.get("retail_price_de"),
        "retailPricePL": deal.get("retail_price_pl"),
        "marginPct": round(deal.get("margin_pct", 0) * 100, 2),
        "stock": deal.get("stock_qty", 0),
        "supplier": deal.get("supplier", ""),
        "vortexResonance": deal.get("vortex_resonance"),
        "vortexPass": bool(deal.get("vortex_pass")),
        "solfeggioHz": freq,
        "status": deal.get("status", "new"),
        "scoutedAt": deal.get("scouted_at"),
        "markets": {},
    }

    # Generate per-market SEO data
    for mkt in MARKETS:
        entry["markets"][mkt] = {
            "seoTitle": generate_seo_title(deal["product_name"], mkt),
            "seoDescription": generate_seo_description(
                deal["product_name"], deal.get("margin_pct", 0), mkt
            ),
            "slug": f"{mkt.lower()}/{slug}",
        }

    return entry


def generate_manifest(
    channel_filter: Optional[str] = None,
    min_margin: float = MIN_MARGIN_DEFAULT,
    min_stock: int = MIN_STOCK_DEFAULT,
    statuses: Optional[list[str]] = None,
) -> dict:
    """
    Query qualified deals and build the full product manifest.

    Returns:
        {
            "generated_at": ISO timestamp,
            "total_products": int,
            "channels": {channel_id: count},
            "products": [product entries...],
            "staticParams": [{"slug": "..."}, ...],  # for generateStaticParams()
        }
    """
    init_db()

    # Query all qualifying deals
    all_deals = get_deals(
        channel_id=channel_filter,
        min_margin=min_margin,
        limit=500,
    )

    # Filter by stock and status
    qualified = []
    for d in all_deals:
        if d.get("stock_qty", 0) < min_stock:
            continue
        if statuses and d.get("status") not in statuses:
            continue
        qualified.append(d)

    log.info(
        "Mass Generator: %d deals from DB, %d qualified (margin>=%.0f%%, stock>=%d)",
        len(all_deals), len(qualified), min_margin * 100, min_stock,
    )

    # Build manifest
    products = []
    channels_count: dict[str, int] = {}
    static_params: list[dict] = []

    for deal in qualified:
        entry = build_product_entry(deal)
        products.append(entry)

        ch = entry["channel"]
        channels_count[ch] = channels_count.get(ch, 0) + 1

        # Static params for Next.js generateStaticParams()
        static_params.append({"slug": entry["slug"]})

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_products": len(products),
        "channels": channels_count,
        "min_margin_pct": min_margin * 100,
        "min_stock": min_stock,
        "products": products,
        "staticParams": static_params,
    }

    return manifest


def export_manifest(manifest: dict) -> Path:
    """Write manifest to JSON file for Next.js consumption."""
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    log.info("Manifest exported: %s (%d products)", MANIFEST_FILE, manifest["total_products"])
    return MANIFEST_FILE


def trigger_revalidation(slugs: list[str], base_url: str = "http://localhost:3000") -> dict:
    """
    POST to Next.js revalidation endpoint for changed product pages.
    Requires the micro-saas app to be running with an /api/revalidate route.
    """
    import urllib.error
    import urllib.request

    results = {"revalidated": 0, "failed": 0, "errors": []}

    for slug in slugs:
        url = f"{base_url}/api/revalidate?path=/audio-premium/{slug}"
        req = urllib.request.Request(url, method="POST", data=b"")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    results["revalidated"] += 1
                else:
                    results["failed"] += 1
        except (urllib.error.URLError, OSError) as e:
            results["failed"] += 1
            results["errors"].append({"slug": slug, "error": str(e)})

    log.info(
        "Revalidation: %d ok, %d failed",
        results["revalidated"], results["failed"],
    )
    return results


def run_mass_generation(
    channel_filter: Optional[str] = None,
    min_margin: float = MIN_MARGIN_DEFAULT,
    min_stock: int = MIN_STOCK_DEFAULT,
    revalidate: bool = False,
) -> dict:
    """Full Mass Generator pipeline: query → build manifest → export → (revalidate)."""
    started = time.monotonic()

    manifest = generate_manifest(
        channel_filter=channel_filter,
        min_margin=min_margin,
        min_stock=min_stock,
    )

    filepath = export_manifest(manifest)

    result = {
        "manifest_path": str(filepath),
        "total_products": manifest["total_products"],
        "channels": manifest["channels"],
        "static_params_count": len(manifest["staticParams"]),
        "revalidation": None,
    }

    if revalidate and manifest["staticParams"]:
        slugs = [p["slug"] for p in manifest["staticParams"]]
        result["revalidation"] = trigger_revalidation(slugs)

    # Record KPI event
    record_kpi_event(
        stream="wholesale",
        event_type="mass_generation",
        amount_usd=0,
        meta={
            "products": manifest["total_products"],
            "channels": manifest["channels"],
            "source": "mass_generator",
        },
    )

    elapsed = round(time.monotonic() - started, 3)
    result["elapsed_seconds"] = elapsed
    log.info(
        "═══ MASS GENERATION complete: %d products, %d params, %.3fs ═══",
        manifest["total_products"], len(manifest["staticParams"]), elapsed,
    )

    return result


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ADRION 369 Mass Generator v2.6")
    parser.add_argument("--channel", type=str, default=None, help="Filter by channel ID")
    parser.add_argument("--min-margin", type=float, default=MIN_MARGIN_DEFAULT, help="Min margin (0.15 = 15%%)")
    parser.add_argument("--min-stock", type=int, default=MIN_STOCK_DEFAULT, help="Min stock quantity")
    parser.add_argument("--revalidate", action="store_true", help="Trigger Next.js ISR revalidation")
    args = parser.parse_args()

    result = run_mass_generation(
        channel_filter=args.channel,
        min_margin=args.min_margin,
        min_stock=args.min_stock,
        revalidate=args.revalidate,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
