-- Database Migration 003: Tasks & Agents Tables (PostgreSQL)
-- File: db/migrations/003_tasks_agents_tables.sql
-- Date: 2026-04-05
-- Status: PHASE B Implementation
-- Platform: PostgreSQL 12+

-- ──────────────────────────────────────────────────────────────────────────
-- TABLES FOR TASKS & AGENTS (Phase B)
-- ──────────────────────────────────────────────────────────────────────────

-- Drop existing tables (safe for dev/testing)
DROP TABLE IF EXISTS agent_feedback CASCADE;
DROP TABLE IF EXISTS agent_performance CASCADE;
DROP TABLE IF EXISTS agent_activity CASCADE;
DROP TABLE IF EXISTS agent_assignments CASCADE;
DROP TABLE IF EXISTS agents CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;

-- ──────────────────────────────────────────────────────────────────────────
-- TASKS TABLE — Tracks all task executions
-- ──────────────────────────────────────────────────────────────────────────

CREATE TABLE tasks (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL DEFAULT 'default',
    name TEXT NOT NULL,
    agent VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    progress INT DEFAULT 0,
    eta_seconds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INT,

    CONSTRAINT check_progress CHECK (progress >= 0 AND progress <= 100),
    CONSTRAINT check_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Create indexes for tasks table
CREATE INDEX idx_tasks_session ON tasks(session_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_updated ON tasks(updated_at DESC);

-- ──────────────────────────────────────────────────────────────────────────
-- AGENTS TABLE — Configurable AI agents
-- ──────────────────────────────────────────────────────────────────────────

CREATE TABLE agents (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(255),
    personality TEXT,
    description TEXT,
    trust_score FLOAT DEFAULT 0.8,
    capability_level VARCHAR(50),
    skills JSONB,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success_rate FLOAT DEFAULT 0,
    tasks_completed INT DEFAULT 0,

    CONSTRAINT check_trust_score CHECK (trust_score >= 0 AND trust_score <= 1),
    CONSTRAINT check_capability CHECK (capability_level IN ('basic', 'intermediate', 'expert'))
);

-- Create indexes for agents table
CREATE INDEX idx_agents_active ON agents(active);
CREATE INDEX idx_agents_trust_score ON agents(trust_score DESC);
CREATE INDEX idx_agents_name ON agents(name);

-- ──────────────────────────────────────────────────────────────────────────
-- DEFAULT AGENTS — Pre-loaded for immediate use
-- ──────────────────────────────────────────────────────────────────────────

INSERT INTO agents (id, name, role, personality, description, trust_score, capability_level, skills, active, success_rate, tasks_completed)
VALUES
(
    'agent-1',
    'Librarian',
    'Knowledge Management',
    'Organized, precise, detail-oriented. Takes pride in perfect documentation and accessibility.',
    'Manages knowledge base, documentation systems, and search capabilities. Ensures all information is organized, searchable, and up-to-date. Excellent at pattern recognition and historical analysis.',
    0.95,
    'expert',
    '["documentation", "search", "organization", "knowledge-management", "indexing"]'::jsonb,
    TRUE,
    0.98,
    342
),
(
    'agent-2',
    'Architect',
    'System Design',
    'Strategic, visionary, forward-thinking. Likes designing elegant solutions for complex problems.',
    'Designs system architecture, scalability patterns, and infrastructure. Plans long-term technical strategies. Expert in distributed systems, microservices, and cloud architecture.',
    0.88,
    'expert',
    '["design", "architecture", "planning", "scalability", "devops"]'::jsonb,
    TRUE,
    0.92,
    187
),
(
    'agent-3',
    'Auditor',
    'Risk Management',
    'Thorough, analytical, cautious. Meticulously checks every detail and flags potential risks.',
    'Conducts comprehensive audits, identifies security and compliance risks, and ensures adherence to standards. Thorough in analysis and conservative in recommendations.',
    0.87,
    'expert',
    '["audit", "risk-assessment", "compliance", "security-review", "vulnerability-detection"]'::jsonb,
    TRUE,
    0.91,
    156
),
(
    'agent-4',
    'Sentinel',
    'Security & Monitoring',
    'Vigilant, protective, always alert. Continuously scans for threats and anomalies.',
    'Monitors system health, detects security threats, sends alerts, and ensures 24/7 uptime. Expert in intrusion detection, threat analysis, and proactive defense.',
    0.92,
    'expert',
    '["monitoring", "security", "alerting", "threat-detection", "incident-response"]'::jsonb,
    TRUE,
    0.95,
    421
);

-- ──────────────────────────────────────────────────────────────────────────
-- DEFAULT TASKS — For testing Phase B
-- ──────────────────────────────────────────────────────────────────────────

INSERT INTO tasks (id, session_id, name, agent, status, progress, eta_seconds, created_at)
VALUES
(
    'task-001',
    'default',
    'Deploy Backend to Production',
    'Architect',
    'running',
    65,
    120,
    CURRENT_TIMESTAMP
),
(
    'task-002',
    'default',
    'Database Migration v3.2',
    'SAP',
    'running',
    40,
    300,
    CURRENT_TIMESTAMP
),
(
    'task-003',
    'default',
    'Security Audit Q2',
    'Auditor',
    'pending',
    0,
    NULL,
    CURRENT_TIMESTAMP
),
(
    'task-004',
    'default',
    'System Health Check',
    'Sentinel',
    'completed',
    100,
    180,
    CURRENT_TIMESTAMP - INTERVAL '2 hours'
);

-- ──────────────────────────────────────────────────────────────────────────
-- VERIFICATION QUERIES
-- ──────────────────────────────────────────────────────────────────────────

-- Run these to verify migration success:

-- 1. Check tables exist
-- SHOW TABLES;

-- 2. Check agents loaded
-- SELECT id, name, role, trust_score FROM agents ORDER BY trust_score DESC;

-- 3. Check tasks loaded
-- SELECT id, name, agent, status, progress FROM tasks;

-- 4. Count by status
-- SELECT status, COUNT(*) as count FROM tasks GROUP BY status;

-- ──────────────────────────────────────────────────────────────────────────
-- END OF MIGRATION 003
-- ──────────────────────────────────────────────────────────────────────────
