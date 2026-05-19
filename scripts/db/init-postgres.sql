-- ═══════════════════════════════════════════════════════════════════════════════
-- ADRION 369 — PostgreSQL Initialization Script
-- Creates essential tables and indexes for ADRION 162D System
-- ═══════════════════════════════════════════════════════════════════════════════

-- Track ADRs (Architectural Decision Records)
CREATE TABLE IF NOT EXISTS adrs (
    id SERIAL PRIMARY KEY,
    adr_id VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PROPOSED',
    context TEXT,
    decision TEXT,
    consequences TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track personas and their states
CREATE TABLE IF NOT EXISTS persona_states (
    id SERIAL PRIMARY KEY,
    persona_name VARCHAR(100) NOT NULL,
    state_type VARCHAR(50) NOT NULL,
    pleasure FLOAT DEFAULT 0.5,
    arousal FLOAT DEFAULT 0.5,
    dominance FLOAT DEFAULT 0.5,
    metadata JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (persona_name, state_type)
);

-- Track system events (audit trail)
CREATE TABLE IF NOT EXISTS system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'INFO',
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track LLM rollout and KPI gates
CREATE TABLE IF NOT EXISTS llm_rollout_state (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'TESTING',
    canary_percentage INT DEFAULT 0,
    backend VARCHAR(50) NOT NULL DEFAULT 'ollama',
    kpi_gate_passed BOOLEAN DEFAULT FALSE,
    last_check TIMESTAMP,
    override_reason VARCHAR(255),
    override_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track API requests (basic metrics)
CREATE TABLE IF NOT EXISTS api_metrics (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(20) NOT NULL,
    status_code INT,
    response_time_ms INT,
    request_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_system_events_timestamp ON system_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_system_events_severity ON system_events(severity);
CREATE INDEX IF NOT EXISTS idx_persona_states_timestamp ON persona_states(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_llm_rollout_version ON llm_rollout_state(version);
CREATE INDEX IF NOT EXISTS idx_api_metrics_timestamp ON api_metrics(request_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_api_metrics_endpoint ON api_metrics(endpoint);

-- Grant privileges to adrion user
GRANT CONNECT ON DATABASE genesis_record TO adrion;
GRANT USAGE ON SCHEMA public TO adrion;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO adrion;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO adrion;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO adrion;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO adrion;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO adrion;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO adrion;

-- ═══════════════════════════════════════════════════════════════════════════════
-- Initialization complete
-- ═══════════════════════════════════════════════════════════════════════════════
