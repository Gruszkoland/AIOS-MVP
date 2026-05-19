-- ============================================================================
-- ADRION 369 v4.0 - POSTGRESQL SCHEMA INITIALIZATION
-- Schema: Main system tables for Event Sourcing, State Management, Audit
-- ============================================================================
-- Execute: psql -U adrion_user -d adrion_prod < 001_schema_init.sql
-- Date: 2026-04-08
-- Author: MASTER ORCHESTRATOR (ADRION 369)
-- ============================================================================

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS adrion_prod;
\c adrion_prod;

-- ============================================================================
-- TABLE 1: tasks (Task/Agent assignment storage - replaces RAM TASKS_STORE)
-- ============================================================================
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(64) NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    result_data JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at DESC);

-- ============================================================================
-- TABLE 2: agents (MCP Server registry + health status)
-- ============================================================================
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    type VARCHAR(64) NOT NULL CHECK (type IN ('genesis', 'router', 'guardian', 'healer', 'oracle', 'vortex')),
    host VARCHAR(128) DEFAULT 'localhost',
    port INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'degraded', 'maintenance')),
    health_score NUMERIC(3, 2) DEFAULT 0.0,
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_updated_at ON agents(updated_at DESC);

-- ============================================================================
-- TABLE 3: events (Event Sourcing - immutable event log)
-- ============================================================================
CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(64) NOT NULL,
    actor_id VARCHAR(128),
    payload JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    version INTEGER DEFAULT 1,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_events_aggregate_id ON events(aggregate_id);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_actor_id ON events(actor_id);

-- ============================================================================
-- TABLE 4: checkpoints (Session snapshots for state recovery)
-- ============================================================================
CREATE TABLE IF NOT EXISTS checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(128) NOT NULL UNIQUE,
    snapshot_data JSONB NOT NULL,
    event_version BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
    verified BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_session_id ON checkpoints(session_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at ON checkpoints(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_checkpoints_expires_at ON checkpoints(expires_at);

-- ============================================================================
-- TABLE 5: audit_log (Guardian Law compliance - immutable audit trail)
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    operation_type VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64),
    resource_id VARCHAR(256),
    actor_id VARCHAR(128),
    actor_role VARCHAR(32),
    status VARCHAR(20) CHECK (status IN ('success', 'failure', 'unauthorized')),
    details JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET
);

CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor_id ON audit_log(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation_type ON audit_log(operation_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_status ON audit_log(status);

-- ============================================================================
-- TABLE 6: api_keys (Authentication + X-API-Key authorization)
-- ============================================================================
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(256) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    owner_id VARCHAR(128),
    permissions JSONB DEFAULT '["read", "write"]',
    rate_limit INTEGER DEFAULT 1000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    revoked BOOLEAN DEFAULT FALSE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_owner_id ON api_keys(owner_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_created_at ON api_keys(created_at DESC);

-- ============================================================================
-- TABLE 7: sessions (User/Agent session management)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(128),
    agent_id VARCHAR(64),
    session_token VARCHAR(512) NOT NULL UNIQUE,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours'),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_sessions_session_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_agent_id ON sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- ============================================================================
-- TABLE 8: performance_metrics (Real-time system monitoring)
-- ============================================================================
CREATE TABLE IF NOT EXISTS performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    agent_id VARCHAR(64),
    metric_type VARCHAR(64) NOT NULL CHECK (metric_type IN ('latency', 'throughput', 'memory', 'cpu', 'error_rate')),
    metric_value NUMERIC(12, 4) NOT NULL,
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_perf_metrics_agent_id ON performance_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_metric_type ON performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_timestamp ON performance_metrics(timestamp DESC);

-- ============================================================================
-- MATERIALIZED VIEWS (For fast queries across events)
-- ============================================================================

-- View 1: Current task state (CQRS Materialized View)
CREATE MATERIALIZED VIEW IF NOT EXISTS task_current_state AS
SELECT
    t.id,
    t.agent_id,
    t.task_name,
    t.status,
    t.priority,
    t.created_at,
    COUNT(e.id) as event_count,
    MAX(e.timestamp) as last_event_time,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - t.created_at)) as duration_seconds
FROM tasks t
LEFT JOIN events e ON e.aggregate_id = t.id
GROUP BY t.id, t.agent_id, t.task_name, t.status, t.priority, t.created_at;

CREATE UNIQUE INDEX IF NOT EXISTS idx_task_current_state_id ON task_current_state(id);

-- View 2: Agent health dashboard
CREATE MATERIALIZED VIEW IF NOT EXISTS agent_health_summary AS
SELECT
    a.id,
    a.name,
    a.type,
    a.status,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'failed' THEN 1 END) as failed_tasks,
    ROUND(100.0 * COUNT(CASE WHEN t.status = 'completed' THEN 1 END) / NULLIF(COUNT(t.id), 0))::INTEGER as success_rate,
    a.last_heartbeat
FROM agents a
LEFT JOIN tasks t ON t.agent_id = a.id
GROUP BY a.id, a.name, a.type, a.status, a.last_heartbeat;

CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_health_summary_id ON agent_health_summary(id);

-- ============================================================================
-- FUNCTIONS (Utility functions for data management)
-- ============================================================================

-- Function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER tasks_update_timestamp BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER agents_update_timestamp BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ============================================================================
-- PERMISSIONS (Database security)
-- ============================================================================

-- Create limited roles for application
CREATE ROLE IF NOT EXISTS adrion_app LOGIN PASSWORD 'set_this_from_env';
GRANT CONNECT ON DATABASE adrion_prod TO adrion_app;
GRANT USAGE ON SCHEMA public TO adrion_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO adrion_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO adrion_app;

CREATE ROLE IF NOT EXISTS adrion_readonly LOGIN PASSWORD 'set_this_from_env';
GRANT CONNECT ON DATABASE adrion_prod TO adrion_readonly;
GRANT USAGE ON SCHEMA public TO adrion_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO adrion_readonly;
GRANT SELECT ON ALL MATERIALIZED VIEWS IN SCHEMA public TO adrion_readonly;

-- ============================================================================
-- INITIAL DATA (Bootstrap data for system startup)
-- ============================================================================

-- Insert MCP agent registry
INSERT INTO agents (id, name, type, host, port) VALUES
    ('genesis-mcp-1', 'Genesis MCP', 'genesis', 'localhost', 9004),
    ('router-mcp-1', 'Router MCP', 'router', 'localhost', 9001),
    ('guardian-mcp-1', 'Guardian MCP', 'guardian', 'localhost', 9002),
    ('healer-mcp-1', 'Healer MCP', 'healer', 'localhost', 9003),
    ('oracle-mcp-1', 'Oracle MCP', 'oracle', 'localhost', 9005),
    ('vortex-mcp-1', 'Vortex MCP', 'vortex', 'localhost', 9006)
ON CONFLICT (id) DO NOTHING;

-- Create default API key for internal use
INSERT INTO api_keys (key_hash, name, owner_id, permissions) VALUES
    ('adrion_internal_key_hash_v1', 'ADRION Internal', 'system', '["read", "write", "admin"]')
ON CONFLICT (key_hash) DO NOTHING;

-- ============================================================================
-- VERIFICATION QUERIES (Run after migration to validate)
-- ============================================================================
-- SELECT * FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;
-- SELECT count(*) as total_tables FROM pg_tables WHERE schemaname='public';
-- SELECT agent_name, status FROM agent_health_summary;

-- ============================================================================
-- END OF SCHEMA INITIALIZATION
-- Duration: ~5-10 seconds on typical server
-- ============================================================================
