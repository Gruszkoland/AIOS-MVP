-- ADRION 369 — Migration 001: Initial Schema
-- Applied by: scripts/migrate.py
-- Direction UP: creates all tables
-- Direction DOWN: drops all tables (see DOWN comments)

-- ── Freelance Arbitrage Core ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS jobs (
    id          TEXT PRIMARY KEY,
    platform    TEXT NOT NULL,
    title       TEXT NOT NULL,
    description TEXT,
    budget_min  REAL DEFAULT 0,
    budget_max  REAL DEFAULT 0,
    client      TEXT,
    url         TEXT,
    keywords    TEXT,
    scouted_at  TEXT DEFAULT (datetime('now')),
    status      TEXT DEFAULT 'new'
);
-- DOWN: DROP TABLE IF EXISTS jobs;

CREATE TABLE IF NOT EXISTS bids (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT REFERENCES jobs(id),
    cover_letter    TEXT,
    our_price       REAL,
    est_profit_usd  REAL,
    analyzer_score  INTEGER,
    llm_backend     TEXT,
    approved        INTEGER DEFAULT 0,
    sent_at         TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);
-- DOWN: DROP TABLE IF EXISTS bids;

CREATE TABLE IF NOT EXISTS kpis (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at   TEXT DEFAULT (datetime('now')),
    jobs_scouted  INTEGER DEFAULT 0,
    bids_sent     INTEGER DEFAULT 0,
    bids_won      INTEGER DEFAULT 0,
    revenue_usd   REAL DEFAULT 0,
    profit_usd    REAL DEFAULT 0,
    xrp_earned    REAL DEFAULT 0
);
-- DOWN: DROP TABLE IF EXISTS kpis;

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
-- DOWN: DROP TABLE IF EXISTS settings;

CREATE TABLE IF NOT EXISTS earnings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT,
    amount_usd      REAL NOT NULL,
    source_note     TEXT,
    earned_at       TEXT DEFAULT (datetime('now'))
);
-- DOWN: DROP TABLE IF EXISTS earnings;

CREATE TABLE IF NOT EXISTS xrp_snapshots (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    xrp_price_usd    REAL NOT NULL,
    total_earned_usd REAL NOT NULL,
    xrp_equivalent   REAL NOT NULL,
    xrp_target       REAL NOT NULL DEFAULT 1000,
    pct_complete     REAL NOT NULL,
    snapshot_at      TEXT DEFAULT (datetime('now'))
);
-- DOWN: DROP TABLE IF EXISTS xrp_snapshots;

CREATE TABLE IF NOT EXISTS autopilot_runs (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at         TEXT NOT NULL,
    finished_at        TEXT,
    success            INTEGER NOT NULL DEFAULT 0,
    dry_run            INTEGER NOT NULL DEFAULT 0,
    jobs_scouted       INTEGER DEFAULT 0,
    new_jobs           INTEGER DEFAULT 0,
    analyzed           INTEGER DEFAULT 0,
    bids_created       INTEGER DEFAULT 0,
    bids_today         INTEGER DEFAULT 0,
    total_earned_usd   REAL DEFAULT 0,
    error_message      TEXT
);
-- DOWN: DROP TABLE IF EXISTS autopilot_runs;

CREATE TABLE IF NOT EXISTS kpi_events (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    stream             TEXT NOT NULL,
    event_type         TEXT NOT NULL,
    amount_usd         REAL DEFAULT 0,
    est_cost_usd       REAL DEFAULT 0,
    meta_json          TEXT,
    created_at         TEXT DEFAULT (datetime('now'))
);
-- DOWN: DROP TABLE IF EXISTS kpi_events;

-- ── Wholesale Arbitrage ───────────────────────────────────────────────────────

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
-- DOWN: DROP TABLE IF EXISTS deals;

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
-- DOWN: DROP TABLE IF EXISTS subscriptions;

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
-- DOWN: DROP TABLE IF EXISTS alerts;

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
-- DOWN: DROP TABLE IF EXISTS payment_events;

-- ── Migration Tracking ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS migrations_applied (
    version     INTEGER PRIMARY KEY,
    filename    TEXT NOT NULL,
    file_hash   TEXT NOT NULL,
    applied_at  TEXT DEFAULT (datetime('now'))
);
-- DOWN: DROP TABLE IF EXISTS migrations_applied;
