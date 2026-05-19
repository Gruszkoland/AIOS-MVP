-- ═══════════════════════════════════════════════════════════════════════════
-- ADRION 369 — Wholesale Arbitrage Schema (PROGRAMATOR #11)
-- Kompatybilny z: SQLite (obecny) / PostgreSQL (Supabase migration)
-- ═══════════════════════════════════════════════════════════════════════════

-- Okazje cenowe z hurtowni (B2B-WHOLESALE-BRIDGE)
CREATE TABLE IF NOT EXISTS deals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sku             TEXT NOT NULL,
    product_name    TEXT NOT NULL,
    channel_id      TEXT NOT NULL DEFAULT 'AUDIO_PREMIUM',
    wholesale_price REAL NOT NULL,
    retail_price_de REAL,
    retail_price_pl REAL,
    margin_pct      REAL,
    vortex_resonance INTEGER,
    vortex_pass     INTEGER DEFAULT 0,
    source_url      TEXT,
    supplier        TEXT,
    stock_qty       INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'new',
    scouted_at      TEXT DEFAULT (datetime('now')),
    executed_at     TEXT,
    UNIQUE(sku, supplier)
);

-- Subskrypcje SaaS (3 tiery: Pilot / Agresor / Dominator)
CREATE TABLE IF NOT EXISTS subscriptions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email      TEXT NOT NULL UNIQUE,
    tier            TEXT NOT NULL DEFAULT 'pilot' CHECK(tier IN ('pilot','agresor','dominator')),
    stripe_customer_id TEXT,
    stripe_sub_id   TEXT,
    active          INTEGER DEFAULT 1,
    channels_json   TEXT DEFAULT '["AUDIO_PREMIUM"]',
    max_alerts_day  INTEGER DEFAULT 3,
    created_at      TEXT DEFAULT (datetime('now')),
    expires_at      TEXT
);

-- Alerty cenowe (wysłane do subskrybentów)
CREATE TABLE IF NOT EXISTS alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id         INTEGER REFERENCES deals(id),
    subscription_id INTEGER REFERENCES subscriptions(id),
    channel_id      TEXT NOT NULL,
    alert_type      TEXT DEFAULT 'price_drop',
    margin_pct      REAL,
    sent            INTEGER DEFAULT 0,
    sent_at         TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Transakcje Stripe (webhook log)
CREATE TABLE IF NOT EXISTS payment_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stripe_event_id TEXT UNIQUE NOT NULL,
    event_type      TEXT NOT NULL,
    amount_cents    INTEGER NOT NULL DEFAULT 0,
    currency        TEXT DEFAULT 'pln',
    customer_email  TEXT,
    subscription_id INTEGER REFERENCES subscriptions(id),
    meta_json       TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Indeksy wydajnościowe
CREATE INDEX IF NOT EXISTS idx_deals_channel ON deals(channel_id);
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
CREATE INDEX IF NOT EXISTS idx_deals_margin ON deals(margin_pct);
CREATE INDEX IF NOT EXISTS idx_alerts_deal ON alerts(deal_id);
CREATE INDEX IF NOT EXISTS idx_alerts_sub ON alerts(subscription_id);
CREATE INDEX IF NOT EXISTS idx_payment_events_type ON payment_events(event_type);
