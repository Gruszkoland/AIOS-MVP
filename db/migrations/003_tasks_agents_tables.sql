-- Database Migration 003: Tasks & Agents Tables
-- File: db/migrations/003_tasks_agents_tables.sql
-- Date: 2026-04-05
-- Status: PHASE B Implementation

-- ──────────────────────────────────────────────────────────────────────────
-- TABLES FOR TASKS & AGENTS (Phase B)
-- ──────────────────────────────────────────────────────────────────────────

-- Drop existing tables (safe for dev/testing)
DROP TABLE IF EXISTS agent_feedback;
DROP TABLE IF EXISTS agent_performance;
DROP TABLE IF EXISTS agent_activity;
DROP TABLE IF EXISTS agent_assignments;
DROP TABLE IF EXISTS agents;
DROP TABLE IF EXISTS tasks;

-- ──────────────────────────────────────────────────────────────────────────
-- TASKS TABLE — Tracks all task executions
-- ──────────────────────────────────────────────────────────────────────────

CREATE TABLE tasks (
    id VARCHAR(255) PRIMARY KEY COMMENT 'Unique task ID (task-xxxxx)',
    session_id VARCHAR(255) NOT NULL DEFAULT 'default' COMMENT 'Session this task belongs to',
    name TEXT NOT NULL COMMENT 'Task name/description',
    agent VARCHAR(255) COMMENT 'Agent assigned to execute',
    status VARCHAR(50) DEFAULT 'pending' COMMENT 'pending/running/completed/failed/cancelled',
    progress INT DEFAULT 0 COMMENT 'Completion percentage (0-100)',
    eta_seconds INT COMMENT 'Estimated time remaining (seconds)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Task creation time',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update time',
    duration_seconds INT COMMENT 'Actual execution time (only when completed)',

    -- Constraints
    CHECK (progress >= 0 AND progress <= 100),
    CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),

    -- Indexes for performance
    INDEX idx_tasks_session (session_id),
    INDEX idx_tasks_status (status),
    INDEX idx_tasks_updated (updated_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ──────────────────────────────────────────────────────────────────────────
-- AGENTS TABLE — Configurable AI agents
-- ──────────────────────────────────────────────────────────────────────────

CREATE TABLE agents (
    id VARCHAR(255) PRIMARY KEY COMMENT 'Unique agent ID (agent-xxxxx)',
    name VARCHAR(255) NOT NULL UNIQUE COMMENT 'Agent display name',
    role VARCHAR(255) COMMENT 'Agent role/specialization',
    personality TEXT COMMENT 'Agent personality description',
    description TEXT COMMENT 'Full agent description',
    trust_score FLOAT DEFAULT 0.8 COMMENT 'Agent reliability score (0.0-1.0)',
    capability_level VARCHAR(50) COMMENT 'basic/intermediate/expert',
    skills JSON COMMENT 'JSON array of agent skills',
    active BOOLEAN DEFAULT TRUE COMMENT 'Is agent currently active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Agent creation time',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last modification time',
    success_rate FLOAT DEFAULT 0 COMMENT 'Percentage of successful tasks',
    tasks_completed INT DEFAULT 0 COMMENT 'Total tasks executed',

    -- Constraints
    CHECK (trust_score >= 0 AND trust_score <= 1),
    CHECK (capability_level IN ('basic', 'intermediate', 'expert')),

    -- Indexes for performance
    INDEX idx_agents_active (active),
    INDEX idx_agents_trust_score (trust_score DESC),
    INDEX idx_agents_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
    '["documentation", "search", "organization", "knowledge-management", "indexing"]',
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
    '["design", "architecture", "planning", "scalability", "devops"]',
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
    '["audit", "risk-assessment", "compliance", "security-review", "vulnerability-detection"]',
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
    '["monitoring", "security", "alerting", "threat-detection", "incident-response"]',
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
    NOW()
),
(
    'task-002',
    'default',
    'Database Migration v3.2',
    'SAP',
    'running',
    40,
    300,
    NOW()
),
(
    'task-003',
    'default',
    'Security Audit Q2',
    'Auditor',
    'pending',
    0,
    NULL,
    NOW()
),
(
    'task-004',
    'default',
    'System Health Check',
    'Sentinel',
    'completed',
    100,
    180,
    DATE_SUB(NOW(), INTERVAL 2 HOUR)
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
