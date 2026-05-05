-- Schema: Genesis Record — Leads Table
-- System: Harmonia 369 / Wirtualny Punkt Odniesienia

CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    business_name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50) DEFAULT '',
    score_total INTEGER NOT NULL CHECK (score_total BETWEEN 0 AND 100),
    score_wv INTEGER NOT NULL CHECK (score_wv BETWEEN 0 AND 100),
    score_wr INTEGER NOT NULL CHECK (score_wr BETWEEN 0 AND 100),
    score_we INTEGER NOT NULL CHECK (score_we BETWEEN 0 AND 100),
    verdict TEXT DEFAULT '',
    lead_status VARCHAR(20) DEFAULT 'NEW' CHECK (lead_status IN ('NEW', 'HOT', 'WARM', 'CONFIRMED', 'CONTACTED', 'CLOSED')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(lead_status);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score_total);
