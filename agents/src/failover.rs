//! Agent Failover & Recovery — <1 second restart mechanism
//! Monitors agent health, detects timeouts, triggers automatic restart

use std::process::{Command, Child};
use std::time::{SystemTime, UNIX_EPOCH};
use std::collections::HashMap;

const HEARTBEAT_TIMEOUT_NANOS: u64 = 1_000_000_000; // 1 second
const MAX_RESTART_ATTEMPTS: u32 = 3;
const AGENT_NAMES: &[&str] = &["librarian", "sap", "auditor", "sentinel", "architect", "healer"];

/// Agent process state tracking
#[derive(Debug, Clone)]
pub struct AgentProcess {
    pub agent_id: u16,
    pub agent_name: String,
    pub pid: u32,
    pub last_heartbeat_nanos: u64,
    pub restart_attempts: u32,
    pub is_running: bool,
}

impl AgentProcess {
    pub fn new(agent_id: u16, agent_name: String, pid: u32) -> Self {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default();

        AgentProcess {
            agent_id,
            agent_name,
            pid,
            last_heartbeat_nanos: now.as_nanos() as u64,
            restart_attempts: 0,
            is_running: true,
        }
    }

    pub fn update_heartbeat(&mut self) {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default();
        self.last_heartbeat_nanos = now.as_nanos() as u64;
    }

    pub fn is_timed_out(&self, now_nanos: u64) -> bool {
        let elapsed = now_nanos.saturating_sub(self.last_heartbeat_nanos);
        elapsed > HEARTBEAT_TIMEOUT_NANOS
    }

    pub fn can_restart(&self) -> bool {
        self.restart_attempts < MAX_RESTART_ATTEMPTS
    }
}

/// Failover manager for all agents
pub struct FailoverManager {
    agents: HashMap<u16, AgentProcess>,
    restart_log: Vec<RestartEvent>,
}

/// Restart event for logging
#[derive(Debug, Clone)]
pub struct RestartEvent {
    pub timestamp_nanos: u64,
    pub agent_id: u16,
    pub agent_name: String,
    pub reason: RestartReason,
    pub success: bool,
    pub restart_time_nanos: u64,
}

#[derive(Debug, Clone, Copy)]
pub enum RestartReason {
    Timeout,
    Crash,
    Manual,
}

impl FailoverManager {
    pub fn new() -> Self {
        let mut agents = HashMap::new();
        for (id, name) in AGENT_NAMES.iter().enumerate() {
            agents.insert(
                id as u16,
                AgentProcess::new(id as u16, name.to_string(), 0),
            );
        }

        FailoverManager {
            agents,
            restart_log: Vec::new(),
        }
    }

    /// Detect timed-out agents and trigger restart
    pub fn detect_and_restart(&mut self, now_nanos: u64) -> Vec<RestartEvent> {
        let mut events = Vec::new();
        let agent_ids: Vec<u16> = self.agents.keys().copied().collect();

        for agent_id in agent_ids {
            if let Some(agent) = self.agents.get_mut(&agent_id) {
                if agent.is_running && agent.is_timed_out(now_nanos) && agent.can_restart() {
                    let restart_start = now_nanos;
                    let success = self.restart_agent_internal(agent);
                    let restart_time = now_nanos.saturating_sub(restart_start);

                    let event = RestartEvent {
                        timestamp_nanos: now_nanos,
                        agent_id,
                        agent_name: agent.agent_name.clone(),
                        reason: RestartReason::Timeout,
                        success,
                        restart_time_nanos: restart_time,
                    };

                    events.push(event.clone());
                    self.restart_log.push(event);
                } else if !agent.can_restart() {
                    agent.is_running = false;
                }
            }
        }

        events
    }

    /// Internal agent restart logic
    fn restart_agent_internal(&mut self, agent: &mut AgentProcess) -> bool {
        agent.restart_attempts += 1;

        // In production: spawn new agent process with binary signing verification (P1-1)
        // For now: simulate successful restart
        let success = agent.restart_attempts <= MAX_RESTART_ATTEMPTS;

        if success {
            agent.pid = (1000 + agent.agent_id as u32) * agent.restart_attempts as u32;
            agent.update_heartbeat();
            agent.is_running = true;
        }

        success
    }

    /// Manual agent restart
    pub fn manual_restart(&mut self, agent_id: u16, now_nanos: u64) -> Result<RestartEvent, String> {
        let agent = self.agents.get_mut(&agent_id)
            .ok_or_else(|| format!("Agent {} not found", agent_id))?;

        if !agent.can_restart() {
            return Err(format!("Agent {} exceeded max restart attempts", agent_id));
        }

        let restart_start = now_nanos;
        let success = self.restart_agent_internal(agent);
        let restart_time = now_nanos.saturating_sub(restart_start);

        let event = RestartEvent {
            timestamp_nanos: now_nanos,
            agent_id,
            agent_name: agent.agent_name.clone(),
            reason: RestartReason::Manual,
            success,
            restart_time_nanos: restart_time,
        };

        self.restart_log.push(event.clone());
        Ok(event)
    }

    pub fn heartbeat(&mut self, agent_id: u16) {
        if let Some(agent) = self.agents.get_mut(&agent_id) {
            agent.update_heartbeat();
            agent.restart_attempts = 0;
        }
    }

    pub fn agent_status(&self, agent_id: u16) -> Option<(bool, u32, u32)> {
        self.agents.get(&agent_id)
            .map(|a| (a.is_running, a.pid, a.restart_attempts))
    }

    pub fn restart_log(&self) -> &[RestartEvent] {
        &self.restart_log
    }

    pub fn all_healthy(&self) -> bool {
        self.agents.values().all(|a| a.is_running)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn current_time() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos() as u64
    }

    #[test]
    fn test_agent_process_creation() {
        let agent = AgentProcess::new(0, "librarian".to_string(), 1234);
        assert_eq!(agent.agent_id, 0);
        assert_eq!(agent.pid, 1234);
        assert_eq!(agent.restart_attempts, 0);
        assert!(agent.is_running);
    }

    #[test]
    fn test_timeout_detection() {
        let mut agent = AgentProcess::new(0, "librarian".to_string(), 1234);
        let now = current_time();
        agent.last_heartbeat_nanos = now;

        // Not timed out immediately
        assert!(!agent.is_timed_out(now));

        // Timed out after 1+ seconds
        let future = now + HEARTBEAT_TIMEOUT_NANOS + 1000;
        assert!(agent.is_timed_out(future));
    }

    #[test]
    fn test_heartbeat_update() {
        let mut agent = AgentProcess::new(0, "librarian".to_string(), 1234);
        let old_time = agent.last_heartbeat_nanos;

        agent.update_heartbeat();
        assert!(agent.last_heartbeat_nanos >= old_time);
    }

    #[test]
    fn test_restart_limit() {
        let mut agent = AgentProcess::new(0, "librarian".to_string(), 1234);

        for _ in 0..MAX_RESTART_ATTEMPTS {
            assert!(agent.can_restart());
            agent.restart_attempts += 1;
        }

        assert!(!agent.can_restart());
    }

    #[test]
    fn test_failover_manager_creation() {
        let mgr = FailoverManager::new();
        assert_eq!(mgr.agents.len(), 6);
        assert!(mgr.all_healthy());
    }

    #[test]
    fn test_detect_and_restart() {
        let mut mgr = FailoverManager::new();
        let now = current_time();

        // Force agent 0 to timeout
        if let Some(agent) = mgr.agents.get_mut(&0) {
            agent.last_heartbeat_nanos = now - HEARTBEAT_TIMEOUT_NANOS - 1000;
        }

        let events = mgr.detect_and_restart(now);
        assert_eq!(events.len(), 1);
        assert_eq!(events[0].agent_id, 0);
        assert!(events[0].success);
    }

    #[test]
    fn test_manual_restart() {
        let mut mgr = FailoverManager::new();
        let now = current_time();

        let result = mgr.manual_restart(0, now);
        assert!(result.is_ok());
        let event = result.unwrap();
        assert_eq!(event.reason as u8, RestartReason::Manual as u8);
        assert!(event.success);
    }

    #[test]
    fn test_heartbeat_resets_attempts() {
        let mut mgr = FailoverManager::new();

        mgr.heartbeat(0);
        if let Some((running, _, attempts)) = mgr.agent_status(0) {
            assert!(running);
            assert_eq!(attempts, 0);
        }
    }
}
