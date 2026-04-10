-- Database Migration 004: Agent Analytics Tables (SQLite + PostgreSQL compatible)
-- File: db/migrations/004_agent_analytics.sql
-- Date: 2026-04-05
-- Status: PHASE C Implementation
-- SQLite: compatible

-- ──────────────────────────────────────────────────────────────────────────
-- ANALYTICS TABLES FOR AGENTS (Phase C)
-- ──────────────────────────────────────────────────────────────────────────

-- agent_activity — History of agent actions
CREATE TABLE IF NOT EXISTS agent_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id VARCHAR(255) NOT NULL REFERENCES agents(id),
    session_id VARCHAR(255),
    activity_type VARCHAR(100),
    description TEXT,
    result VARCHAR(50),  -- 'success', 'failure', 'partial'
    duration_seconds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_activity_agent ON agent_activity(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_activity_session ON agent_activity(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_activity_created ON agent_activity(created_at);

-- agent_performance — Performance metrics per agent
CREATE TABLE IF NOT EXISTS agent_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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

CREATE INDEX IF NOT EXISTS idx_agent_perf_agent ON agent_performance(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_perf_success ON agent_performance(success_rate);

-- agent_feedback — Feedback and ratings from users
CREATE TABLE IF NOT EXISTS agent_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id VARCHAR(255) NOT NULL REFERENCES agents(id),
    session_id VARCHAR(255),
    rating INT,  -- 1-5 stars
    comment TEXT,
    trust_adjustment FLOAT,  -- Change in agent trust score (-0.1 to +0.1)
    feedback_type VARCHAR(50),  -- 'positive', 'negative', 'neutral'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_feedback_agent ON agent_feedback(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_feedback_session ON agent_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_feedback_created ON agent_feedback(created_at);

-- ──────────────────────────────────────────────────────────────────────────
-- SEED DATA FOR ANALYTICS
-- ──────────────────────────────────────────────────────────────────────────

-- Initialize performance records for seed agents
INSERT OR IGNORE INTO agent_performance (agent_id, tasks_completed, tasks_failed, avg_duration_seconds, success_rate, monthly_tasks)
SELECT id, 0, 0, 60, 0.0, 0 FROM agents;

-- Sample activity log entries
INSERT OR IGNORE INTO agent_activity (id, agent_id, session_id, activity_type, description, result, duration_seconds, metadata)
VALUES
(
    1,
    'agent-1',
    'default',
    'knowledge_search',
    'Searched for documentation about Trinity Score',
    'success',
    2,
    '{"query_terms": 2, "results_found": 45}'
),
(
    2,
    'agent-2',
    'default',
    'architecture_design',
    'Designed microservice scaling strategy',
    'success',
    180,
    '{"services": 5, "scaling_factor": 3}'
),
(
    3,
    'agent-4',
    'default',
    'security_scan',
    'Performed security vulnerability scan',
    'success',
    45,
    '{"vulnerabilities_found": 0, "warnings": 2}'
);

-- Sample feedback
INSERT OR IGNORE INTO agent_feedback (id, agent_id, session_id, rating, comment, trust_adjustment, feedback_type)
VALUES
(
    1,
    'agent-1',
    'default',
    5,
    'Excellent documentation retrieval, very accurate',
    0.05,
    'positive'
),
(
    2,
    'agent-2',
    'default',
    4,
    'Good design but took longer than expected',
    0.02,
    'positive'
),
(
    3,
    'agent-4',
    'default',
    5,
    'Thorough security check, caught a subtle issue',
    0.08,
    'positive'
);

-- Update agent performance with activity data
UPDATE agent_performance SET
    tasks_completed = (SELECT COUNT(*) FROM agent_activity WHERE agent_activity.agent_id = agent_performance.agent_id AND result = 'success'),
    tasks_failed = (SELECT COUNT(*) FROM agent_activity WHERE agent_activity.agent_id = agent_performance.agent_id AND result = 'failure'),
    last_activity = (SELECT MAX(created_at) FROM agent_activity WHERE agent_activity.agent_id = agent_performance.agent_id)
WHERE EXISTS (SELECT 1 FROM agent_activity WHERE agent_activity.agent_id = agent_performance.agent_id);

-- ──────────────────────────────────────────────────────────────────────────
-- END OF MIGRATION 004
-- ──────────────────────────────────────────────────────────────────────────
