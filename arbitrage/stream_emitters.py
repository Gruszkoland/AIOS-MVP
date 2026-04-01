"""
ADRION 369 - Auxiliary Stream Emitters
Automated KPI event emitters for UGC and resale streams.
"""
from datetime import datetime
import hashlib
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from .database import record_kpi_event, get_conn
from .config import STREAMS_CONNECTOR_TOKEN, UGC_SOURCE_URL, RESALE_SOURCE_URL


UGC_OPPORTUNITIES = [
    {"brand": "WellnessLab", "base_fee": 180.0},
    {"brand": "HomeFit", "base_fee": 220.0},
    {"brand": "GlowCare", "base_fee": 160.0},
    {"brand": "SmartDesk", "base_fee": 250.0},
    {"brand": "EcoBottle", "base_fee": 140.0},
]

RESALE_OPPORTUNITIES = [
    {"asset": "aged-domain", "entry": 35.0, "exit": 95.0},
    {"asset": "micro-site", "entry": 70.0, "exit": 190.0},
    {"asset": "vintage-tech", "entry": 45.0, "exit": 120.0},
    {"asset": "template-pack", "entry": 20.0, "exit": 75.0},
    {"asset": "newsletter-slot", "entry": 30.0, "exit": 88.0},
]


def _fetch_external_payload(url: str | None, stream_name: str = "unknown") -> dict | list | None:
    if not url:
        return None

    headers = {
        "User-Agent": "ADRION369-StreamConnector/1.0",
        "Accept": "application/json",
        "X-ADRION-Stream": stream_name
    }
    if STREAMS_CONNECTOR_TOKEN:
        headers["Authorization"] = f"Bearer {STREAMS_CONNECTOR_TOKEN}"

    # Try up to 2 times (initial + 1 retry)
    for attempt in range(2):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=15) as resp:
                # Hardening: Limit read to 1MB to prevent OOM
                data_raw = resp.read(1024 * 1024)
                data = data_raw.decode("utf-8")
                return json.loads(data)
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError) as e:
            if attempt == 0:
                continue # Retry once
            return None
    return None


def _normalize_external_events(stream: str, payload: dict | list | None) -> list[dict]:
    if payload is None:
        return []

    if isinstance(payload, list):
        raw_items = payload
    elif isinstance(payload, dict):
        raw_items = payload.get("events") or payload.get("opportunities") or payload.get("items") or []
        if not isinstance(raw_items, list):
            raw_items = []
    else:
        raw_items = []

    events = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue

        # Data Validation & Normalization
        try:
            amount = float(item.get("amount_usd", item.get("revenue_usd", 0)) or 0)
            est_cost = float(item.get("est_cost_usd", item.get("cost_usd", 0)) or 0)
        except (ValueError, TypeError):
            continue # Skip invalid numeric data

        # Sanity check: Avoid negative or impossible costs (Hardening)
        amount = max(0, amount)
        est_cost = max(0, est_cost)
        
        event_type = str(item.get("event_type", "")).strip().lower()
        meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}

        if stream == "ugc":
            default_type = "ugc_deal_closed" if amount > 0 else "ugc_pitch_sent"
            if not event_type:
                event_type = default_type
            if not meta:
                meta = {
                    "brand": str(item.get("brand", "unknown"))[:50],
                    "source": "external",
                }
        else:
            default_type = "resale_flip_closed" if amount > 0 else "resale_listing_created"
            if not event_type:
                event_type = default_type
            if not meta:
                meta = {
                    "asset": str(item.get("asset", item.get("name", "unknown")))[:50],
                    "source": "external",
                }

        events.append(
            {
                "event_type": event_type,
                "amount_usd": amount,
                "est_cost_usd": est_cost,
                "meta": meta,
            }
        )
    return events


def _emit_events(stream: str, events: list[dict], dry_run: bool = False) -> int:
    emitted = 0
    for event in events:
        if not dry_run:
            record_kpi_event(
                stream=stream,
                event_type=event["event_type"],
                amount_usd=event["amount_usd"],
                est_cost_usd=event["est_cost_usd"],
                meta=event["meta"],
            )
        emitted += 1
    return emitted


def _daily_count(stream: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM kpi_events WHERE stream=? AND DATE(created_at)=DATE('now')",
            (stream,),
        ).fetchone()
        return int(row["c"] or 0) if row else 0


def _seeded_ratio(seed: str) -> float:
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def run_ugc_emitter(max_events_per_day: int = 4, dry_run: bool = False) -> dict:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    already = _daily_count("ugc")
    remaining = max(0, int(max_events_per_day) - already)
    emitted = 0

    if remaining <= 0:
        return {"stream": "ugc", "emitted": 0, "reason": "daily_cap_reached"}

    external_events = _normalize_external_events("ugc", _fetch_external_payload(UGC_SOURCE_URL, "ugc"))
    if external_events:
        emitted = _emit_events("ugc", external_events[:remaining], dry_run=dry_run)
        return {
            "stream": "ugc",
            "emitted": emitted,
            "remaining": max(0, remaining - emitted),
            "source_mode": "external",
        }

    seeded_events = []
    for item in UGC_OPPORTUNITIES:
        ratio = _seeded_ratio(f"ugc:{today}:{item['brand']}")
        raw_upsell = 1.4 if ratio >= 0.45 else 1.0
        revenue = round(item["base_fee"] * raw_upsell, 2)
        est_cost = round(0.4 + (ratio * 1.2), 2)
        event_type = "ugc_deal_closed" if ratio >= 0.35 else "ugc_pitch_sent"
        seeded_events.append(
            {
                "event_type": event_type,
                "amount_usd": revenue if event_type == "ugc_deal_closed" else 0,
                "est_cost_usd": est_cost,
                "meta": {"brand": item["brand"], "raw_upsell_applied": raw_upsell > 1, "source": "seed"},
            }
        )

    emitted = _emit_events("ugc", seeded_events[:remaining], dry_run=dry_run)
    return {
        "stream": "ugc",
        "emitted": emitted,
        "remaining": max(0, remaining - emitted),
        "source_mode": "seed",
    }


def run_resale_emitter(max_events_per_day: int = 4, dry_run: bool = False) -> dict:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    already = _daily_count("resale")
    remaining = max(0, int(max_events_per_day) - already)
    emitted = 0

    if remaining <= 0:
        return {"stream": "resale", "emitted": 0, "reason": "daily_cap_reached"}

    external_events = _normalize_external_events("resale", _fetch_external_payload(RESALE_SOURCE_URL, "resale"))
    if external_events:
        emitted = _emit_events("resale", external_events[:remaining], dry_run=dry_run)
        return {
            "stream": "resale",
            "emitted": emitted,
            "remaining": max(0, remaining - emitted),
            "source_mode": "external",
        }

    seeded_events = []
    for item in RESALE_OPPORTUNITIES:
        ratio = _seeded_ratio(f"resale:{today}:{item['asset']}")
        margin = max(0, item["exit"] - item["entry"])
        closed = ratio >= 0.40
        est_cost = round(0.2 + (ratio * 0.9), 2)
        seeded_events.append(
            {
                "event_type": "resale_flip_closed" if closed else "resale_listing_created",
                "amount_usd": round(margin, 2) if closed else 0,
                "est_cost_usd": est_cost,
                "meta": {
                    "asset": item["asset"],
                    "entry_usd": item["entry"],
                    "exit_usd": item["exit"],
                    "source": "seed",
                },
            }
        )

    emitted = _emit_events("resale", seeded_events[:remaining], dry_run=dry_run)
    return {
        "stream": "resale",
        "emitted": emitted,
        "remaining": max(0, remaining - emitted),
        "source_mode": "seed",
    }


def run_aux_streams(ugc_daily_cap: int = 4, resale_daily_cap: int = 4, dry_run: bool = False) -> dict:
    ugc = run_ugc_emitter(max_events_per_day=ugc_daily_cap, dry_run=dry_run)
    resale = run_resale_emitter(max_events_per_day=resale_daily_cap, dry_run=dry_run)
    return {
        "ugc": ugc,
        "resale": resale,
        "dry_run": bool(dry_run),
        "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
    }


def get_stream_sources_status() -> dict:
    return {
        "ugc_source_url_configured": bool(UGC_SOURCE_URL),
        "resale_source_url_configured": bool(RESALE_SOURCE_URL),
        "connector_token_configured": bool(STREAMS_CONNECTOR_TOKEN),
    }
