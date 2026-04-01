"""
XRP Tracker — fetches live XRP/USD price and calculates progress
toward the 1000 XRP earnings target.

Price source: CoinGecko public API (no key required, rate-limited to 10-30 req/min).
Fallback: cached price from last successful call stored in DB (kpis table).
"""

import json
import logging
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

from arbitrage.config import XRP_TARGET
from arbitrage.database import get_conn

logger = logging.getLogger(__name__)

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=ripple&vs_currencies=usd"
)
_BROWSER_UA = "ADRION-369-XRP-Tracker/1.0"

# ──────────────────────────────────────────────────────────────────────────────
# Price oracle
# ──────────────────────────────────────────────────────────────────────────────

def fetch_xrp_price_usd() -> float:
    """
    Return current XRP price in USD via CoinGecko.
    Falls back to last cached value (or 0.50 if DB is empty).
    """
    try:
        req = Request(COINGECKO_URL, headers={"User-Agent": _BROWSER_UA})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            price = float(data["ripple"]["usd"])
            _cache_xrp_price(price)
            return price
    except (URLError, KeyError, Exception) as exc:
        logger.warning("CoinGecko unavailable (%s) — using cached price", exc)
        return _get_cached_xrp_price()


def _cache_xrp_price(price: float):
    """Persist latest price in settings table."""
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("xrp_price_usd", str(price)),
        )


def _get_cached_xrp_price() -> float:
    """Read last cached XRP price; return 0.50 as safe default."""
    try:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key='xrp_price_usd'"
            ).fetchone()
            if row:
                return float(row["value"])
    except Exception:
        pass
    return 0.50  # conservative fallback


# ──────────────────────────────────────────────────────────────────────────────
# Earnings + progress
# ──────────────────────────────────────────────────────────────────────────────

def total_earned_usd() -> float:
    """Sum all profit_usd rows from kpis table."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(profit_usd), 0) AS total FROM kpis"
        ).fetchone()
        return float(row["total"]) if row else 0.0


def record_earning(profit_usd: float, source: str = ""):
    """Add a single earning record to kpis."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO kpis (profit_usd, revenue_usd) VALUES (?, ?)",
            (profit_usd, profit_usd),
        )
    logger.info("Recorded earning: $%.2f (%s)", profit_usd, source)


def get_progress() -> dict:
    """
    Return a full XRP progress snapshot dict:
    {
        xrp_price_usd, total_earned_usd, xrp_earned,
        xrp_target, xrp_remaining, pct_complete,
        timestamp
    }
    """
    price       = fetch_xrp_price_usd()
    earned_usd  = total_earned_usd()
    xrp_earned  = earned_usd / price if price > 0 else 0.0
    xrp_remaining = max(0.0, XRP_TARGET - xrp_earned)
    pct         = min(100.0, (xrp_earned / XRP_TARGET) * 100) if XRP_TARGET > 0 else 0.0

    return {
        "xrp_price_usd":   round(price, 4),
        "total_earned_usd":round(earned_usd, 2),
        "xrp_earned":      round(xrp_earned, 4),
        "xrp_target":      XRP_TARGET,
        "xrp_remaining":   round(xrp_remaining, 4),
        "pct_complete":    round(pct, 2),
        "timestamp":       datetime.now().isoformat(),
    }


def print_progress():
    """Pretty-print XRP progress to stdout."""
    p = get_progress()
    bar_len  = 30
    filled   = int(bar_len * p["pct_complete"] / 100)
    bar      = "█" * filled + "░" * (bar_len - filled)

    print("\n╔══════════════════════════════════════════════╗")
    print("║          XRP EARNINGS TRACKER                ║")
    print("╠══════════════════════════════════════════════╣")
    print(f"║  Price  : ${p['xrp_price_usd']:<10.4f}                        ║")
    print(f"║  Earned : ${p['total_earned_usd']:<10.2f} USD                  ║")
    print(f"║  XRP    : {p['xrp_earned']:<10.4f} / {p['xrp_target']:.0f} XRP              ║")
    print(f"║  [{bar}] {p['pct_complete']:5.1f}% ║")
    print(f"║  Remain : {p['xrp_remaining']:.4f} XRP (${p['xrp_remaining']*p['xrp_price_usd']:.2f})       ║")
    print("╚══════════════════════════════════════════════╝\n")
