-- ADRION 369 — Migration 002: Performance Indexes
-- Applied by: scripts/migrate.py
-- These indexes cover the most common query patterns.

-- ── Deals ─────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_deals_channel ON deals(channel_id);
CREATE INDEX IF NOT EXISTS idx_deals_status  ON deals(status);
CREATE INDEX IF NOT EXISTS idx_deals_margin  ON deals(margin_pct DESC);
-- DOWN: DROP INDEX IF EXISTS idx_deals_channel; DROP INDEX IF EXISTS idx_deals_status; DROP INDEX IF EXISTS idx_deals_margin;

-- ── Alerts ────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_alerts_deal ON alerts(deal_id);
CREATE INDEX IF NOT EXISTS idx_alerts_sub  ON alerts(subscription_id);
-- DOWN: DROP INDEX IF EXISTS idx_alerts_deal; DROP INDEX IF EXISTS idx_alerts_sub;

-- ── Jobs ──────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_jobs_status     ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_platform   ON jobs(platform);
CREATE INDEX IF NOT EXISTS idx_jobs_scouted_at ON jobs(scouted_at DESC);
-- DOWN: DROP INDEX IF EXISTS idx_jobs_status; DROP INDEX IF EXISTS idx_jobs_platform; DROP INDEX IF EXISTS idx_jobs_scouted_at;

-- ── Bids ──────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_bids_job_id     ON bids(job_id);
CREATE INDEX IF NOT EXISTS idx_bids_created_at ON bids(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bids_approved   ON bids(approved);
-- DOWN: DROP INDEX IF EXISTS idx_bids_job_id; DROP INDEX IF EXISTS idx_bids_created_at; DROP INDEX IF EXISTS idx_bids_approved;

-- ── KPI Events ────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_kpi_events_stream     ON kpi_events(stream);
CREATE INDEX IF NOT EXISTS idx_kpi_events_created_at ON kpi_events(created_at DESC);
-- DOWN: DROP INDEX IF EXISTS idx_kpi_events_stream; DROP INDEX IF EXISTS idx_kpi_events_created_at;

-- ── Payment Events ────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_payment_events_type ON payment_events(event_type);
-- DOWN: DROP INDEX IF EXISTS idx_payment_events_type;
