-- Database Migration 004: Agent Analytics Tables (PostgreSQL)
-- File: db/migrations/004_agent_analytics.sql
-- Date: 2026-04-05
-- Status: PHASE C Implementation
-- Platform: PostgreSQL 12+

-- ──────────────────────────────────────────────────────────────────────────
-- ANALYTICS TABLES FOR AGENTS (Phase C)
-- ──────────────────────────────────────────────────────────────────────────

-- agent_activity — History of agent actions
CREATE TABLE agent_activity (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL REFERENCES agents(id),
    session_id VARCHAR(255),
    activity_type VARCHAR(100),
    description TEXT,
    result VARCHAR(50),  -- 'success', 'failure', 'partial'
    duration_seconds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_agent_activity_agent ON agent_activity(agent_id);
CREATE INDEX idx_agent_activity_session ON agent_activity(session_id);
CREATE INDEX idx_agent_activity_created ON agent_activity(created_at DESC);

-- agent_performance — Performance metrics per agent
CREATE TABLE agent_performance (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL UNIQUE REFERENCES agents(id),
    tasks_completed INT DEFAULT 0,
    tasks_failed INT DEFAULT 0,
    avg_duration_seconds FLOAT,
    success_rate FLOAT,
    last_activity TIMESTAMP,
    monthly_tasks INT DEFAULT 0,
    arousal_level FLOAT DEFAULT 0.5,  -- EBDI metric
    dominance_level FLOAT DEFAULT 0.5,  -- EBDI metric
    pleasure_level FLOAT DEFAULT 0.5,  -- EBDI metric
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_perf_agent ON agent_performance(agent_id);
CREATE INDEX idx_agent_perf_success ON agent_performance(success_rate DESC);

-- agent_feedback — Feedback and ratings from users
CREATE TABLE agent_feedback (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL REFERENCES agents(id),
    session_id VARCHAR(255),
    rating INT,  -- 1-5 stars
    comment TEXT,
    trust_adjustment FLOAT,  -- Change in agent trust score (-0.1 to +0.1)
    feedback_type VARCHAR(50),  -- 'positive', 'negative', 'neutral'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_feedback_agent ON agent_feedback(agent_id);
CREATE INDEX idx_agent_feedback_session ON agent_feedback(session_id);
CREATE INDEX idx_agent_feedback_created ON agent_feedback(created_at DESC);

-- ──────────────────────────────────────────────────────────────────────────
-- SEED DATA FOR ANALYTICS
-- ──────────────────────────────────────────────────────────────────────────

-- Initialize performance records for seed agents
INSERT INTO agent_performance (agent_id, tasks_completed, tasks_failed, avg_duration_seconds, success_rate, monthly_tasks)
SELECT id, 0, 0, 60, 0.0, 0 FROM agents;

-- Sample activity log entries
INSERT INTO agent_activity (agent_id, session_id, activity_type, description, result, duration_seconds, metadata)
VALUES
(
    'agent-1',
    'default',
    'knowledge_search',
    'Searched for documentation about Trinity Score',
    'success',
    2,
    '{"query_terms": 2, "results_found": 45}'::jsonb
),
(
    'agent-2',
    'default',
    'architecture_design',
    'Designed microservice scaling strategy',
    'success',
    180,
    '{"services": 5, "scaling_factor": 3}'::jsonb
),
(
    'agent-4',
    'default',
    'security_scan',
    'Performed security vulnerability scan',
    'success',
    45,
    '{"vulnerabilities_found": 0, "warnings": 2}'::jsonb
);

-- Sample feedback
INSERT INTO agent_feedback (agent_id, session_id, rating, comment, trust_adjustment, feedback_type)
VALUES
(
    'agent-1',
    'default',
    5,
    'Excellent documentation retrieval, very accurate',
    0.05,
    'positive'
),
(
    'agent-2',
    'default',
    4,
    'Good design but took longer than expected',
    0.02,
    'positive'
),
(
    'agent-4',
    'default',
    5,
    'Thorough security check, caught a subtle issue',
    0.08,
    'positive'
);

-- Update agent performance with activity data
UPDATE agent_performance ap SET
    tasks_completed = (SELECT COUNT(*) FROM agent_activity WHERE agent_id = ap.agent_id AND result = 'success'),
    tasks_failed = (SELECT COUNT(*) FROM agent_activity WHERE agent_id = ap.agent_id AND result = 'failure'),
    last_activity = (SELECT MAX(created_at) FROM agent_activity WHERE agent_id = ap.agent_id)
WHERE EXISTS (SELECT 1 FROM agent_activity WHERE agent_id = ap.agent_id);

-- ──────────────────────────────────────────────────────────────────────────
-- END OF MIGRATION 004
-- ──────────────────────────────────────────────────────────────────────────
